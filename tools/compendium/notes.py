"""Reading and writing Compendium notes.

A note is Markdown with YAML frontmatter. This module knows nothing about
archetypes or the registry; it only exposes the note's structure.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import yaml

from . import paths
from .util import words, write_text

FM_RE = re.compile(r"\A---\n(.*?)\n---[ \t]*\n?", re.S)
# [[Target]], [[Target|alias]], [[Target#Heading]], ![[Embed]]
LINK_RE = re.compile(r"!?\[\[([^\]\|#\^]*)(?:[#\^][^\]\|]*)?(?:\|[^\]]*)?\]\]")
H2_RE = re.compile(r"^##[ \t]+(.+?)[ \t]*#*[ \t]*$", re.M)
FENCE_RE = re.compile(r"^(`{3,}|~{3,})([^\n]*)\n(.*?)^\1[ \t]*$", re.S | re.M)
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$", re.M)
CALLOUT_RE = re.compile(r"^>\s*\[!([A-Za-z0-9_-]+)\]([+-]?)", re.M)
AUTO_RE = re.compile(r"(<!-- cc:auto:([^\s>]+) -->\n)(.*?)(<!-- cc:end -->)", re.S)
BOX_CHARS = set("┌┐└┘├┤┬┴┼─│╭╮╰╯═║▶◀▲▼")


@dataclass
class CodeBlock:
    lang: str
    info: str
    code: str
    line: int  # 1-based line of the opening fence


class Note:
    def __init__(self, path: Path, text: str | None = None):
        self.path = Path(path)
        raw = text if text is not None else self.path.read_text(encoding="utf-8")
        self.text = raw.replace("\r\n", "\n")
        m = FM_RE.match(self.text)
        if m:
            try:
                self.fm = yaml.safe_load(m.group(1)) or {}
                self.fm_error = None
            except yaml.YAMLError as exc:  # keep going, validator reports it
                self.fm, self.fm_error = {}, str(exc)
            self.body = self.text[m.end():]
            self._body_offset = self.text[: m.end()].count("\n")
        else:
            self.fm, self.fm_error, self.body, self._body_offset = {}, None, self.text, 0
        if not isinstance(self.fm, dict):
            self.fm, self.fm_error = {}, "frontmatter is not a mapping"

    # ---------------------------------------------------------------- identity
    @property
    def stem(self) -> str:
        return self.path.stem

    @property
    def id(self) -> str | None:
        return self.fm.get("id")

    @property
    def title(self) -> str:
        return str(self.fm.get("title") or self.stem)

    @property
    def status(self) -> str:
        return str(self.fm.get("status") or "")

    # ---------------------------------------------------------------- structure
    @cached_property
    def code_blocks(self) -> list[CodeBlock]:
        out = []
        for m in FENCE_RE.finditer(self.body):
            info = m.group(2).strip()
            lang = info.split()[0].lower() if info else ""
            line = self._body_offset + self.body[: m.start()].count("\n") + 1
            out.append(CodeBlock(lang, info, m.group(3), line))
        return out

    @cached_property
    def prose(self) -> str:
        """Body with fenced code removed (used for word counts and link scans)."""
        return FENCE_RE.sub("", self.body)

    @cached_property
    def headings(self) -> list[str]:
        return [h.strip() for h in H2_RE.findall(self.prose)]

    def section(self, heading: str) -> str:
        """Text of an H2 section (until the next H2), code included."""
        pat = re.compile(r"^##[ \t]+" + re.escape(heading) + r"[ \t]*$(.*?)(?=^##[ \t]|\Z)", re.S | re.M)
        m = pat.search(self.body)
        return m.group(1) if m else ""

    @cached_property
    def links(self) -> list[str]:
        """Link targets (file names without extension / folders), in order."""
        found = []
        for m in LINK_RE.finditer(self.prose):
            target = m.group(1).strip()
            if target:
                found.append(target.split("/")[-1])
        for key in ("prereqs", "related"):
            val = self.fm.get(key) or []
            if isinstance(val, str):
                val = [val]
            for v in val:
                for m in LINK_RE.finditer(str(v)):
                    if m.group(1).strip():
                        found.append(m.group(1).strip().split("/")[-1])
        return found

    @cached_property
    def callouts(self) -> list[tuple[str, str]]:
        return [(m.group(1).lower(), m.group(2)) for m in CALLOUT_RE.finditer(self.prose)]

    @cached_property
    def word_count(self) -> int:
        text = LINK_RE.sub(lambda m: m.group(1), self.prose)
        text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        return len(words(text))

    @cached_property
    def table_count(self) -> int:
        return len(TABLE_SEP_RE.findall(self.prose))

    @cached_property
    def diagram_count(self) -> int:
        n = 0
        for b in self.code_blocks:
            if b.lang == "mermaid":
                n += 1
            elif b.lang in ("text", "txt", "") and sum(ch in BOX_CHARS for ch in b.code) >= 8:
                n += 1
        return n

    def cpp_blocks(self) -> list[CodeBlock]:
        return [b for b in self.code_blocks if b.lang in ("cpp", "c++", "cxx")]

    # ---------------------------------------------------------------- writing
    def save(self, fm: dict | None = None, body: str | None = None) -> bool:
        fm = self.fm if fm is None else fm
        body = self.body if body is None else body
        return write_text(self.path, render(fm, body))

    def set(self, **fields) -> bool:
        fm = dict(self.fm)
        for k, v in fields.items():
            if v is None:
                fm.pop(k, None)
            else:
                fm[k] = v
        return self.save(fm=fm)


class _Dumper(yaml.SafeDumper):
    pass


def _str_rep(dumper, data):
    style = '"' if (data.startswith("[[") or ":" in data or data.startswith(("#", "*", "&", "!", "@", "`"))) else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


_Dumper.add_representer(str, _str_rep)

FM_ORDER = ["id", "title", "aliases", "type", "domain", "tier", "status", "standard", "prereqs", "related",
            "practice", "tags", "created", "updated", "reviewed", "score", "rubric", "revise_notes"]


def render(fm: dict, body: str) -> str:
    ordered = {k: fm[k] for k in FM_ORDER if k in fm}
    ordered.update({k: v for k, v in fm.items() if k not in ordered})
    head = yaml.dump(ordered, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=1000).rstrip("\n")
    return f"---\n{head}\n---\n{body if body.startswith(chr(10)) else chr(10) + body}"


def iter_notes(root: Path | None = None):
    """All Compendium Markdown notes (skips system internals, templates, resources)."""
    root = root or paths.VAULT
    for p in sorted(root.rglob("*.md")):
        if any(part in paths.EXCLUDED_DIRS for part in p.relative_to(root).parts):
            continue
        yield p


def load_all() -> list[Note]:
    return [Note(p) for p in iter_notes()]


def file_index() -> dict[str, Path]:
    """Lower-cased stem -> path, for every file Obsidian could link to."""
    idx = {}
    for p in paths.VAULT.rglob("*"):
        if p.is_file() and ".obsidian" not in p.parts:
            idx.setdefault(p.stem.lower(), p)
            idx.setdefault(p.name.lower(), p)
    return idx


def replace_auto_blocks(text: str, generators: dict) -> str:
    """Replace every <!-- cc:auto:NAME --> ... <!-- cc:end --> region.

    NAME may carry an argument after a colon, e.g. `domain-index:D04`.
    Unknown generators are left untouched.
    """
    def sub(m):
        spec = m.group(2)
        name, _, arg = spec.partition(":")
        gen = generators.get(name)
        if gen is None:
            return m.group(0)
        content = gen(arg) if arg else gen(None)
        return f"{m.group(1)}{content.rstrip()}\n{m.group(4)}"
    return AUTO_RE.sub(sub, text)
