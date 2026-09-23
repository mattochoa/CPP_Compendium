"""Create a note skeleton for a registry topic from its archetype template."""
from __future__ import annotations

from . import paths, registry
from .notes import Note, render
from .util import today, today_date, write_text


def frontmatter_for(t: registry.Topic, all_topics: dict[str, registry.Topic]) -> dict:
    fm = {
        "id": t.id,
        "title": t.title,
        "aliases": list(t.aliases),
        "type": t.type,
        "domain": t.domain,
        "tier": t.tier,
        "status": "stub",
        "standard": "",
        "prereqs": [all_topics[p].link for p in t.pre if p in all_topics],
        "related": [],
        "practice": list(t.practice),
        "tags": [f"type/{t.type}", f"domain/{t.domain.lower()}", f"tier/{t.tier}"],
        "created": today_date(),
        "updated": today_date(),
    }
    if not fm["aliases"]:
        fm.pop("aliases")
    return fm


def new(topic_id: str, overwrite: bool = False) -> str:
    topics = registry.load_topics()
    idx = registry.by_id(topics)
    t = idx.get(topic_id)
    if t is None:
        raise SystemExit(f"unknown topic id `{topic_id}` (see `cc.py next` or tools/data/topics.yaml)")
    if t.note and not overwrite:
        return f"exists: {paths.rel(t.note.path)} (status {t.status})"
    spec = registry.archetypes()[t.type]
    tpl_path = paths.TEMPLATES / spec["template"]
    tpl = Note(tpl_path)
    body = tpl.body
    dom = registry.domains()[t.domain]
    repl = {"{{title}}": t.title, "{{date}}": today(), "{{id}}": t.id, "{{domain}}": t.domain,
            "{{domain_name}}": dom["name"], "{{domain_question}}": dom["question"]}
    for k, v in repl.items():
        body = body.replace(k, v)
    fm = frontmatter_for(t, idx)
    target = t.folder / f"{t.title}.md"
    write_text(target, render(fm, body))
    return f"created: {paths.rel(target)}  (status stub; set status: draft when written)"
