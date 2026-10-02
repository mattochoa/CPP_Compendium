---
type: system
tags: [system/directives]
pin: [path-course-companion, stream-state-and-input, file-io, recursion, switch-statement, operator-overloading, rule-of-zero-three-five, lambdas]
focus: [D10, D05, D06]
hold: []
deepen: [cpp-design-philosophy, object-model, abstract-machine]
updated: 2026-10-02
---
# Directives: Editor → Builder

> [!essence] The Editor's standing instructions to the hourly Builder. The frontmatter steers the work queue (`pin` ids first, `focus` domains favoured, `hold` ids skipped, `deepen` ids used on DEEPEN runs). The sections below steer *how* to write. The Builder reads this every run; the Editor rewrites it every morning.

## Active Directives
1. **Phase 3 · Proficiency: open the practice track.** Phase 2 (Spine) is complete: every wave-1 note exists and today's audit passed the eight pinned spine notes. Write [[Path — Course Companion]] first: an ordered route through the written notes with the CPP Project Continuum projects (Tiers 1–5) as milestones, each milestone naming the notes to read before starting it. Use [[Continuum Bridge]] as the source of the project ↔ note mapping, and mark a milestone "ready" only when all its notes exist.
2. **Then close the Continuum's Tier 1–3 gaps, in pin order:** [[Stream State and Robust Input]] (projects 3, 5), [[File IO]] (7, 10, 16), [[Recursion]] (9, 15), [[switch and Fallthrough]] (2), then [[Operator Overloading]], [[Rule of Zero, Three and Five]], [[Lambda Expressions]]. Each must set `practice:` and write a concrete *Practice* line for its project.
3. **Label C++26 changes as such** (Style Guide §4.6). Two new cases today: reading an uninitialized automatic variable is *erroneous behavior* in C++26 (P2795R5), not UB; and P2748R5 rejects returning a reference bound to a *temporary*, not to a named local. Say "undefined through C++23; erroneous in C++26" where it applies.
4. **Check the exact clause before quoting a rule's mechanism.** Today's errors were all mechanism-level: an invalid pointer is about *storage duration ending*, not lifetime (`[basic.compound]` ¶6 and its note); `std::launder` is for when transparent replacement does *not* hold; C++14 *permits* eliding replaceable `operator new` calls (N3664), it doesn't forbid it; `start_lifetime_as` is C++23, not C++26.
5. **"This vault's toolchain" = the TOOLCHAIN line preflight prints** (Style Guide §4.7, revised today). Currently GCC 11.4, x86-64 Ubuntu 22.04, ASan/UBSan available. Keep naming compiler, version and platform every time.
6. **Keep citing the page where the point is made, and verify it** with `cc.py src find` (one wrong Primer section title today: §6.1.1 is "Local Objects").
7. **DEEPEN runs: tighten, don't append.** The deepen queue is the three lowest-scoring reviewed notes; improve the named weak dimension (visual is the weakest across the spine: 2/3 on all 8 notes audited today).

## Quality Watchlist
- **Rules that changed between standards stated for one standard only.** Recurred today: [[Constructors]] and [[Pointers]] called uninitialized reads UB without the C++26 erroneous-behavior label; [[The C++ Object Model — What an Object Is]] dated `start_lifetime_as` to C++26 (it is C++23). Fixed.
- **Evolution-table rows describing a change backwards or too broadly.** New today: [[The C++ Abstract Machine]] (C++14 allocation elision described as the opposite), [[References]] (C++26 P2748 said to cover returning a named local). Fixed.
- **Platform-specific layouts drawn as universal** (from 09-27; no recurrence in today's 8 notes, all labelled LP64/Itanium correctly). Keep for one more audit.
- Retired: *tool evidence overstated* (the 09-27 rule itself was wrong about which toolchain the Builder uses; today's ASan/UBSan observations were reproduced by the Editor).

## Directive log
- 2026-09-23: initial directives (setup).
- 2026-09-23 (Editor #1): pinned map-d00/d07/d08; deepen queue set; citation, lifetime-vocabulary and sanitizer directives added; Watchlist opened with 3 items.
- 2026-09-23 (owner request, human run): Header Cards product opened. 13 owner sheets migrated to `05 Headers/` (status draft, for tomorrow's audit), hub map written, 44 cards registered (HDR domain); `// cc: stmts` and `cc.py export-pdf` added.
- 2026-09-27 (Editor #2): Phase 1 closed, Phase 2 pins set to the object-model → lifetime chain plus references/pointers/virtual functions/constructors; focus D04/D07/D08; deepen queue replaced; Style Guide §4.6–4.8 added; Watchlist rewritten (3 new items, 2 retired).
- 2026-10-02 (Editor #3): Phase 2 closed (8 pinned spine notes audited, all pass). Phase 3 pins: Path — Course Companion first, then 7 Continuum Tier 1–3 gap topics; focus D10/D05/D06; deepen queue reset; Style Guide §4.7 toolchain definition corrected; Watchlist rewritten.
