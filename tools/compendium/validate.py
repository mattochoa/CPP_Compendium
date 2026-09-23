"""Automated lint of notes against the Framework (archetypes.yaml + schema).

Levels
  error  must be fixed before a note may be `draft` or better
  warn   should be fixed; the Editor weighs these in the rubric

The lint score (0-100) is a mechanical proxy only. Quality is judged by the
Editor's rubric (see Audit Protocol.md).
"""
from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass

from . import paths, registry
from .notes import Note, file_index

REQUIRED_FM = ["id", "title", "type", "domain", "tier", "status", "created", "updated", "tags"]
URL_RE = re.compile(r"https?://[^\s)>\]]+")
BOOK_CITE_RE = re.compile(r"\b(Primer|Tour|PPP|Pikus)\b\s*(§|ch\.?|chapter|p\.)", re.I)
ESSENCE_WINDOW = 15      # essence callout must appear within the first N body lines
SYSTEM_TYPES = {"system", "brief", "ledger", "dashboard", "home"}


@dataclass
class Issue:
    level: str
    code: str
    msg: str

    def __str__(self):
        return f"{self.level.upper():5} {self.code:18} {self.msg}"


def check(note: Note, topics_by_id: dict | None = None, file_idx: dict | None = None,
          titles: set | None = None, copy_guard: bool = True) -> list[Issue]:
    topics_by_id = topics_by_id if topics_by_id is not None else registry.by_id(registry.load_topics())
    file_idx = file_idx if file_idx is not None else file_index()
    titles = titles if titles is not None else {t.title.lower() for t in topics_by_id.values()}
    alias_titles = set()
    for t in topics_by_id.values():
        alias_titles.update(a.lower() for a in t.aliases)
    issues: list[Issue] = []
    E = lambda c, m: issues.append(Issue("error", c, m))   # noqa: E731
    W = lambda c, m: issues.append(Issue("warn", c, m))    # noqa: E731

    fm = note.fm
    content_dirs = (paths.MAPS, paths.NOTES, paths.SOURCES, paths.PRACTICE)
    in_content = any(note.path.resolve().is_relative_to(d.resolve()) for d in content_dirs)
    if not fm.get("type") and not in_content:
        return issues   # the owner's own free-form notes (e.g. RESOURCES.md) are not policed
    if note.fm_error:
        E("frontmatter", f"YAML error: {note.fm_error}")
        return issues
    ntype = fm.get("type")
    if ntype in SYSTEM_TYPES:
        return issues   # system pages are not content notes
    for k in REQUIRED_FM:
        if k not in fm or fm.get(k) in (None, ""):
            E("frontmatter", f"missing `{k}`")
    if ntype not in registry.TYPES:
        E("frontmatter", f"type `{ntype}` not one of {registry.TYPES}")
        return issues
    status = fm.get("status")
    if status not in registry.STATUSES:
        E("frontmatter", f"status `{status}` not one of {registry.STATUSES}")
    topic = topics_by_id.get(fm.get("id"))
    if topic is None:
        E("registry", f"id `{fm.get('id')}` not in topics.yaml (add it with `cc.py registry add`)")
    else:
        if topic.title != note.stem:
            E("registry", f"file name `{note.stem}` != registry title `{topic.title}`")
        if topic.type != ntype:
            E("registry", f"type `{ntype}` != registry type `{topic.type}`")
        if topic.domain != fm.get("domain"):
            E("registry", f"domain `{fm.get('domain')}` != registry domain `{topic.domain}`")
        if note.path.parent.resolve() != topic.folder.resolve():
            W("location", f"expected in {paths.rel(topic.folder)}")
    for key in ("created", "updated"):
        v = fm.get(key)
        if v and not isinstance(v, _dt.date):
            try:
                _dt.date.fromisoformat(str(v))
            except ValueError:
                E("frontmatter", f"`{key}` must be YYYY-MM-DD")
    tags = fm.get("tags") or []
    if isinstance(tags, list) and not any(str(t).startswith("type/") for t in tags):
        W("frontmatter", "tags should include type/<archetype> and domain/<code>")

    if status == "stub":
        return issues   # scaffolded placeholder: structure checks start at draft

    spec = registry.archetypes()[ntype]
    heads = [h.lower() for h in note.headings]
    for s in spec["sections"]:
        if s.lower() not in heads:
            E("section", f"missing `## {s}`")
    body_lines = [ln for ln in note.body.splitlines() if ln.strip()]
    if not any(re.match(r">\s*\[!essence\]", ln) for ln in body_lines[:ESSENCE_WINDOW]):
        E("essence", "no `> [!essence]` callout at the top of the note")
    if ntype not in ("guide", "path", "evolution") and not any(c == "principle" for c, _ in note.callouts):
        W("first-principles", "no `> [!principle]` callout (derive the idea from constraints)")
    if note.word_count < spec["min_words"]:
        E("depth", f"{note.word_count} words < {spec['min_words']} minimum for {ntype}")
    if note.diagram_count < spec["diagrams"]:
        E("visual", f"{note.diagram_count} diagrams < {spec['diagrams']} required (mermaid or box-drawing text)")
    if note.table_count < spec["tables"]:
        E("visual", f"{note.table_count} tables < {spec['tables']} required")
    ncpp = len(note.cpp_blocks())
    if ncpp < spec["code"]:
        E("code", f"{ncpp} C++ blocks < {spec['code']} required")
    nquiz = sum(1 for c, _ in note.callouts if c == "quiz")
    if nquiz < spec["quiz"]:
        E("quiz", f"{nquiz} `> [!quiz]-` items < {spec['quiz']} required")
    for c, fold in note.callouts:
        if c == "quiz" and fold != "-":
            W("quiz", "quiz callouts should be folded: `> [!quiz]-`")
            break

    # Links resolve to a file, or to a planned registry title (the "frontier").
    for target in set(note.links):
        low = target.lower()
        if low in file_idx or low.removesuffix(".md") in file_idx:
            continue
        if low in titles:
            continue
        if low in alias_titles:
            W("link", f"[[{target}]] is an alias; link the canonical title instead")
            continue
        E("link", f"[[{target}]] resolves to nothing (not a note, not a planned topic)")
    if len(set(note.links)) < 4 and ntype not in ("guide", "path"):
        W("integration", f"only {len(set(note.links))} distinct links; weave the note into the graph")

    src = note.section("Sources")
    if "Sources" in note.headings:
        if not BOOK_CITE_RE.search(src):
            W("sources", "no book citation with location (e.g. `Primer §13.6.2 (p. 532)`)")
        if not URL_RE.search(src):
            W("sources", "no web reference (cppreference / eel.is draft / Core Guidelines)")
        if len([ln for ln in src.splitlines() if ln.strip().startswith(("-", "*", "1", "|"))]) < 3 and ntype not in ("path",):
            W("sources", "fewer than 3 sources")

    for b in note.cpp_blocks():
        n = b.code.count("\n")
        if n > 60:
            W("code", f"code block at line {b.line} is {n} lines; split or trim (≤ 40 preferred)")

    if copy_guard:
        try:
            from .sources import copied_runs
            runs = copied_runs(note.prose)
            for r in runs[:5]:
                E("copyright", f"verbatim book text: \"{r[:90]}…\" — paraphrase and cite instead")
            code = "\n".join(b.code for b in note.code_blocks if b.lang in ("cpp", "c++"))
            for r in copied_runs(code)[:3]:
                W("copyright", f"code closely matches a book listing: \"{r[:70]}…\" — write your own example")
        except Exception as exc:  # book cache missing etc.
            W("copyright", f"copy-guard unavailable: {exc}")
    return issues


def score(issues: list[Issue]) -> int:
    e = sum(1 for i in issues if i.level == "error")
    w = sum(1 for i in issues if i.level == "warn")
    return max(0, 100 - 12 * e - 3 * w)


def check_many(notes: list[Note], copy_guard: bool = True) -> dict:
    topics = registry.load_topics(notes)
    tb = registry.by_id(topics)
    fi = file_index()
    titles = {t.title.lower() for t in topics}
    return {n.path: check(n, tb, fi, titles, copy_guard) for n in notes}
