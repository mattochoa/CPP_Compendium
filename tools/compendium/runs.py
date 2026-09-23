"""Run orchestration: `preflight` opens a run, `finish` closes it.

Builder modes
  AUTHOR   write the next topic in the queue (default)
  REVISE   fix a note the Editor sent back (takes priority whenever one exists)
  DEEPEN   every 6th Builder run: raise the weakest existing note one rubric level
Editor mode
  AUDIT    daily: audit, fix, re-prioritise, direct, brief
"""
from __future__ import annotations

import shutil
import subprocess
import urllib.request

from . import build, gitops, paths, registry, snippets, sources, state, validate
from .notes import Note
from .util import iso, today_date

DEEPEN_EVERY = 6


def _toolchain() -> str:
    exe = shutil.which("g++")
    local = "none"
    if exe:
        local = "g++ " + subprocess.run([exe, "-dumpversion"], capture_output=True, text=True).stdout.strip()
    try:
        urllib.request.urlopen(urllib.request.Request("https://godbolt.org/api/version"), timeout=6)
        remote = "Compiler Explorer reachable"
    except Exception:
        remote = "Compiler Explorer UNREACHABLE (C++23 blocks cannot be verified)"
    return f"{local} (local) · {remote}"


def _directive_text() -> str:
    if not paths.DIRECTIVES.exists():
        return "(no Directives.md)"
    n = Note(paths.DIRECTIVES)
    sec = n.section("Active Directives").strip()
    return sec or "(none)"


def preflight(role: str = "builder") -> int:
    print(f"CPP COMPENDIUM · PREFLIGHT · role={role} · {iso()}")
    if paths.SETUP_MARKER.exists() and not paths.SETUP_MARKER.read_text(encoding="utf-8").startswith("done"):
        print("STOP: setup in progress (.cache/SETUP_IN_PROGRESS). Nothing to do this run.")
        return 0
    if not gitops.is_repo():
        print("STOP: repo root is not a git repository.")
        return 0
    b = gitops.busy()
    if b:
        print(f"STOP: git operation in progress ({b}); a human is mid-merge. Try next run.")
        return 0
    held = state.lock_active()
    if held:
        print(f"STOP: another run holds the lock (role={held.get('role')}, run {held.get('run')}, {held.get('age_min')} min old).")
        return 0

    st = state.load()
    topics = registry.load_topics()
    probs = registry.registry_problems(topics)
    st["runs"] += 1
    key = "builder_runs" if role == "builder" else "editor_runs"
    st[key] += 1
    run_no = st[key]

    if role == "builder":
        revise = [t for t in topics if t.status == "revise"]
        deepen = registry.deepen_candidates(topics)
        if revise:
            mode = "REVISE"
        elif run_no % DEEPEN_EVERY == 0 and deepen:
            mode = "DEEPEN"
        else:
            mode = "AUTHOR"
    else:
        mode = "AUDIT"

    state.acquire(role, run_no, mode)
    st["current"] = {"role": role, "run": run_no, "mode": mode, "started": iso()}
    state.save(st)
    try:
        _report(role, run_no, st, mode, topics, probs)
    except Exception as exc:  # never leave a lock behind a crashed preflight
        state.release()
        print(f"STOP: preflight failed ({type(exc).__name__}: {exc}). Lock released; report this.")
        raise
    return 0


def _report(role, run_no, st, mode, topics, probs) -> None:
    print(f"RUN: {role} #{run_no} (global #{st['runs']}) · MODE: {mode}")
    print(f"TOOLCHAIN: {_toolchain()}")
    rd = sources.ready()
    print("BOOK INDEX: " + " ".join(f"{k}{'✓' if v else '✗'}" for k, v in rd.items())
          + ("" if all(rd.values()) else "  → run `python3 tools/cc.py src build` (repeat until all ✓) before researching"))
    if probs:
        print("REGISTRY PROBLEMS (fix first):\n  " + "\n  ".join(probs[:15]))
    dirty = [d for d in gitops.dirty() if not d.startswith(("tools/state/", ".cache/"))]
    if dirty:
        print("UNCOMMITTED CHANGES (likely the user's own edits — never overwrite them; they will be committed with this run):")
        for d in dirty[:20]:
            print("  · " + d)
    print("\nDIRECTIVES FROM THE EDITOR:\n" + _directive_text())
    c = registry.counts(topics)
    print(f"\nATLAS: {len(topics)} topics · " + " · ".join(f"{k} {v}" for k, v in c.items()))
    if role == "builder":
        if mode == "DEEPEN":
            print("\nDEEPEN CANDIDATES:")
            for i, (t, why) in enumerate(registry.deepen_candidates(topics), 1):
                print(f"  {i}. {t.id:34} {t.title}  [{t.status}] {why}")
        print("\nWORK QUEUE:")
        for i, (t, why) in enumerate(registry.candidates(topics, limit=8), 1):
            print(f"  {i}. {t.id:34} {t.title}  [{t.type} · {t.domain} · T{t.tier}] — {why}")
        print(f"\nNEXT: read '00 System/Run Protocol.md' and execute the {mode} procedure.")
    else:
        print("\nNEXT: read '00 System/Audit Protocol.md' and execute it. Start with `python3 tools/cc.py audit worksheet`.")


def finish(role: str, items: list[str], summary: str, force: bool = False, commit: bool = True,
           push: bool = True, mode: str | None = None) -> int:
    st = state.load()
    cur = st.get("current") or {}
    mode = mode or cur.get("mode", "?")
    topics = registry.load_topics()
    idx = registry.by_id(topics)
    lint_scores, code_summary, failures = [], [], []
    for iid in items:
        t = idx.get(iid)
        if not t or not t.note:
            print(f"finish: `{iid}` has no note; skipping")
            continue
        note = Note(t.note.path)
        if role == "builder" and note.status == "stub":
            note.set(status="draft")
            note = Note(t.note.path)
        issues = validate.check(note)
        errs = [i for i in issues if i.level == "error"]
        res = snippets.check_note(note)
        bad = [r for r in res if r.status == "FAIL"]
        lint_scores.append(validate.score(issues))
        code_summary.append(f"{sum(r.status == 'PASS' for r in res)}/{len(res)}")
        if errs or bad:
            failures.append((note, errs, bad))
        if role == "builder":
            note.set(updated=today_date())
    if failures and not force and role == "builder":
        print("finish: BLOCKED — fix these, then run finish again (the lock is still held):")
        for note, errs, bad in failures:
            print(f"\n{note.stem}")
            for e in errs:
                print("  " + str(e))
            for r in bad:
                print(str(r))
        return 1
    for note, errs, bad in (failures if role == "builder" else []):   # forced through: park it for the Editor
        Note(note.path).set(status="revise", revise_notes="auto: failed checks at finish — " +
                            "; ".join([e.msg for e in errs][:3] + [f"code block {r.index} fails" for r in bad][:2]))
    changed = build.build_all(verbose=False)
    lint = f"{min(lint_scores)}–{max(lint_scores)}" if lint_scores else "-"
    names = ", ".join(f"[[{idx[i].title}]]" for i in items if i in idx) or "—"
    entry = {"when": iso(), "run": cur.get("run", "?"), "role": role, "mode": mode, "items": names,
             "lint": lint, "code": " ".join(code_summary) or "-", "commit": "✓" if commit else "—", "summary": summary}
    state.ledger_append(entry)
    st["history"].append({**entry, "items": items})
    st["current"] = None
    st[f"last_{role}"] = iso()
    state.save(st)
    state.release()
    msg = f"{role} #{cur.get('run', '?')} {mode}: " + (", ".join(idx[i].title for i in items if i in idx) or summary[:60])
    sha = gitops.commit(msg) if commit else "-"
    pushed = gitops.try_push() if (commit and push and sha not in ("-",) and not sha.startswith("FAILED")) else ""
    print(f"finish: {role} run closed · lint {lint} · code {entry['code']} · commit {sha} {pushed}")
    print(f"        derived artefacts refreshed: {len(changed)}")
    return 0
