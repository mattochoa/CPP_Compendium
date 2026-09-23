---
type: system
tags: [system/directives]
pin: [map-d00, map-d07, map-d08]
focus: []
hold: []
deepen: [pointers-vs-references, dangling-pointers-and-references]
updated: 2026-09-23
---
# Directives: Editor → Builder

> [!essence] The Editor's standing instructions to the hourly Builder. The frontmatter steers the work queue (`pin` ids first, `focus` domains favoured, `hold` ids skipped, `deepen` ids used on DEEPEN runs). The sections below steer *how* to write. The Builder reads this every run; the Editor rewrites it every morning.

## Active Directives
1. **Phase 1 · Frame.** Finish all 16 remaining Domain Maps (wave 0) today. Start with the pinned three: [[Map — What C++ Is]] (the root every map links to), then [[Map — Ownership & Move Semantics]] and [[Map — Inheritance & Polymorphism]], which the reviewed notes [[RAII]] and [[Virtual Dispatch — vptr and vtable]] already point to. Each map derives its question from first principles and draws its concept map with *registered* titles only.
2. **Use [[Map — Objects, Memory & Lifetime]] as the map exemplar** (19/21). Beat it on *depth*: every Key Idea gets one supporting sentence that states a mechanism, not a slogan.
3. **Cite the page where the point is made**, not only where the section starts: `Primer §12.1.2 (p. 463)`, not `(p. 458)`. Verify every page with `cc.py src find` before writing it. The PPP edition has no printed pages: cite `PPP §17.4`, never a bare chapter. (The old house example `Primer 13.6.2 (p. 532)` was wrong; the Style Guide is corrected.)
4. **Precision on lifetime vocabulary.** *Lifetime* ends when the destructor starts; *storage* is released when its storage duration ends (scope exit, `delete`, program end), which can be later. Don't conflate them, and quote the clause (`[basic.life]`, `[basic.stc.general]`) when the difference matters.
5. **Code verification changed today.** Local g++ (MinGW) has no ASan/UBSan runtime; `cc.py code` now falls back to UBSan trap mode automatically. Never write "ASan reports X" as if the check had observed it: say what ASan reports *on Linux/macOS* and keep the block `// cc: ub`.
6. Every note names at least one of the Five Tensions (tag `tension/...` plus a `[!tension]` or `[!principle]` callout), and every C++14+ behavior is checked against cppreference: the Primer is C++11.
7. **After wave 0**, begin wave 1 with the Source Guides (`guide-primer`, `guide-tour`, `guide-web-references`) before the concept notes. They make every later citation faster and more precise.

## Quality Watchlist
- **Citation locations are imprecise** (4 of 6 exemplars fixed today): section-start pages instead of the page of the point, PPP cited by chapter only, one Tour passage attributed to the wrong section. Example: [[RAII]] cited Tour "§4.3, p. 45"; the passage is in §4.2.
- **Integration is the weakest rubric dimension** (2/3 on all six reviewed notes). New notes must add inbound links from ≥ 2 written notes (Run Protocol §3.6) and cite ≥ 3 sources with exact locations.
- **Library mechanics described loosely.** Example: [[Dangling Pointers and References]] said `string_view`'s *constructor* takes the temporary; it is `std::string`'s conversion operator. Name the exact function that does the work.

## Directive log
- 2026-09-23: initial directives (setup).
- 2026-09-23 (Editor #1): pinned map-d00/d07/d08; deepen queue set; citation, lifetime-vocabulary and sanitizer directives added; Watchlist opened with 3 items.
