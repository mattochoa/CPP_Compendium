"""Run bookkeeping: counter, lock, history, ledger."""
from __future__ import annotations

import json

from . import paths
from .util import iso, load_json, now_utc, parse_iso, save_json, today, write_text

LOCK_TTL_MIN = {"builder": 55, "editor": 90, "human": 240}
HISTORY_KEEP = 200


def load() -> dict:
    s = load_json(paths.STATE, None) or {}
    s.setdefault("runs", 0)
    s.setdefault("builder_runs", 0)
    s.setdefault("editor_runs", 0)
    s.setdefault("history", [])
    s.setdefault("current", None)
    return s


def save(s: dict) -> None:
    s["history"] = s["history"][-HISTORY_KEEP:]
    save_json(paths.STATE, s)


# ----------------------------------------------------------------------------- lock
def lock_info() -> dict | None:
    # The vault lives on a mount where files cannot be deleted, so a released
    # lock is overwritten with {"released": true} instead of removed.
    if not paths.LOCK.exists():
        return None
    try:
        info = json.loads(paths.LOCK.read_text(encoding="utf-8") or "{}")
    except Exception:
        return {"role": "?", "started": iso()}
    if not info or info.get("released"):
        return None
    return info


def lock_active() -> dict | None:
    info = lock_info()
    if not info:
        return None
    age_min = (now_utc() - parse_iso(info["started"])).total_seconds() / 60
    if age_min > LOCK_TTL_MIN.get(info.get("role"), 60):
        return None   # stale: previous run died
    info["age_min"] = round(age_min)
    return info


def acquire(role: str, run_no: int, mode: str) -> None:
    paths.CACHE.mkdir(parents=True, exist_ok=True)
    paths.LOCK.write_text(json.dumps({"role": role, "run": run_no, "mode": mode, "started": iso()}), encoding="utf-8")


def release() -> None:
    if paths.LOCK.exists():
        paths.LOCK.write_text(json.dumps({"released": True, "at": iso()}), encoding="utf-8")


# ----------------------------------------------------------------------------- ledger
LEDGER_HEAD = """---
type: ledger
tags: [system/ledger]
---
# Ledger — {month}

> [!info] Append-only log of every Builder and Editor run. Written by `cc.py finish`.

| When (UTC) | Run | Role | Mode | Produced / touched | Lint | Code | Commit | Summary |
|---|---|---|---|---|---|---|---|---|
"""


def ledger_append(row: dict) -> None:
    month = today()[:7]
    p = paths.LEDGER / f"{month}.md"
    text = p.read_text(encoding="utf-8") if p.exists() else LEDGER_HEAD.format(month=month)
    cells = [row.get(k, "") for k in ("when", "run", "role", "mode", "items", "lint", "code", "commit", "summary")]
    cells = [str(c).replace("|", "/").replace("\n", " ") for c in cells]
    text = text.rstrip("\n") + "\n| " + " | ".join(cells) + " |\n"
    write_text(p, text)
