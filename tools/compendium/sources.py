"""Local book library: text cache, tables of contents, search, and copy-guard.

The books themselves stay in the vault's __RESOURCES__ folder (git-ignored).
Extracted text lives in .cache/books (git-ignored); TOCs live in
tools/data/books (committed: they are bibliographic facts, not content).

Notes must PARAPHRASE and CITE. The copy-guard flags any 12-word run in a note
that also appears verbatim in a book.
"""
from __future__ import annotations

import hashlib
import html
import json
import pickle
import re
import time
import zipfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath

from . import paths
from .util import load_yaml

SHINGLE = 12
_WORD = re.compile(r"[a-z0-9]+")


# ----------------------------------------------------------------------------- catalogue
def books() -> list[dict]:
    out = []
    for b in load_yaml(paths.DATA / "books.yaml"):
        b = dict(b)
        hits = sorted(paths.RESOURCES.glob(b["glob"]))
        b["file"] = hits[0] if hits else None
        out.append(b)
    return out


def book(key: str) -> dict:
    for b in books():
        if b["key"] == key:
            return b
    raise SystemExit(f"unknown book '{key}'. Known: {', '.join(x['key'] for x in books())}")


def _text_path(key: str) -> Path:
    return paths.BOOK_TEXT / f"{key}.json"


def _toc_path(key: str) -> Path:
    return paths.BOOK_TOC / f"{key}.toc.json"


# ----------------------------------------------------------------------------- extraction
def _clean(s: str) -> str:
    s = s.replace("­", "").replace("ﬁ", "fi").replace("ﬂ", "fl")
    s = re.sub(r"-\n(?=[a-z])", "", s)       # de-hyphenate line breaks
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def _extract_pdf(b: dict, start: int = 0, budget_s: float = 150.0) -> tuple[list[dict], list[dict], bool]:
    import pypdf
    reader = pypdf.PdfReader(str(b["file"]))
    try:
        labels = list(reader.page_labels)
    except Exception:
        labels = [str(i + 1) for i in range(len(reader.pages))]
    cached = json.loads(_text_path(b["key"]).read_text(encoding="utf-8")) if start and _text_path(b["key"]).exists() else {"pages": []}
    pages = cached["pages"][:start]
    t0 = time.time()
    complete = True
    for i in range(start, len(reader.pages)):
        try:
            txt = reader.pages[i].extract_text() or ""
        except Exception:
            txt = ""
        pages.append({"i": i, "label": labels[i] if i < len(labels) else str(i + 1), "text": _clean(txt)})
        if time.time() - t0 > budget_s:
            complete = i == len(reader.pages) - 1
            break
    toc = []

    def walk(items, level):
        for it in items:
            if isinstance(it, list):
                walk(it, level + 1)
                continue
            try:
                pi = reader.get_destination_page_number(it)
            except Exception:
                continue
            toc.append({"level": level, "title": str(it.title).strip(), "i": pi,
                        "label": labels[pi] if 0 <= pi < len(labels) else str(pi + 1)})

    walk(reader.outline, 0)
    return pages, toc, complete


class _Text(HTMLParser):
    BLOCK = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "tr", "section"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self._skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)

    def text(self):
        return re.sub(r"\n\s*\n+", "\n\n", "".join(self.parts))


def _extract_epub(b: dict) -> tuple[list[dict], list[dict], bool]:
    z = zipfile.ZipFile(str(b["file"]))
    names = z.namelist()
    opf_name = next(n for n in names if n.endswith(".opf"))
    opf = z.read(opf_name).decode("utf-8", "replace")
    base = PurePosixPath(opf_name).parent
    manifest = {m.group(1): m.group(2) for m in re.finditer(r'<item\b[^>]*\bid="([^"]+)"[^>]*\bhref="([^"]+)"', opf)}
    manifest.update({m.group(2): m.group(1) for m in re.finditer(r'<item\b[^>]*\bhref="([^"]+)"[^>]*\bid="([^"]+)"', opf)})
    spine = re.findall(r'<itemref\b[^>]*\bidref="([^"]+)"', opf)
    pages, href_to_i = [], {}
    for idref in spine:
        href = manifest.get(idref)
        if not href:
            continue
        full = str(base / href) if str(base) != "." else href
        try:
            raw = z.read(full).decode("utf-8", "replace")
        except KeyError:
            continue
        p = _Text()
        p.feed(raw)
        txt = _clean(html.unescape(p.text()))
        if not txt:
            continue
        i = len(pages)
        href_to_i[PurePosixPath(href).name] = i
        pages.append({"i": i, "label": PurePosixPath(href).stem, "text": txt})
    toc = []
    ncx = next((n for n in names if n.endswith(".ncx")), None)
    if ncx:
        doc = z.read(ncx).decode("utf-8", "replace")
        depth = 0
        for m in re.finditer(r"<navPoint\b|</navPoint>|<text>(.*?)</text>|<content\b[^>]*src=\"([^\"]+)\"", doc, re.S):
            tok = m.group(0)
            if tok.startswith("<navPoint"):
                depth += 1
            elif tok == "</navPoint>":
                depth -= 1
            elif m.group(1) is not None:
                toc.append({"level": max(0, depth - 1), "title": html.unescape(re.sub(r"\s+", " ", m.group(1))).strip(), "i": None, "label": ""})
            elif m.group(2) and toc and toc[-1]["i"] is None:
                name = PurePosixPath(m.group(2).split("#")[0]).name
                i = href_to_i.get(name)
                toc[-1]["i"] = i
                toc[-1]["label"] = pages[i]["label"] if i is not None else ""
        toc = [t for t in toc if t["i"] is not None]
    return pages, toc, True


def build(key: str | None = None, force: bool = False, budget_s: float = 150.0) -> None:
    """Extract text + TOC for one or all books. Resumable within the time budget."""
    paths.BOOK_TEXT.mkdir(parents=True, exist_ok=True)
    paths.BOOK_TOC.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + budget_s          # one budget for the whole call (device shells time out)
    for b in books():
        remaining = deadline - time.time()
        if remaining < 10:
            print("time budget used — run `src build` again to continue")
            break
        if key and b["key"] != key:
            continue
        if not b["file"]:
            print(f"[{b['key']}] MISSING file for glob {b['glob']}")
            continue
        tp = _text_path(b["key"])
        state = json.loads(tp.read_text(encoding="utf-8")) if tp.exists() else None
        if state and state.get("complete") and not force:
            print(f"[{b['key']}] cached ({len(state['pages'])} pages)")
            continue
        t0 = time.time()
        if b["kind"] == "pdf":
            start = len(state["pages"]) if (state and not force) else 0
            pages, toc, complete = _extract_pdf(b, start=start, budget_s=remaining)
        else:
            pages, toc, complete = _extract_epub(b)
        tp.write_text(json.dumps({"key": b["key"], "complete": complete, "pages": pages}, ensure_ascii=False), encoding="utf-8")
        _toc_path(b["key"]).write_text(json.dumps(toc, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"[{b['key']}] {'complete' if complete else 'PARTIAL (run again)'}: {len(pages)} pages, {len(toc)} toc entries, {time.time() - t0:.0f}s")
    # copy-guard index is invalidated by mtime (see _shingle_index); nothing to delete


def ready() -> dict[str, bool]:
    out = {}
    for b in books():
        tp = _text_path(b["key"])
        ok = False
        if tp.exists():
            try:
                ok = bool(json.loads(tp.read_text(encoding="utf-8")).get("complete"))
            except Exception:
                ok = False
        out[b["key"]] = ok
    return out


# ----------------------------------------------------------------------------- lookup
def _pages(key: str) -> list[dict]:
    tp = _text_path(key)
    if not tp.exists():
        return []
    return json.loads(tp.read_text(encoding="utf-8"))["pages"]


def toc(key: str) -> list[dict]:
    tp = _toc_path(key)
    return json.loads(tp.read_text(encoding="utf-8")) if tp.exists() else []


def section_of(key: str, page_i: int, entries: list[dict] | None = None) -> str:
    entries = entries if entries is not None else toc(key)
    best = None
    for e in entries:
        if e["i"] is not None and e["i"] <= page_i and (best is None or e["i"] >= best["i"]):
            best = e
    return best["title"] if best else ""


def find(query: str, key: str | None = None, limit: int = 12) -> list[dict]:
    terms = [t for t in query.lower().split() if t]
    phrase = query.lower().strip()
    hits = []
    for b in books():
        if key and b["key"] != key:
            continue
        entries = toc(b["key"])
        for pg in _pages(b["key"]):
            low = pg["text"].lower()
            if not all(t in low for t in terms):
                continue
            score = 10 * low.count(phrase) + sum(min(low.count(t), 5) for t in terms)
            pos = low.find(phrase) if phrase in low else low.find(terms[0])
            snip = pg["text"][max(0, pos - 140): pos + 220].replace("\n", " ")
            hits.append({"book": b["key"], "cite": b["cite"], "i": pg["i"], "page": pg["label"], "score": score,
                         "section": section_of(b["key"], pg["i"], entries), "snippet": snip})
    hits.sort(key=lambda h: -h["score"])
    return hits[:limit]


def toc_grep(key: str | None, pattern: str | None) -> list[dict]:
    rx = re.compile(pattern, re.I) if pattern else None
    out = []
    for b in books():
        if key and b["key"] != key:
            continue
        for e in toc(b["key"]):
            if rx is None or rx.search(e["title"]):
                out.append({**e, "book": b["key"], "cite": b["cite"]})
    return out


def read(key: str, spec: str, by_label: bool = True, max_chars: int = 12000) -> str:
    """Pages as text. spec: '531', '531-534', or 'i:540-542' for raw indices."""
    pages = _pages(key)
    raw = spec.startswith("i:")
    spec = spec[2:] if raw else spec
    a, _, b = spec.partition("-")
    if raw or not by_label:
        lo, hi = int(a), int(b or a)
        sel = [p for p in pages if lo <= p["i"] <= hi]
    else:
        labels = [p["label"] for p in pages]
        try:
            lo = labels.index(a)
            hi = labels.index(b) if b else lo
        except ValueError:
            return f"page label not found: {spec} (try i:<index>)"
        sel = pages[lo: hi + 1]
    out = []
    for p in sel:
        out.append(f"===== {key} p.{p['label']} (i:{p['i']}) · {section_of(key, p['i'])}\n{p['text']}")
    text = "\n\n".join(out)
    return text if len(text) <= max_chars else text[:max_chars] + f"\n… [truncated at {max_chars} chars]"


def suggest(words: list[str], limit: int = 15) -> list[dict]:
    """TOC entries across all books that best match a topic's title/keywords."""
    terms = {w.lower() for w in words if len(w) > 2}
    scored = []
    for b in books():
        for e in toc(b["key"]):
            t = e["title"].lower()
            s = sum(1 for w in terms if w in t)
            if s:
                scored.append((s, b["cite"], e))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [{"cite": c, **e} for s, c, e in scored[:limit]]


# ----------------------------------------------------------------------------- copy-guard
def _norm_words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _h(ws) -> int:
    return int.from_bytes(hashlib.blake2b(" ".join(ws).encode(), digest_size=8).digest(), "little")


def _shingle_index() -> set[int]:
    pk = paths.CACHE / "shingles.pkl"
    texts = [_text_path(b["key"]) for b in books() if _text_path(b["key"]).exists()]
    stale = pk.exists() and any(t.stat().st_mtime > pk.stat().st_mtime for t in texts)
    if pk.exists() and not stale and pk.stat().st_size > 0:
        with open(pk, "rb") as fh:
            return pickle.load(fh)
    idx: set[int] = set()
    for b in books():
        for pg in _pages(b["key"]):
            w = _norm_words(pg["text"])
            for i in range(0, max(0, len(w) - SHINGLE + 1)):
                idx.add(_h(w[i: i + SHINGLE]))
    if idx:
        paths.CACHE.mkdir(parents=True, exist_ok=True)
        tmp = pk.with_suffix(".tmp")
        with open(tmp, "wb") as fh:
            pickle.dump(idx, fh, protocol=pickle.HIGHEST_PROTOCOL)
        tmp.replace(pk)
    return idx


_IDX: set[int] | None = None


def copied_runs(text: str) -> list[str]:
    """Verbatim 12-word runs shared with any book (merged into maximal spans)."""
    global _IDX
    if _IDX is None:
        _IDX = _shingle_index()
    if not _IDX:
        return []
    w = _norm_words(text)
    hit = [i for i in range(0, max(0, len(w) - SHINGLE + 1)) if _h(w[i: i + SHINGLE]) in _IDX]
    spans, start, prev = [], None, None
    for i in hit:
        if start is None:
            start = prev = i
        elif i == prev + 1:
            prev = i
        else:
            spans.append((start, prev))
            start = prev = i
    if start is not None:
        spans.append((start, prev))
    return [" ".join(w[a: b + SHINGLE]) for a, b in spans]
