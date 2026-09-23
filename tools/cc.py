#!/usr/bin/env python3
"""cc — the CPP Compendium command line.

Run from anywhere:  python3 tools/cc.py <command> [...]

  Run lifecycle
    preflight [--role builder|editor]   open a run: lock, mode, queue, directives
    finish --role R --items id,id --summary "..." [--force] [--no-commit]
    unlock                               clear a stuck lock (humans only)

  Knowledge base
    status                               one-screen overview
    next [-n N]                          the Builder's work queue
    new <id>                             scaffold a note from its archetype template
    check [targets] [--all|--changed H] [--no-copy-guard]   lint notes
    code <targets>                       compile/run every C++ block in notes
    asm <file.cpp> [--flags "..."]       assembly via Compiler Explorer
    build                                regenerate derived pages, canvas, graph colours
    export-pdf [targets] [--out DIR]     PDF of notes (default: every written Header Card) via Edge/Chrome headless

  Sources
    src build [--book K] [--force]       extract book text + TOC (resumable)
    src find "query" [--book K] [-n N]   full-text search → cite + page + section
    src toc [--book K] [--grep RX]       table of contents
    src read <book> <pages>              e.g.  src read primer 531-533   |  src read tour i:120
    src suggest <id>                     TOC sections relevant to a topic

  Registry
    registry check | show <id> | add --id --title --type --domain --tier --wave [--pre a,b] [--pr 1,2]

  Editor
    audit worksheet [--hours H] | record <id> --scores a,f,c,d,v,k,i [--notes ".."] [--verdict pass|revise]
    audit promote | health | brief

Targets are topic ids, note titles, or paths.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from compendium import (audit, build, gitops, paths, registry, runs, scaffold,  # noqa: E402
                        snippets, sources, state, validate)
from compendium.notes import Note, load_all  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def resolve_targets(targets: list[str]) -> list[Note]:
    topics = registry.load_topics()
    idx = registry.by_id(topics)
    by_title = {t.title.lower(): t for t in topics}
    out = []
    for tg in targets:
        p = Path(tg)
        if p.suffix == ".md" and (p.exists() or (paths.REPO / p).exists()):
            out.append(Note(p if p.exists() else paths.REPO / p))
        elif tg in idx and idx[tg].note:
            out.append(Note(idx[tg].note.path))
        elif tg.lower() in by_title and by_title[tg.lower()].note:
            out.append(Note(by_title[tg.lower()].note.path))
        else:
            print(f"?? no note for target `{tg}`")
    return out


def cmd_status(_a):
    topics = registry.load_topics()
    c = registry.counts(topics)
    st = state.load()
    print(f"CPP Compendium · {len(topics)} topics · " + " · ".join(f"{registry.GLYPH[k]} {k} {v}" for k, v in c.items()))
    print(f"runs: builder {st['builder_runs']} · editor {st['editor_runs']} · lock: {state.lock_active() or 'free'}")
    for h in st["history"][-5:]:
        print(f"  {h['when']}  {h['role']:7} {h['mode']:7} {h.get('items')}  — {h.get('summary', '')[:70]}")
    print("next:")
    for t, why in registry.candidates(topics, 5):
        print(f"  · {t.id:34} {t.title} — {why}")


def cmd_next(a):
    for i, (t, why) in enumerate(registry.candidates(registry.load_topics(), a.n), 1):
        print(f"{i:2}. {t.id:34} {t.title:55} [{t.type} · {t.domain} · T{t.tier} · w{t.wave}] {why}")


def cmd_check(a):
    if a.all:
        notes = load_all()
    elif a.changed is not None:
        rels = set(gitops.changed_since(a.changed)) | {d for d in gitops.dirty() if d.endswith(".md")}
        notes = [Note(paths.REPO / r) for r in sorted(rels) if (paths.REPO / r).exists()]
    else:
        notes = resolve_targets(a.targets)
    results = validate.check_many(notes, copy_guard=not a.no_copy_guard)
    n_err = 0
    for p, issues in results.items():
        n = Note(p)
        if n.fm.get("type") in validate.SYSTEM_TYPES and not issues:
            continue
        e = sum(i.level == "error" for i in issues)
        n_err += e
        print(f"{'✗' if e else '✓'} {validate.score(issues):3}  {paths.rel(p)}")
        for i in issues:
            if i.level == "error" or not a.errors_only:
                print("      " + str(i))
    probs = registry.registry_problems(registry.load_topics())
    for pr in probs:
        print("REGISTRY  " + pr)
    return 1 if (n_err or probs) else 0


def cmd_code(a):
    rc = 0
    for n in resolve_targets(a.targets):
        print(n.stem)
        for r in snippets.check_note(n):
            print(r)
            rc |= r.status == "FAIL"
    return rc


def cmd_export(a):
    from compendium import export
    if a.targets:
        notes = resolve_targets(a.targets)
    else:   # default: every written Header Card
        notes = [Note(t.note.path) for t in registry.load_topics() if t.type == "header" and t.status in registry.DONE]
    out = Path(a.out) if a.out else None
    rc = 0
    for n in notes:
        msg = export.export(n, out)
        print(msg)
        rc |= msg.startswith(("FAILED", "timeout"))
    return rc


def cmd_asm(a):
    code = sys.stdin.read() if a.file == "-" else Path(a.file).read_text(encoding="utf-8")
    print(snippets.asm(code, a.flags, a.compiler))


def cmd_src(a):
    if a.sub == "build":
        sources.build(a.book, force=a.force, budget_s=a.budget)
    elif a.sub == "find":
        for h in sources.find(a.query, a.book, a.n):
            print(f"{h['cite']:6} p.{h['page']:>5} (i:{h['i']})  §{h['section'][:60]}\n        …{h['snippet']}…")
    elif a.sub == "toc":
        for e in sources.toc_grep(a.book, a.grep):
            print(f"{e['cite']:6} {'  ' * e['level']}{e['title']}  → p.{e['label']} (i:{e['i']})")
    elif a.sub == "read":
        print(sources.read(a.book, a.pages))
    elif a.sub == "suggest":
        t = registry.by_id(registry.load_topics()).get(a.id)
        if not t:
            raise SystemExit("unknown id")
        words = t.title.replace("—", " ").replace("-", " ").split() + [w for k in t.kw for w in str(k).split()] + list(t.aliases)
        for e in sources.suggest(words):
            print(f"{e['cite']:6} {e['title']}  → p.{e['label']} (i:{e['i']})")


def cmd_registry(a):
    topics = registry.load_topics()
    if a.sub == "check":
        probs = registry.registry_problems(topics)
        print("\n".join(probs) or f"registry OK · {len(topics)} topics")
        return 1 if probs else 0
    if a.sub == "show":
        t = registry.by_id(topics).get(a.id)
        if not t:
            raise SystemExit("unknown id")
        print(f"{t.id}: {t.title} [{t.type} · {t.domain} · T{t.tier} · w{t.wave}] status={t.status}")
        print(f"  path: {paths.rel(t.path)}\n  pre: {t.pre}\n  kw: {t.kw}\n  practice: {t.practice}\n  aliases: {t.aliases}")
        return 0
    if a.sub == "add":
        if a.id in registry.by_id(topics):
            raise SystemExit(f"id exists: {a.id}")
        fields = [f"id: {a.id}", f't: "{a.title}"', f"ty: {a.type}", f"d: {a.domain}", f"tier: {a.tier}", f"w: {a.wave}"]
        if a.pre:
            fields.append(f"pre: [{a.pre}]")
        if a.pr:
            fields.append(f"pr: [{a.pr}]")
        if a.kw:
            fields.append("kw: [" + ", ".join(f'"{k.strip()}"' for k in a.kw.split(",")) + "]")
        line = "- {" + ", ".join(fields) + "}"
        p = paths.DATA / "topics.yaml"
        text = p.read_text(encoding="utf-8")
        if "# ---------------------------------------------------------------- ADDITIONS" not in text:
            text = text.rstrip("\n") + "\n\n# ---------------------------------------------------------------- ADDITIONS\n# Appended by `cc.py registry add`; the Editor files them into their domain sections.\n"
        p.write_text(text.rstrip("\n") + "\n" + line + "\n", encoding="utf-8", newline="\n")
        from compendium.util import load_yaml
        load_yaml.cache_clear()
        probs = registry.registry_problems(registry.load_topics())
        print(line)
        if probs:
            print("WARNING:\n  " + "\n  ".join(probs))
        return 0


def cmd_audit(a):
    if a.sub == "worksheet":
        audit.worksheet(a.hours)
    elif a.sub == "record":
        scores = [int(x) for x in a.scores.split(",")]
        print(audit.record(a.id, scores, a.notes or "", a.verdict))
    elif a.sub == "promote":
        print("promoted to evergreen: " + (", ".join(audit.promote()) or "none"))
    elif a.sub == "health":
        audit.print_health()
    elif a.sub == "brief":
        print(audit.brief_scaffold())


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cc", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("preflight"); p.add_argument("--role", default="builder", choices=["builder", "editor"])
    p = sp.add_parser("finish")
    p.add_argument("--role", default="builder", choices=["builder", "editor", "human"])
    p.add_argument("--items", default="")
    p.add_argument("--summary", default="")
    p.add_argument("--mode")
    p.add_argument("--force", action="store_true")
    p.add_argument("--no-commit", action="store_true")
    p.add_argument("--no-push", action="store_true")
    sp.add_parser("unlock")
    sp.add_parser("status")
    p = sp.add_parser("next"); p.add_argument("-n", type=int, default=10)
    p = sp.add_parser("new"); p.add_argument("id"); p.add_argument("--overwrite", action="store_true")
    p = sp.add_parser("check"); p.add_argument("targets", nargs="*"); p.add_argument("--all", action="store_true")
    p.add_argument("--changed", type=float, metavar="HOURS"); p.add_argument("--no-copy-guard", action="store_true")
    p.add_argument("--errors-only", action="store_true")
    p = sp.add_parser("code"); p.add_argument("targets", nargs="+")
    p = sp.add_parser("asm"); p.add_argument("file"); p.add_argument("--flags", default="-O2 -std=c++20")
    p.add_argument("--compiler")
    sp.add_parser("build")
    p = sp.add_parser("export-pdf"); p.add_argument("targets", nargs="*"); p.add_argument("--out")

    p = sp.add_parser("src"); ss = p.add_subparsers(dest="sub", required=True)
    q = ss.add_parser("build"); q.add_argument("--book"); q.add_argument("--force", action="store_true")
    q.add_argument("--budget", type=float, default=150.0)
    q = ss.add_parser("find"); q.add_argument("query"); q.add_argument("--book"); q.add_argument("-n", type=int, default=12)
    q = ss.add_parser("toc"); q.add_argument("--book"); q.add_argument("--grep")
    q = ss.add_parser("read"); q.add_argument("book"); q.add_argument("pages")
    q = ss.add_parser("suggest"); q.add_argument("id")

    p = sp.add_parser("registry"); ss = p.add_subparsers(dest="sub", required=True)
    ss.add_parser("check")
    q = ss.add_parser("show"); q.add_argument("id")
    q = ss.add_parser("add")
    for f in ("id", "title", "type", "domain"):
        q.add_argument(f"--{f}", required=True)
    q.add_argument("--tier", type=int, default=2); q.add_argument("--wave", type=int, default=3)
    q.add_argument("--pre"); q.add_argument("--pr"); q.add_argument("--kw")

    p = sp.add_parser("audit"); ss = p.add_subparsers(dest="sub", required=True)
    q = ss.add_parser("worksheet"); q.add_argument("--hours", type=float)
    q = ss.add_parser("record"); q.add_argument("id"); q.add_argument("--scores", required=True)
    q.add_argument("--notes"); q.add_argument("--verdict", choices=["pass", "revise"])
    ss.add_parser("promote"); ss.add_parser("health"); ss.add_parser("brief")

    a = ap.parse_args(argv)
    if a.cmd == "preflight":
        return runs.preflight(a.role)
    if a.cmd == "finish":
        items = [x.strip() for x in a.items.split(",") if x.strip()]
        return runs.finish(a.role, items, a.summary, force=a.force, commit=not a.no_commit,
                           push=not a.no_push, mode=a.mode)
    if a.cmd == "unlock":
        state.release()
        print("lock released")
        return 0
    if a.cmd == "new":
        print(scaffold.new(a.id, a.overwrite))
        return 0
    if a.cmd == "build":
        build.build_all()
        return 0
    handler = {"status": cmd_status, "next": cmd_next, "check": cmd_check, "code": cmd_code, "asm": cmd_asm,
               "src": cmd_src, "registry": cmd_registry, "audit": cmd_audit, "export-pdf": cmd_export}[a.cmd]
    return handler(a) or 0


if __name__ == "__main__":
    sys.exit(main())
