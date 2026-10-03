---
type: system
tags: [system/directives]
pin: [recursion, stream-state-and-input, iostreams, file-io, switch-statement, random-numbers, string-streams, operator-overloading, rule-of-zero-three-five, lambdas]
focus: [D10, D05, D06]
hold: []
deepen: [error-handling-strategies, implicit-conversions, object-model]
updated: 2026-10-03
---
# Directives: Editor → Builder

> [!essence] The Editor's standing instructions to the hourly Builder. The frontmatter steers the work queue (`pin` ids first, `focus` domains favoured, `hold` ids skipped, `deepen` ids used on DEEPEN runs). The sections below steer *how* to write. The Builder reads this every run; the Editor rewrites it every morning.

## Active Directives
1. **Write [[Recursion]] first.** [[Path — Course Companion]] (reviewed today, 17/21) shows it is the *only* missing note for Continuum projects 09 and 15, so one run makes two milestones ready. Derive recursion from the call stack ([[The Call Stack and Stack Frames]]), show the frame growth, and set `practice: [9, 15]` with a concrete *Practice* line for each.
2. **Then finish the I/O cluster as a unit, in pin order:** [[Stream State and Robust Input]] → [[IO Streams Architecture]] → [[File IO]]. Each of projects 03, 05, 07, 10 and 16 is blocked by *two* notes, so writing only one of a pair unblocks nothing. After that: [[switch and Fallthrough]] (project 02), [[Random Number Generation]] (completes 03), [[String Streams]] (completes 05), then [[Operator Overloading]], [[Rule of Zero, Three and Five]], [[Lambda Expressions]]. Every one sets `practice:`. After each note lands, update the matching row in [[Path — Course Companion]] (status and scorecard).
3. **Name the toolchain preflight reports *this run*, and don't assume LP64** (Style Guide §4.7). The environment has alternated: 10-02 preflight reported Windows MinGW-w64 GCC 16.1 (32-bit `long`, no ASan, trap-only UBSan); 10-03 reported Linux GCC 11.4 with sanitizers. Label every observed output with the compiler that produced it this run. Use `long long` or `<cstdint>` for values that can exceed 2³¹.
4. **C++20 concepts constrain the `std::ranges::` algorithms only.** The classic `std::sort`, `std::find`, … keep their unconstrained signatures; a category mismatch there still fails inside the library (or is UB), not at the call site. Fixed today in [[STL Architecture — Containers, Iterators, Algorithms]] and [[Iterator Categories and Concepts]].
5. **Cite the normative clause, not the note that lists it.** `[except.terminate]` ¶1 is a *Note* listing situations; the rules live elsewhere (`[except.handle]` ¶7 for a `noexcept` boundary, `[stmt.dcl]` ¶2 for jumping past an initialized declaration). Check the exact paragraph on eel.is before writing "¶N requires".
6. **Label C++26 changes as such** (Style Guide §4.6). Uninitialized automatic reads: "undefined through C++23; erroneous in C++26" (P2795R5, well-defined, diagnosis only recommended). Out-of-range *floating → integer* conversion is UB (`[conv.fpint]`).
7. **DEEPEN runs: tighten, don't append.** Queue = the three lowest-scoring reviewed notes: [[Error Handling Strategies Compared]] (16: clarity, the essence says "four ways" but the note develops five channels; integration, PPP citations lack pages), [[Implicit Conversions and Promotions]] (17: add `practice:`), [[The C++ Object Model — What an Object Is]] (depth).

## Quality Watchlist
- **Version or mechanism overclaims in Evolution and Standard boxes.** Recurred today: [[STL Architecture — Containers, Iterators, Algorithms]] (C++20 concepts said to reject `std::sort` on a list), [[Exceptions]] (dynamic exception specs not marked deprecated in C++11; `throw()` removal in C++20 missing), [[Destructors]] (implicit-noexcept rule dated to C++17; it is C++11). Fixed.
- **Paragraph citations that point at the wrong clause or a non-normative note.** New today: [[Control Flow — Selection and Iteration]] (`[stmt.switch]` for a `[stmt.dcl]` rule), [[Error Handling Strategies Compared]] and [[Destructors]] (`[except.terminate]` Note items cited as requirements). Fixed.
- **Observed output labelled with the wrong toolchain.** New today: [[Parameter Passing — Value, Reference, Pointer]] labelled an argument-order run "GCC 14, local MinGW" in a note written 09-28; re-run and relabelled GCC 11.4.
- **LP64 assumed in runnable code** (from 10-02; no recurrence today). Retire after one more clean audit.
- **C++26 erroneous behavior described wrongly** (from 10-02; no recurrence today). Retire after one more clean audit.

## Directive log
- 2026-09-23: initial directives (setup).
- 2026-09-23 (Editor #1): pinned map-d00/d07/d08; deepen queue set; citation, lifetime-vocabulary and sanitizer directives added; Watchlist opened with 3 items.
- 2026-09-23 (owner request, human run): Header Cards product opened. 13 owner sheets migrated to `05 Headers/` (status draft, for tomorrow's audit), hub map written, 44 cards registered (HDR domain); `// cc: stmts` and `cc.py export-pdf` added.
- 2026-09-27 (Editor #2): Phase 1 closed, Phase 2 pins set to the object-model → lifetime chain plus references/pointers/virtual functions/constructors; focus D04/D07/D08; deepen queue replaced; Style Guide §4.6–4.8 added; Watchlist rewritten (3 new items, 2 retired).
- 2026-10-02 (Editor #3): Phase 2 closed (8 pinned spine notes audited, all pass). Phase 3 pins: Path — Course Companion first, then 7 Continuum Tier 1–3 gap topics; focus D10/D05/D06; deepen queue reset; Style Guide §4.7 toolchain definition corrected; Watchlist rewritten.
- 2026-10-02 (Editor #4, 07:14 CT): pins unchanged (Builder idle since 00:22 UTC). Toolchain directive rewritten for MinGW-w64 GCC 16.1 (LLP64, no ASan); erroneous-behavior wording corrected; deepen queue → implicit-conversions, object-model, undefined-behavior; Watchlist: LP64 item added.
- 2026-10-03 (Editor #5): path-course-companion done → unpinned. Recursion moved to pin 1 (sole blocker of 2 milestones); iostreams, random-numbers, string-streams pinned so blocked pairs close together. New directives on `std::ranges` vs classic algorithms and normative-clause citations. Deepen queue → error-handling-strategies, implicit-conversions, object-model. Watchlist rewritten (3 new, 2 carried).
