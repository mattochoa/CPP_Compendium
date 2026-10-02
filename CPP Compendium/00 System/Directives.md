---
type: system
tags: [system/directives]
pin: [path-course-companion, stream-state-and-input, file-io, recursion, switch-statement, operator-overloading, rule-of-zero-three-five, lambdas]
focus: [D10, D05, D06]
hold: []
deepen: [implicit-conversions, object-model, undefined-behavior]
updated: 2026-10-02
---
# Directives: Editor → Builder

> [!essence] The Editor's standing instructions to the hourly Builder. The frontmatter steers the work queue (`pin` ids first, `focus` domains favoured, `hold` ids skipped, `deepen` ids used on DEEPEN runs). The sections below steer *how* to write. The Builder reads this every run; the Editor rewrites it every morning.

## Active Directives
1. **Phase 3 · Proficiency: the practice track is still unopened.** No Builder run has happened since 00:22 UTC, so none of yesterday's pins were started. Write [[Path — Course Companion]] first: an ordered route through the written notes with the CPP Project Continuum projects (Tiers 1–5) as milestones, each milestone naming the notes to read before starting it. Use [[Continuum Bridge]] as the project ↔ note mapping, and mark a milestone "ready" only when all its notes exist.
2. **Then close the Continuum's Tier 1–3 gaps, in pin order:** [[Stream State and Robust Input]] (projects 3, 5), [[File IO]] (7, 10, 16), [[Recursion]] (9, 15), [[switch and Fallthrough]] (2), then [[Operator Overloading]], [[Rule of Zero, Three and Five]], [[Lambda Expressions]]. Each must set `practice:` and write a concrete *Practice* line for its project.
3. **The toolchain changed: name it every time, and don't assume LP64** (Style Guide §4.7, revised today). Preflight now reports MinGW-w64 GCC 16.1 on Windows: `long` is 32 bits, ASan is not available, and UBSan runs in trap mode only (no message text). Use `long long` or `<cstdint>` types for any value that can exceed 2³¹. Don't present an ASan/UBSan *message* as observed unless you produced it this run (Compiler Explorer with `-fsanitize=address` is fine; label it so).
4. **Label C++26 changes as such** (Style Guide §4.6). Reading an uninitialized automatic variable is *erroneous behavior* in C++26 (P2795R5): **well-defined**, with an implementation-chosen value, and diagnosis is only *recommended*. It is not "diagnose-or-terminate". It stays UB for heap objects, for `indeterminate`-attributed variables, and when the value isn't valid for the type (`[basic.indet]`). Write "undefined through C++23; erroneous in C++26".
5. **Check the exact clause before quoting a rule's mechanism.** Today's fixes: out-of-range *floating → integer* conversion is UB (`[conv.fpint]`), only *integer → integer* wraps; RTTI and exceptions are *language* features; the zero-overhead principle is a design criterion, never normative text.
6. **Keep citing the page where the point is made, and verify it** with `cc.py src find` (today: array-parameter adjustment is Primer §6.2.4 p. 214, not §4.11.2).
7. **DEEPEN runs: tighten, don't append.** Queue = the three lowest-scoring reviewed notes. Improve the named weak dimension: integration (missing `practice:`) for implicit-conversions and undefined-behavior; depth for object-model.

## Quality Watchlist
- **C++26 erroneous behavior described wrongly or not at all.** Recurred today: [[Undefined Behavior]] ("diagnose-or-terminate, not silent"), [[Scope]] (`int x = x;` unlabelled). Fixed.
- **LP64 assumed in runnable code.** New today: [[The Call Stack and Stack Frames]] and [[Performance — Measure, Don't Guess]] summed into `long`, which overflows on Windows and failed `cc.py code`. Fixed with `long long`.
- **Evolution-table rows that overstate or invert a change.** Recurred today: [[Zero-Overhead Principle]] (C++98 row made the principle a compiler guarantee). Fixed.
- **Platform-specific layouts drawn as universal** (from 09-27; no recurrence in two audits). Retire after the next clean audit.

## Directive log
- 2026-09-23: initial directives (setup).
- 2026-09-23 (Editor #1): pinned map-d00/d07/d08; deepen queue set; citation, lifetime-vocabulary and sanitizer directives added; Watchlist opened with 3 items.
- 2026-09-23 (owner request, human run): Header Cards product opened. 13 owner sheets migrated to `05 Headers/` (status draft, for tomorrow's audit), hub map written, 44 cards registered (HDR domain); `// cc: stmts` and `cc.py export-pdf` added.
- 2026-09-27 (Editor #2): Phase 1 closed, Phase 2 pins set to the object-model → lifetime chain plus references/pointers/virtual functions/constructors; focus D04/D07/D08; deepen queue replaced; Style Guide §4.6–4.8 added; Watchlist rewritten (3 new items, 2 retired).
- 2026-10-02 (Editor #3): Phase 2 closed (8 pinned spine notes audited, all pass). Phase 3 pins: Path — Course Companion first, then 7 Continuum Tier 1–3 gap topics; focus D10/D05/D06; deepen queue reset; Style Guide §4.7 toolchain definition corrected; Watchlist rewritten.
- 2026-10-02 (Editor #4, 07:14 CT): pins unchanged (Builder idle since 00:22 UTC). Toolchain directive rewritten for MinGW-w64 GCC 16.1 (LLP64, no ASan); erroneous-behavior wording corrected; deepen queue → implicit-conversions, object-model, undefined-behavior; Watchlist: LP64 item added.
