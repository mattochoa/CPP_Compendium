"""Editor tooling: worksheet, rubric recording, promotion, health, brief scaffold."""
from __future__ import annotations

import datetime as _dt

from . import gitops, paths, registry, snippets, state, validate
from .notes import Note, render
from .util import bar, parse_iso, now_utc, today, today_date, write_text

RUBRIC = ["accuracy", "first_principles", "clarity", "depth", "visual", "code", "integration"]
RUBRIC_LABEL = {
    "accuracy": "Accuracy — correct, precise, standard-conformant, versions labelled",
    "first_principles": "First principles — idea derived from the problem and constraints",
    "clarity": "Conceptual clarity — one mental model, precise vocabulary, no hand-waving",
    "depth": "Depth — mechanics, under-the-hood, edge cases, evolution",
    "visual": "Visual communication — diagrams/tables carry meaning; Visual Language followed",
    "code": "Code — minimal, compiled, annotated, idiomatic modern C++",
    "integration": "Integration — links, prereqs, sources with locations, practice",
}
PASS_TOTAL = 16          # of 21
EVERGREEN_TOTAL = 18
EVERGREEN_AGE_DAYS = 14


def _since_hours() -> float:
    st = state.load()
    last = st.get("last_editor")
    if not last:
        return 24 * 7
    return max(1.0, (now_utc() - parse_iso(last)).total_seconds() / 3600 + 0.5)


def worksheet(hours: float | None = None) -> None:
    hours = hours or _since_hours()
    topics = registry.load_topics()
    by_path = {t.note.path.resolve(): t for t in topics if t.note}
    changed = gitops.changed_since(hours)
    dirty = [d for d in gitops.dirty() if d.endswith(".md")]
    targets = []
    for rel in sorted(set(changed) | set(dirty)):
        p = (paths.REPO / rel).resolve()
        t = by_path.get(p)
        if t and t.status in ("draft", "reviewed", "evergreen", "revise"):
            targets.append(t)
    # Drafts never audited are always in scope
    for t in topics:
        if t.status == "draft" and t not in targets:
            targets.append(t)
    print(f"AUDIT WORKSHEET · {today()} · window {hours:.0f}h · {len(targets)} notes in scope\n")
    for t in targets:
        n = Note(t.note.path)
        issues = validate.check(n)
        res = snippets.check_note(n)
        print(f"■ {t.id} · {t.title} · {t.type} · {t.domain} · status={t.status} · words={n.word_count} "
              f"· diagrams={n.diagram_count} · tables={n.table_count} · lint={validate.score(issues)}")
        for i in issues:
            print("    " + str(i))
        for r in res:
            if r.status != "PASS":
                print("  " + str(r))
        print(f"    code: {sum(r.status == 'PASS' for r in res)}/{len(res)} pass")
        prev = n.fm.get("rubric")
        if prev:
            print(f"    previous rubric: {prev} (score {n.fm.get('score')})")
        print()
    print("RUBRIC (0 absent · 1 weak · 2 solid · 3 exemplary) — pass = total ≥ 16/21 and no dimension at 0:")
    for k in RUBRIC:
        print(f"  {k:17} {RUBRIC_LABEL[k]}")
    print("\nRecord each verdict:  python3 tools/cc.py audit record <id> --scores a,f,c,d,v,k,i --notes \"...\"")


def record(topic_id: str, scores: list[int], notes: str = "", verdict: str | None = None) -> str:
    topics = registry.load_topics()
    t = registry.by_id(topics).get(topic_id)
    if not t or not t.note:
        raise SystemExit(f"no note for `{topic_id}`")
    if len(scores) != len(RUBRIC) or any(s not in (0, 1, 2, 3) for s in scores):
        raise SystemExit(f"--scores needs {len(RUBRIC)} integers 0-3 in order: {','.join(RUBRIC)}")
    total = sum(scores)
    passed = total >= PASS_TOTAL and 0 not in scores
    if verdict is None:
        verdict = "pass" if passed else "revise"
    status = "reviewed" if verdict == "pass" else "revise"
    fields = {"rubric": dict(zip(RUBRIC, scores)), "score": total, "reviewed": today_date(), "status": status,
              "revise_notes": notes if status == "revise" else None}
    if status == "reviewed" and t.status == "evergreen":
        fields["status"] = "evergreen"
    Note(t.note.path).set(**fields)
    return f"{topic_id}: {total}/21 → {fields['status']}" + (f" · {notes}" if status == "revise" else "")


def promote() -> list[str]:
    """reviewed → evergreen when score ≥ 18 and reviewed ≥ 14 days ago with no open lint errors."""
    out = []
    for t in registry.load_topics():
        if t.status != "reviewed":
            continue
        fm = t.note.fm
        sc = fm.get("score")
        rv = fm.get("reviewed")
        if not isinstance(sc, int) or sc < EVERGREEN_TOTAL or not rv:
            continue
        try:
            age = (_dt.date.today() - _dt.date.fromisoformat(str(rv))).days
        except ValueError:
            continue
        if age < EVERGREEN_AGE_DAYS:
            continue
        if any(i.level == "error" for i in validate.check(Note(t.note.path), copy_guard=False)):
            continue
        Note(t.note.path).set(status="evergreen")
        out.append(t.id)
    return out


def health() -> dict:
    topics = registry.load_topics()
    written = [t for t in topics if t.status in registry.DONE]
    notes = [Note(t.note.path) for t in written]
    lint = [validate.score(validate.check(n, copy_guard=False)) for n in notes]
    scores = [n.fm.get("score") for n in notes if isinstance(n.fm.get("score"), int)]
    # integration: notes with at least one inbound link from another note
    inbound: dict[str, int] = {}
    for n in notes:
        for l in set(n.links):
            inbound[l.lower()] = inbound.get(l.lower(), 0) + 1
    orphans = [n.stem for n in notes if inbound.get(n.stem.lower(), 0) == 0]
    reviewed_share = sum(1 for t in written if t.status in ("reviewed", "evergreen")) / max(1, len(written))
    h = {
        "topics": len(topics),
        "written": len(written),
        "coverage": len(written) / max(1, len(topics)),
        "avg_lint": sum(lint) / max(1, len(lint)),
        "avg_score": (sum(scores) / len(scores)) if scores else None,
        "reviewed_share": reviewed_share,
        "revise": sum(1 for t in topics if t.status == "revise"),
        "orphans": orphans,
    }
    quality = (h["avg_score"] / 21) if h["avg_score"] is not None else 0.5
    h["health"] = round(100 * (0.35 * quality + 0.25 * h["avg_lint"] / 100 + 0.2 * reviewed_share
                               + 0.2 * (1 - len(orphans) / max(1, len(notes)))))
    return h


def print_health() -> None:
    h = health()
    print(f"HEALTH {h['health']}/100")
    print(f"  coverage       `{bar(h['coverage'])}` {h['written']}/{h['topics']} ({h['coverage']:.0%})")
    print(f"  avg lint       {h['avg_lint']:.0f}/100")
    print(f"  avg rubric     {h['avg_score']:.1f}/21" if h["avg_score"] is not None else "  avg rubric     n/a")
    print(f"  reviewed share {h['reviewed_share']:.0%}")
    print(f"  awaiting revise {h['revise']}")
    print(f"  orphans        {len(h['orphans'])}: {', '.join(h['orphans'][:12])}")


def brief_scaffold() -> str:
    p = paths.BRIEFS / f"{today()} Daily Brief.md"
    if p.exists():
        return f"exists: {paths.rel(p)}"
    tpl = Note(paths.TEMPLATES / "T-Daily Brief.md")
    h = health()
    body = tpl.body.replace("{{date}}", today()).replace("{{health}}", str(h["health"])).replace(
        "{{coverage}}", f"{h['written']}/{h['topics']} ({h['coverage']:.0%})").replace(
        "{{avg_score}}", f"{h['avg_score']:.1f}/21" if h["avg_score"] is not None else "n/a").replace(
        "{{avg_lint}}", f"{h['avg_lint']:.0f}")
    write_text(p, render({"type": "brief", "date": today_date(), "health": h["health"], "tags": ["system/brief"]}, body))
    return f"created: {paths.rel(p)}"
