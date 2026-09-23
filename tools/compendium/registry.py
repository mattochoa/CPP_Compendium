"""The Atlas: topics.yaml joined with the vault's notes.

Status lifecycle (note frontmatter `status`):
    planned   (no note yet: implicit)
    stub      scaffolded by `cc.py new`, not yet written
    draft     written by the Builder, passes automated checks
    revise    sent back by the Editor (see `revise_notes`)
    reviewed  passed the Editor's rubric
    evergreen reviewed, integrated, and stable for 14+ days with score >= 18
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import paths
from .notes import Note, load_all
from .util import load_yaml

STATUSES = ["planned", "stub", "draft", "revise", "reviewed", "evergreen"]
DONE = {"draft", "reviewed", "evergreen", "revise"}   # counts as "exists" for prerequisites
GLYPH = {"planned": "○", "stub": "◌", "draft": "◐", "revise": "⟲", "reviewed": "●", "evergreen": "★"}
TYPES = ["map", "concept", "mechanism", "idiom", "pitfall", "comparison", "evolution", "guide", "path", "header"]
BAD_FILENAME = re.compile(r'[:/\\?*<>|"]')


@dataclass
class Topic:
    id: str
    title: str
    type: str
    domain: str
    tier: int
    wave: int
    order: int
    pre: list = field(default_factory=list)
    kw: list = field(default_factory=list)
    practice: list = field(default_factory=list)
    aliases: list = field(default_factory=list)
    note: Note | None = None

    @property
    def status(self) -> str:
        if self.note is None:
            return "planned"
        return self.note.status or "stub"

    @property
    def glyph(self) -> str:
        return GLYPH.get(self.status, "?")

    @property
    def folder(self) -> Path:
        if self.type == "map":
            return paths.MAPS
        return paths.VAULT / domains()[self.domain]["folder"]

    @property
    def path(self) -> Path:
        return self.note.path if self.note else self.folder / f"{self.title}.md"

    @property
    def link(self) -> str:
        return f"[[{self.title}]]"


def domains() -> dict[str, dict]:
    return {d["code"]: d for d in load_yaml(paths.DATA / "domains.yaml")}


def archetypes() -> dict[str, dict]:
    return load_yaml(paths.DATA / "archetypes.yaml")


def load_topics(notes: list[Note] | None = None) -> list[Topic]:
    raw = load_yaml(paths.DATA / "topics.yaml") or []
    topics = []
    for i, r in enumerate(raw):
        topics.append(Topic(
            id=r["id"], title=r["t"], type=r["ty"], domain=r["d"], tier=int(r.get("tier", 1)),
            wave=int(r.get("w", 2)), order=i, pre=list(r.get("pre") or []), kw=list(r.get("kw") or []),
            practice=list(r.get("pr") or []), aliases=list(r.get("al") or []),
        ))
    notes = load_all() if notes is None else notes
    by_id = {n.id: n for n in notes if n.id}
    by_stem = {n.stem.lower(): n for n in notes}
    for t in topics:
        t.note = by_id.get(t.id) or by_stem.get(t.title.lower())
    return topics


def registry_problems(topics: list[Topic]) -> list[str]:
    """Integrity checks on topics.yaml itself."""
    probs, ids, titles = [], set(), set()
    doms = domains()
    for t in topics:
        if t.id in ids:
            probs.append(f"duplicate id: {t.id}")
        if t.title.lower() in titles:
            probs.append(f"duplicate title: {t.title}")
        ids.add(t.id)
        titles.add(t.title.lower())
        if BAD_FILENAME.search(t.title):
            probs.append(f"title not a legal file name: {t.title}")
        if t.type not in TYPES:
            probs.append(f"{t.id}: unknown type {t.type}")
        if t.domain not in doms:
            probs.append(f"{t.id}: unknown domain {t.domain}")
    for t in topics:
        for p in t.pre:
            if p not in ids:
                probs.append(f"{t.id}: unknown prerequisite {p}")
    return probs


def by_id(topics: list[Topic]) -> dict[str, Topic]:
    return {t.id: t for t in topics}


def directives() -> dict:
    """Machine-readable part of Directives.md (its frontmatter)."""
    if not paths.DIRECTIVES.exists():
        return {}
    return Note(paths.DIRECTIVES).fm or {}


def candidates(topics: list[Topic], limit: int = 10) -> list[tuple[Topic, str]]:
    """Ordered work queue for the Builder: (topic, reason)."""
    d = directives()
    pins = [p for p in (d.get("pin") or [])]
    hold = set(d.get("hold") or [])
    focus = list(d.get("focus") or [])
    idx = by_id(topics)
    out: list[tuple[Topic, str]] = []
    seen: set[str] = set()

    def add(t: Topic, why: str):
        if t.id not in seen and t.id not in hold:
            out.append((t, why))
            seen.add(t.id)

    # 1. Editor send-backs, oldest review first
    revise = sorted((t for t in topics if t.status == "revise"),
                    key=lambda t: str(t.note.fm.get("reviewed") or ""))
    for t in revise:
        add(t, "revise: " + str(t.note.fm.get("revise_notes") or "see Editor notes")[:80])
    # 2. Stubs left behind by an interrupted run
    for t in topics:
        if t.status == "stub":
            add(t, "finish stub")
    # 3. Editor pins
    for pid in pins:
        t = idx.get(pid)
        if t and t.status in ("planned", "stub"):
            add(t, "pinned by Editor")
    # 4. Planned topics: lowest wave, prerequisites satisfied, balanced across domains
    written_per_domain: dict[str, int] = {}
    total_per_domain: dict[str, int] = {}
    for t in topics:
        total_per_domain[t.domain] = total_per_domain.get(t.domain, 0) + 1
        if t.status in DONE:
            written_per_domain[t.domain] = written_per_domain.get(t.domain, 0) + 1

    def ready(t: Topic) -> bool:
        for p in t.pre:
            pt = idx.get(p)
            if pt and pt.wave <= t.wave and pt.status not in DONE:
                return False
        return True

    planned = [t for t in topics if t.status == "planned" and t.id not in hold]

    def key(t: Topic):
        coverage = written_per_domain.get(t.domain, 0) / max(1, total_per_domain.get(t.domain, 1))
        return (t.wave, 0 if t.domain in focus else 1, 0 if ready(t) else 1, round(coverage, 2), t.order)

    for t in sorted(planned, key=key):
        add(t, f"wave {t.wave}" + ("" if ready(t) else " (prereqs pending)") + (" · focus" if t.domain in focus else ""))
        if len(out) >= limit:
            break
    return out[:limit]


def deepen_candidates(topics: list[Topic], limit: int = 5) -> list[tuple[Topic, str]]:
    """Existing notes most in need of deepening (DEEPEN runs)."""
    d = directives()
    idx = by_id(topics)
    out = [(idx[i], "Editor requested deepening") for i in (d.get("deepen") or []) if i in idx and idx[i].note]
    pool = [t for t in topics if t.note and t.status in ("draft", "reviewed")]

    def key(t: Topic):
        score = t.note.fm.get("score")
        score = int(score) if isinstance(score, (int, float)) else 99
        return (score, str(t.note.fm.get("updated") or ""), t.order)

    for t in sorted(pool, key=key):
        if all(t.id != o.id for o, _ in out):
            out.append((t, f"score={t.note.fm.get('score', 'n/a')} updated={t.note.fm.get('updated', '?')}"))
    return out[:limit]


def counts(topics: list[Topic]) -> dict[str, int]:
    c = {s: 0 for s in STATUSES}
    for t in topics:
        c[t.status] = c.get(t.status, 0) + 1
    return c
