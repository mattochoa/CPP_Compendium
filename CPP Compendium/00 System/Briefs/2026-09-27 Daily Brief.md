---
type: brief
tags:
- system/brief
date: 2026-09-27
health: 84
---

# Daily Brief · 2026-09-27

> [!essence] At a glance
> **Health 84/100** (78 before this audit; target ≥ 85) · coverage 74/354 (21%) · avg rubric 19.8/21 · avg lint 100 · orphans 0 · code 100% PASS
> Phase 1 (Domain Maps) is complete and Phase 2 (Spine) is well under way. All 20 audited spine notes pass (18–21/21), but only after about 40 surgical fixes: 11 of the 20 had a correctness slip, most often a rule stated for the wrong C++ standard or a sanitizer result that was never observed. This is the first audit since 09-23, so 51 drafts are still waiting.

## Yesterday's output
- **Last 24 h:** 17 Builder runs, 14 new notes, 3 deepens. Plan is about 24 a day, so velocity is **58%**. Ledger rows are missing for runs 48, 59 and 64, and nothing ran between 22:27 and 03:40 UTC, about 5 runs lost.
- **Since the last audit (09-23):** runs 21–66 finished all 17 Domain Maps, the 3 Source Guides and about 33 wave-1 notes.
- **Phase:** 1 · Frame is **done** (maps are drafts, still to audit). Current phase is **2 · Spine**, about 33 of ~50.

## Audit results
| Note | Score /21 | Verdict | Key finding |
|---|---|---|---|
| [[Virtual Dispatch — vptr and vtable]] | 21 | pass | Clean. Re-scored after back-weave; integration now 3. |
| [[Pointers vs References]] | 20 | pass | Deep review: all 7 clause cites verified. Fixed `[expr.add]` ¶4.3→¶4.2. Getting long (3.4k words). |
| [[Dangling Pointers and References]] | 20 | pass | "ASan reports…" was stated as if observed (Directive 5). Reworded. |
| [[The Compilation Pipeline]] | 20 | pass | Deep review. Cited "nine phases" against the C++26 draft, which has eight. The `SQUARE(2)+3` example didn't prove its point. Both fixed and re-compiled. Map D01 fixed too. |
| [[Translation Units]] | 20 | pass | Tool label ("this vault's toolchain" for GCC 11). Fixed. |
| [[The Preprocessor]] | 20 | pass | Said macros collide "program-wide" (they're per translation unit). Quiz answer on `f() f()` was wrong. Fixed. |
| [[const and Const-Correctness]] | 20 | pass | Deep review: `[basic.type.qualifier]` ¶1.1/¶5/¶6 and `[expr.prim.this]` ¶4 verified. Low-level-const rule re-attributed to `[conv.qual]`. |
| [[Fundamental Types]] | 20 | pass | **Core error fixed:** it called out-of-range signed conversion UB, following the Primer. It is modulo 2^N since C++20 `[conv.integral]`. |
| [[What a Type Is]] | 19 | pass | Claimed UBSan catches type punning (it doesn't). Cited the wrong clause (`[basic.lval]` ¶11). Diagram bytes didn't match the printed value. Fixed. |
| [[Anatomy of an Expression]] | 19 | pass | **Core error fixed:** `i = i++ + 1` shown as UB, but it is well-defined since C++17. |
| [[Precedence and Associativity]] | 20 | pass | Stray self-correction in the derivation; example heading said "prefix" for postfix. Fixed. |
| [[Process Memory Layout — Stack, Heap, Static]] | 20 | pass | Pointer comparison after storage end is implementation-defined. Added. |
| [[Anatomy of a Function]] | 20 | pass | "No overload on return type" was cited to the wrong clause. Fixed. |
| [[Classes as User-Defined Types]] | 20 | pass | Layout diagram assumed 8-byte `long`, which is wrong on Windows. Fixed. |
| [[Encapsulation and Class Invariants]] | 20 | pass | Same `long` issue. Claimed a throwing constructor has "nothing to destroy" (built members are destroyed). Fixed. |
| [[Ownership — Who Releases What]] | 20 | pass | Clean; `[expr.delete]` ¶2 verified. |
| [[Inheritance]] | 20 | pass | Wrong Primer section (§15.7 → §15.2.2); a trap heading said "derived" for "base". Fixed. |
| [[Templates — Code That Writes Code]] | 20 | pass | Clean. |
| [[string]] | 20 | pass | "Verified on this Linux toolchain" was false. libstdc++ SSO internals were presented as universal. COW/SSO history was wrong. Fixed. |
| [[The C++ Design Philosophy]] | 18 | pass | Copy elision was described as an as-if-rule case. Fixed. Depth, visuals and integration thin: queued for DEEPEN. |

**Deep reviews (every claim verified):** [[Pointers vs References]], [[const and Const-Correctness]], [[The Compilation Pipeline]]. These were checked against eel.is (`[dcl.ref]`, `[class.copy.assign]`, `[expr.add]`, `[expr.rel]`, `[basic.type.qualifier]`, `[expr.prim.this]`, `[lex.phases]`), cppreference and `cc.py src find`.
**Fixed by Editor:** about 40 surgical edits across 17 notes plus Map D01. Style Guide §4.6–4.8 added. Directives rewritten.
**Sent back:** none. Every defect had an unambiguous fix.
**Carried to tomorrow (51):** 16 Domain Maps and Map — Standard Headers, 3 Source Guides, 20 Header Cards, the Kit, and 10 notes: functions-and-parameters, function-overloading, class-overloading, stl-architecture, std-vector, iterators, iterator-categories, error-handling-strategies, concurrency-vs-parallelism, compilers-and-flags.

## Health and trends
- Health 78 → **84**. Reviewed share went from 4% to 31%. Avg rubric is 19.8.
- Lint 100 on every note. Code blocks 100% PASS; the Compilation Pipeline's new example compiled clean.
- Orphans 0. Copy-guard is clean. No note is awaiting revise.
- Weakest dimension now: **visual**, 2/3 on 9 of 20 notes. Integration improved to 3/3 on 16 of 20.

## Top risks
1. **Correct-looking notes that are wrong for the reader's standard.** 3 core errors today came from rules that changed between C++11, 17, 20 and 26. They are hard to spot because the Primer says the old thing. Mitigation: Style Guide §4.6 and Directive 2.
2. **The audit backlog is outrunning the audit.** 51 drafts are unreviewed, the cap is 24 a day, and the Builder adds about 15 a day. This only closes if the Editor actually runs daily (it didn't on 09-24, 25 or 26).
3. **Sanitizer claims nobody can check locally.** Without ASan on Windows, the Builder keeps describing ASan results it never saw (3 notes today).

## Today's plan for the Builder
- **Pins, in order:** abstract-machine → object-model → storage-duration → object-lifetime → references → pointers → virtual-functions → constructors. **Focus:** D04, D07, D08.
- **DEEPEN queue:** cpp-design-philosophy (depth/visual/integration), anatomy-of-an-expression (depth/integration), what-a-type-is (depth/integration). Tighten, don't append.
- **Watchlist:** version span for rules that changed · honest tool labels · ABI/library labels for layouts · exact library mechanics.

## Decisions needed from the owner
1. **The Editor didn't run on 09-24, 09-25 or 09-26.** Is the scheduled task disabled, or was the computer asleep at 7:00 CT? Please check it. Without daily audits the backlog grows by about 15 notes a day.
2. **Audit capacity.** Options: (a) add a second daily Editor run, for example at 19:00 CT; (b) raise the per-run cap from 24 to 36; (c) accept a multi-day lag. I recommend **(a)**, because a 60-minute run can't deep-read more than about 20 notes well.
3. **Sanitizer toolchain (open since 09-23).** Route `cc.py code` `// cc: ub` blocks through the installed Ubuntu WSL so ASan results are really observed. This is still my recommendation; today's 3 sanitizer defects are the cost of waiting.
4. FYI, no action needed unless you want it: the Ledger has two duplicate rows (09-24 20:15, run "?") and logs some DEEPEN runs as AUTHOR (#33, #45, #46). `RESOURCES.md` is still 0 bytes (decision from 09-23 still open).
