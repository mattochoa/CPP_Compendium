#!/usr/bin/env python3
"""One-time (idempotent) Obsidian configuration for the Compendium vault.

Merges settings into existing .obsidian/*.json files. It never deletes the
owner's own settings:
  * enables the `compendium` CSS snippet (Visual Language callouts)
  * points core Templates at 00 System/Templates
  * hides templates and generated system noise from search/graph
  * bookmarks Home, Charter, Directives, Coverage, the Atlas canvas and dashboards
  * opens on Home
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compendium import build, paths  # noqa: E402

O = paths.OBSIDIAN


def load(name: str) -> dict:
    p = O / name
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save(name: str, data: dict) -> None:
    (O / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("updated", name)


def main() -> None:
    O.mkdir(exist_ok=True)
    app = load("app.json")
    ignore = set(app.get("userIgnoreFilters") or [])
    ignore.update({"00 System/Templates/"})
    app["userIgnoreFilters"] = sorted(ignore)
    app.setdefault("alwaysUpdateLinks", True)
    app.setdefault("newLinkFormat", "shortest")
    app.setdefault("showFrontmatter", False)
    save("app.json", app)

    ap = load("appearance.json")
    snippets = set(ap.get("enabledCssSnippets") or [])
    snippets.add("compendium")
    ap["enabledCssSnippets"] = sorted(snippets)
    save("appearance.json", ap)

    tp = load("templates.json")
    tp["folder"] = "00 System/Templates"
    save("templates.json", tp)

    cp = load("core-plugins.json")
    for k in ("templates", "bases", "canvas", "bookmarks", "graph", "backlink", "outline", "properties"):
        cp[k] = True
    save("core-plugins.json", cp)

    bm = load("bookmarks.json")
    items = bm.get("items") or []
    have = {i.get("path") for i in items}
    now = int(time.time() * 1000)
    wanted = [
        ("Home.md", "Home"),
        ("01 Maps/Atlas.canvas", "Atlas"),
        ("00 System/Charter.md", "Charter"),
        ("00 System/Directives.md", "Directives"),
        ("00 System/Coverage.md", "Coverage"),
        ("00 System/Dashboards/Pipeline.base", "Pipeline"),
        ("04 Practice/Continuum Bridge.md", "Continuum Bridge"),
    ]
    group = {"type": "group", "ctime": now, "title": "CPP Compendium", "items": []}
    for path, title in wanted:
        if path not in have:
            group["items"].append({"type": "file", "ctime": now, "path": path, "title": title})
    if group["items"] and not any(i.get("title") == "CPP Compendium" for i in items):
        items.insert(0, group)
        bm["items"] = items
        save("bookmarks.json", bm)

    build.build_graph_colors(build.Ctx())
    print("graph colour groups set per domain")


if __name__ == "__main__":
    main()
