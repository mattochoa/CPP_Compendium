"""Filesystem layout. Everything is derived from this file's location, so the
repo can be moved or cloned anywhere."""
from __future__ import annotations

from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
REPO = TOOLS.parent
VAULT = REPO / "CPP Compendium"

SYSTEM = VAULT / "00 System"
TEMPLATES = SYSTEM / "Templates"
LEDGER = SYSTEM / "Ledger"
BRIEFS = SYSTEM / "Briefs"
DIRECTIVES = SYSTEM / "Directives.md"
COVERAGE = SYSTEM / "Coverage.md"
MAPS = VAULT / "01 Maps"
NOTES = VAULT / "02 Notes"
SOURCES = VAULT / "03 Sources"
PRACTICE = VAULT / "04 Practice"
HEADERS = VAULT / "05 Headers"     # Header Cards: one quick-reference card per standard header
HEADER_PDFS = VAULT / "__RESOURCES__" / "std-headers-pdf"   # git-ignored PDF exports of the cards
RESOURCES = VAULT / "__RESOURCES__"
HOME = VAULT / "Home.md"
ATLAS_CANVAS = MAPS / "Atlas.canvas"
BRIDGE = PRACTICE / "Continuum Bridge.md"
OBSIDIAN = VAULT / ".obsidian"

DATA = TOOLS / "data"
BOOK_TOC = DATA / "books"
STATE = TOOLS / "state" / "state.json"

CACHE = REPO / ".cache"            # git-ignored; rebuildable
BOOK_TEXT = CACHE / "books"
LOCK = CACHE / "run.lock"
SETUP_MARKER = CACHE / "SETUP_IN_PROGRESS"
SCRATCH = CACHE / "scratch"

# Sibling project: the 35-project C++ curriculum (outside the vault)
CONTINUUM = REPO.parents[2] / "CPP_Project_Continuum" if len(REPO.parents) > 2 else REPO / "_missing_"

# Folders that never contain Compendium notes
EXCLUDED_DIRS = {".obsidian", "__RESOURCES__", "Templates", ".trash"}


def rel(p: Path) -> str:
    """Path relative to the repo root, forward slashes (stable in logs)."""
    try:
        return p.resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError:
        return p.as_posix()
