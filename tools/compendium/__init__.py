"""CPP Compendium toolkit.

Small, single-purpose modules driven by the `cc.py` CLI:

    paths      where everything lives
    notes      reading / writing Markdown notes (frontmatter, sections, links, code)
    registry   the topic Atlas (topics.yaml) joined with note status; work selection
    sources    local book library: text cache, TOC, search, copy-guard
    validate   structural + editorial lint of notes against archetypes.yaml
    snippets   compile / run the C++ code blocks inside notes (local g++ or Compiler Explorer)
    build      regenerate derived artefacts: auto-blocks, Coverage, Atlas canvas, Bridge, graph colours
    state      run counter, lock, ledger
    gitops     commits
    runs       preflight / finish orchestration for Builder and Editor roles
    audit      Editor tooling: worksheet, rubric recording, health score
"""
__version__ = "1.0.0"
