---
type: system
tags: [system/directives]
pin: [abstract-machine, object-model, storage-duration, object-lifetime, references, pointers, virtual-functions, constructors]
focus: [D04, D07, D08]
hold: []
deepen: [cpp-design-philosophy, anatomy-of-an-expression, what-a-type-is]
updated: 2026-09-27
---
# Directives: Editor → Builder

> [!essence] The Editor's standing instructions to the hourly Builder. The frontmatter steers the work queue (`pin` ids first, `focus` domains favoured, `hold` ids skipped, `deepen` ids used on DEEPEN runs). The sections below steer *how* to write. The Builder reads this every run; the Editor rewrites it every morning.

## Active Directives
1. **Phase 2 · Spine: build the object-to-RAII walk.** Phase 1 is done (all 17 Domain Maps and the Standard Headers hub exist as drafts). Write the pinned chain in dependency order: [[The C++ Abstract Machine]] → [[The C++ Object Model — What an Object Is]] → [[Storage Duration]] → [[Object Lifetime]], then [[References]], [[Pointers]], [[Virtual Functions]], [[Constructors]]. Many written notes already link to these titles as frontier links; each new note must resolve them and back-link at least two of the reviewed notes that point at it.
2. **Say which standard a rule holds for** (Style Guide §4.6, new today). Three of today's errors were true in one standard and false in another: `i = i++ + 1` (UB only through C++14), out-of-range signed conversion (never UB; modulo 2^N since C++20), the translation phases (eight in the C++26 draft that eel.is shows, nine through C++23). Before writing "UB", "nine", "since", or a ¶ number, check the rule's history on cppreference.
3. **Label tool evidence honestly** (Style Guide §4.7, new today). Name compiler, version and platform for every asm listing, `nm` or `-E` count. "This vault's toolchain" means only the local MinGW g++. Sanitizer results you did not observe are reported behavior ("on Linux/macOS, ASan reports…"). UBSan does not check strict aliasing.
4. **Label implementation-specific layouts** (Style Guide §4.8). `sizeof(long)` is 4 on 64-bit Windows; SSO layout and the short/long test are libstdc++ facts, not `std::string` facts.
5. **Make every example demonstrate its claim.** A pitfall example must fail the naive expectation. Today's `SQUARE(2) + 3` example "proved" textual substitution with output a function would also produce; it is now `SQUARE_NAIVE(2 + 3)` → 11.
6. **Keep citing the page where the point is made, and verify it** with `cc.py src find` (unchanged from 09-23: the precision is much better now; one wrong section label today, Primer §15.7 for a p. 598 point that is §15.2.2).
7. **Stop growing already-long notes on DEEPEN runs.** [[Pointers vs References]] is 3,400 words after three deepens. The DEEPEN queue is the three lowest-scoring notes above; improve the named weak dimension (Brief lists them), and prefer tightening to appending.

## Quality Watchlist
- **Rules that changed between standards stated for one standard only.** Examples: [[Anatomy of an Expression]] (`i = i++ + 1` called UB in C++17), [[Fundamental Types]] (signed out-of-range conversion called UB, following the Primer), [[The Compilation Pipeline]] (nine phases cited against the eight-phase C++26 draft). All fixed today.
- **Tool evidence overstated or mislabelled.** Examples: [[What a Type Is]] (claimed UBSan reports type punning), [[string]] ("verified on this Linux toolchain"), [[Dangling Pointers and References]] ("ASan reports", unobserved), three D01 notes labelled GCC 11 output "this vault's toolchain". All fixed today.
- **Platform-specific layouts drawn as universal.** Examples: [[Classes as User-Defined Types]] and [[Encapsulation and Class Invariants]] (8-byte `long`), [[string]] (libstdc++'s SSO test presented as the only design). Fixed today.
- **Library mechanics described loosely** (from 09-23; one recurrence today: [[Encapsulation and Class Invariants]] said a throwing constructor leaves "nothing to destroy"; fully built members are destroyed, `[except.ctor]`).
- Retired: *citation locations imprecise* (1 of 20 notes today) and *integration weakest dimension* (now 3/3 on 16 of 20 notes).

## Directive log
- 2026-09-23: initial directives (setup).
- 2026-09-23 (Editor #1): pinned map-d00/d07/d08; deepen queue set; citation, lifetime-vocabulary and sanitizer directives added; Watchlist opened with 3 items.
- 2026-09-23 (owner request, human run): Header Cards product opened. 13 owner sheets migrated to `05 Headers/` (status draft, for tomorrow's audit), hub map written, 44 cards registered (HDR domain); `// cc: stmts` and `cc.py export-pdf` added.
- 2026-09-27 (Editor #2): Phase 1 closed, Phase 2 pins set to the object-model → lifetime chain plus references/pointers/virtual functions/constructors; focus D04/D07/D08; deepen queue replaced; Style Guide §4.6–4.8 added; Watchlist rewritten (3 new items, 2 retired).
