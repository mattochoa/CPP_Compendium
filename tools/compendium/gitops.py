"""Git operations, safe on a mount where files cannot be deleted.

The vault's folder is mounted into the agent's Linux VM with *delete disabled*
(renames work, unlinks don't). Git normally deletes lock and temp files, so:
  * read-only commands run with --no-optional-locks (no index.lock at all);
  * objects are finalised by rename (core.createObject=rename), gc is off;
  * stale *.lock files older than LOCK_STALE_MIN are renamed into
    .git/cc-stale-locks/ before each write operation.
Commits are attributed to the automation, never to the owner's identity.
"""
from __future__ import annotations

import os
import subprocess
import time

from . import paths

ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
SAFE = ["-c", "core.createObject=rename", "-c", "gc.auto=0", "-c", "maintenance.auto=false",
        "-c", "core.fsmonitor=false"]
BOT = ["-c", "user.name=CPP Compendium Bot", "-c", "user.email=noreply@anthropic.com",
       "-c", "commit.gpgsign=false"]   # never block on a signing prompt
TRAILER = "\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
LOCK_STALE_MIN = 10


def git(*args, check=False, timeout=90, write=False) -> subprocess.CompletedProcess:
    pre = [] if write else ["--no-optional-locks"]
    return subprocess.run(["git", *pre, "-C", str(paths.REPO), *SAFE, *args], capture_output=True, text=True,
                          timeout=timeout, check=check, env=ENV)


def sweep_stale_locks(max_age_min: float = LOCK_STALE_MIN) -> list[str]:
    """Rename abandoned git lock files out of the way (they cannot be deleted here)."""
    gd = paths.REPO / ".git"
    moved = []
    if not gd.is_dir():
        return moved
    now = time.time()
    for p in list(gd.glob("*.lock")) + list((gd / "refs").rglob("*.lock")):
        try:
            if now - p.stat().st_mtime < max_age_min * 60:
                continue
            dest = gd / "cc-stale-locks"
            dest.mkdir(exist_ok=True)
            p.rename(dest / f"{p.name}.{int(now)}")
            moved.append(p.name)
        except OSError:
            pass
    return moved


def is_repo() -> bool:
    return git("rev-parse", "--is-inside-work-tree").stdout.strip() == "true"


def busy() -> str | None:
    """A merge/rebase/cherry-pick in progress (or a *fresh* index.lock) means someone is mid-operation."""
    sweep_stale_locks()
    gd = paths.REPO / ".git"
    for marker in ("MERGE_HEAD", "rebase-merge", "rebase-apply", "CHERRY_PICK_HEAD", "index.lock"):
        if (gd / marker).exists():
            return marker
    return None


def dirty() -> list[str]:
    out = git("status", "--porcelain", "-uall").stdout
    return [ln[3:].strip().strip('"') for ln in out.splitlines() if ln.strip()]


def changed_since(hours: float) -> list[str]:
    out = git("log", f"--since={int(hours * 60)} minutes ago", "--name-only", "--pretty=format:").stdout
    return sorted({ln.strip() for ln in out.splitlines() if ln.strip().endswith(".md")})


def commit(message: str) -> str:
    sweep_stale_locks()
    a = git("add", "-A", "--", ".", write=True)
    sweep_stale_locks(max_age_min=0)
    if a.returncode != 0:
        return "FAILED(add): " + (a.stderr or a.stdout).strip()[:200]
    if not git("diff", "--cached", "--name-only").stdout.strip():
        return "-"
    cp = git(*BOT, "commit", "-q", "--no-verify", "-m", message + TRAILER, write=True)
    # git could not unlink its own lock files (e.g. HEAD.lock); they are ours, so clear them now
    sweep_stale_locks(max_age_min=0)
    if cp.returncode != 0:
        return "FAILED: " + (cp.stderr or cp.stdout).strip()[:200]
    return git("rev-parse", "--short", "HEAD").stdout.strip()


def try_push(timeout=25) -> str:
    try:
        cp = git("push", "-q", timeout=timeout, write=True)
        return "pushed" if cp.returncode == 0 else "not pushed (no credentials in the agent VM; push from GitHub Desktop / Obsidian Git)"
    except subprocess.TimeoutExpired:
        return "push timed out"
