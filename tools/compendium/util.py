"""Tiny shared helpers (YAML IO, time, text)."""
from __future__ import annotations

import datetime as _dt
import functools
import json
import re
from pathlib import Path

import yaml


@functools.lru_cache(maxsize=None)
def load_yaml(path: Path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_json(path: Path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    tmp.replace(path)


def write_text(path: Path, text: str) -> bool:
    """Write only if content changed. Returns True when the file changed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == text:
        return False
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return True


def now_utc() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0)


def iso(dt: _dt.datetime | None = None) -> str:
    return (dt or now_utc()).isoformat().replace("+00:00", "Z")


def parse_iso(s: str) -> _dt.datetime:
    return _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def today() -> str:
    # Local calendar date for the user (America/Chicago). Fixed offset is good
    # enough for dating notes; exact DST handling is not needed here.
    try:
        from zoneinfo import ZoneInfo
        return _dt.datetime.now(ZoneInfo("America/Chicago")).date().isoformat()
    except Exception:  # pragma: no cover
        return _dt.date.today().isoformat()


def today_date() -> _dt.date:
    """Today's local date as a date object (YAML dumps it unquoted, so Obsidian types it as a date)."""
    return _dt.date.fromisoformat(today())


WORD_RE = re.compile(r"[A-Za-z0-9_']+")


def words(text: str) -> list[str]:
    return WORD_RE.findall(text)


def bar(fraction: float, width: int = 10) -> str:
    fraction = max(0.0, min(1.0, fraction))
    full = round(fraction * width)
    return "█" * full + "░" * (width - full)
