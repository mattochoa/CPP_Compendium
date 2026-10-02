---
type: brief
tags:
- system/brief
date: 2026-10-02
health: 83
---

# Daily Brief · 2026-10-02

> [!essence] At a glance (morning run, Editor #4, 07:14 CT)
> **Health 83/100** (82 last night; target ≥ 85) · coverage 126/357 (35%) · avg rubric 19.5/21 · reviewed share 21% → **27%** · lint 100 on every note, 0 orphans
> **8 more notes audited: 8 pass, 0 sent back, 19 fixes in 9 notes.** Two things need you: **the Builder hasn't run since 00:22 UTC (≈12 h)**, and **the compile toolchain switched to Windows MinGW GCC 16.1**, which has no AddressSanitizer and broke two examples.
> This page has two parts: this morning's run first, then last night's run (Editor #3) unchanged below it.

## Morning run (Editor #4)

### Since last night's audit
- **No Builder output.** The last Builder run was #146 at 00:22 UTC; the last commit is Editor #3's at 00:42 UTC. Nothing was written overnight, so no pins were started.
- **Toolchain:** preflight now reports `g++ 16.1.0 (local)`, which is MinGW-w64 (WinLibs UCRT) on Windows. I confirmed `-lasan` and `-lubsan` don't link; only trap-mode UBSan works. Under that toolchain, 3 of 290+ code blocks failed in the worksheet; I fixed 2 (see risks).
- **Scope:** 108 notes are in scope (drafts never audited). I took the next Tier-1 notes in the carry list. **~74 drafts carried** to tomorrow.

### Audit results
| Note | Score /21 | Verdict | Key finding |
|---|---|---|---|
| [[Undefined Behavior]] | 18 | pass | **Deep review.** C++26 erroneous behavior was called "diagnose-or-terminate, not silent". `[defns.erroneous]`: it's *well-defined*, and diagnosis is only recommended. Fixed in Mechanics and Evolution, Example 3 labelled. |
| [[Integer Representation and Two's Complement]] | 20 | pass | Said C "still permits all three" representations; C23 mandates two's complement. Fixed. Asm and `[basic.fundamental]` footnote verified. |
| [[Implicit Conversions and Promotions]] | 17 | pass | **Deep review.** Implied an out-of-range `double → int` wraps; it's UB (`[conv.fpint]`). Wrong Primer section for parameter adjustment (§6.2.4 p. 214). Both fixed. |
| [[Zero-Overhead Principle]] | 18 | pass | Called RTTI and exceptions "standard-library features" (cppreference says *language*). The C++98 Evolution row made the principle a compiler guarantee, contradicting the note. Fixed, plus 2 wording fixes. |
| [[Headers and Include Guards]] | 20 | pass | Clean. ODR-per-TU and reserved-identifier claims verified. |
| [[Declarations vs Definitions]] | 20 | pass | `[basic.def]` ¶2.1/2.2/2.3/2.5 verified. Fixed an ill-formed sample (`return f;`). |
| [[Dynamic Memory — new and delete]] | 20 | pass | **Deep review.** `[expr.new]` ¶17/¶21/¶27 verified. Fixed a muddled `f(new A, new B)` leak row and called delete-through-non-virtual-base UB. |
| [[Scope]] | 19 | pass | `int x = x;` lacked the C++26 label. Primer §6.1.1 title fixed. `[basic.scope.pdecl]` verified. |

**Deep reviews:** Undefined Behavior, Implicit Conversions and Promotions, Dynamic Memory. Checked against eel.is (`[defns.erroneous]`, `[basic.indet]`, `[conv.fpint]`, `[basic.def]`, `[expr.new]`) and cppreference (*Zero-overhead principle*).
**Fixed outside the audit set:** [[The Call Stack and Stack Frames]] and [[Performance — Measure, Don't Guess]]. Both summed into `long`, which overflows on Windows (32-bit `long`), so I switched them to `long long`. Both now pass `cc.py code` on GCC 16.1.
**Still failing:** [[Error Handling Strategies Compared]] block 4 (a `-Wterminate` warning on an intentional noexcept violation). It needs a `cc:` tag or a rewrite, so it's left for the Builder.
**System changes:** Style Guide §4.7 (toolchain wording + no-LP64 rule), Directives rewritten (pins kept, toolchain directive, deepen queue).

### Health and trends
- Health 82 → **83**. Avg rubric 19.7 → 19.5 (39 scored notes). Reviewed share 21% → 27%.
- `audit health` works again even though `RESOURCES.md` is still deleted.
- Weakest dimension today: **integration**. 4 of the 8 notes have no Continuum `practice:` link.
- The `audit worksheet` run stopped printing at the Header Cards (after `hdr-ios`), with no error. The Header Cards' code status is unverified on the new toolchain.

### Top risks
1. **Builder stalled.** No runs for ≈12 h, while Phase 3 pins wait. Velocity today is 0% of plan so far.
2. **Toolchain switch.** With MinGW there's no ASan, and `long` is 32-bit. Notes whose "observed" ASan output came from Linux GCC 11.4 can't be reproduced locally any more. More LP64-dependent examples may surface when those notes are next re-run.
3. **Audit backlog.** ~74 unaudited drafts. At 8–16 a day it takes about a week to clear if the Builder resumes at its normal pace.

### Today's plan for the Builder
- **Pins, in order (unchanged):** path-course-companion → stream-state-and-input → file-io → recursion → switch-statement → operator-overloading → rule-of-zero-three-five → lambdas. **Focus:** D10, D05, D06.
- **DEEPEN queue:** implicit-conversions, object-model, undefined-behavior (integration first: add `practice:`).
- **Watchlist:** C++26 erroneous-behavior wording · LP64 in runnable code · Evolution rows that overstate a change.

### Decisions needed from the owner
1. **Is the Builder's scheduled task still running?** Nothing since 00:22 UTC. Check that the task is enabled and the PC wasn't asleep overnight.
2. **Which compiler should be the vault's reference toolchain?** The Builder used to compile on Linux GCC 11.4 with sanitizers; it now gets Windows MinGW GCC 16.1, which has no ASan. Options: (a) keep MinGW and use Compiler Explorer for sanitizer evidence, or (b) give the Builder a Linux GCC (e.g. WSL) for runs that need ASan. I'd pick (b) if WSL is available.
3. **`RESOURCES.md` deletion is now committed.** `cc.py finish` commits uncommitted owner changes, as preflight says it will. If you didn't mean to delete it, run `git checkout bcfe78f -- "CPP Compendium/RESOURCES.md"` to restore it. The Editor schedule question and the per-note exercises question below also still stand.

---

## Evening run (Editor #3, 2026-10-01 19:25 CT)

> [!info] At a glance
> **Health ≈82/100** (84 on 09-27; target ≥ 85) · coverage 126/357 (35%) · avg rubric 19.7/21 · reviewed share 21% · lint 100 on every note re-checked
> **Phase 2 (Spine) is done; Phase 3 (Proficiency) starts now, and the practice track opens with it.** All 8 pinned spine notes pass (18–20/21) after 14 surgical fixes. Health dipped only because the Builder wrote ~52 notes while the Editor was away 09-28 → 10-01, so the unreviewed pile is now 82 drafts.

### Yesterday's output
- **Last 24 h (Ledger, UTC):** runs #130–146, 14 ledger rows: 12 new notes, 2 deepens. Velocity ≈ **58%** of the ~24/day plan. Rows missing for runs 135, 138, 139.
- **Since the last audit (09-27):** the whole wave-1 spine was finished (abstract machine → object model → storage duration → lifetime → references → pointers → virtual functions → constructors), plus 48 of 126 wave-2 notes and 8 wave-3 notes.
- **Phase:** 2 · Spine **complete** (52/52 wave-1 notes written). Current phase is **3 · Proficiency**, 48 of ~126.

### Audit results
| Note | Score /21 | Verdict | Key finding |
|---|---|---|---|
| [[The C++ Abstract Machine]] | 19 | pass | `[intro.abstract]` ¶1–¶8 and footnote 5 verified. **Evolution row was backwards:** C++14 (N3664) *permits* eliding replaceable `operator new` calls. Signed overflow said UB "through C++23" (it still is in C++26; cite `[expr.pre]` ¶4). Fixed; example re-run on GCC 11.4. |
| [[The C++ Object Model — What an Object Is]] | 18 | pass | `start_lifetime_as` dated to C++26; it is C++23 (P2590R2). Fixed. UBSan misalignment output reproduced. |
| [[Storage Duration]] | 19 | pass | Namespace-scope row ignored `thread_local`; `nm` prose named the wrong variables; garbled TLS sentence; Primer §6.1.1 title wrong. All fixed. TLS asm (local-exec vs `__tls_get_addr`) reproduced. |
| [[Object Lifetime]] | 20 | pass | **Deep review**, clean. `[basic.life]` ¶2, ¶3, ¶9–¶11 and `[class.cdtor]` verified; vptr-rewrite asm and ASan SEGV reproduced. |
| [[References]] | 19 | pass | C++26 row claimed P2748 makes returning a reference to a *named local* an error; it covers *temporaries* only. Fixed. `[dcl.ref]` ¶4/¶5/¶7 verified. |
| [[Pointers]] | 19 | pass | "Invalid pointer = target's lifetime ended" is wrong: it's *storage duration* ending (`[basic.compound]` ¶6 note). `std::launder` row inverted. Uninitialized read lacked the C++26 label. Fixed. |
| [[Virtual Functions]] | 20 | pass | **Deep review**, clean. `[class.virtual]` ¶2/¶4/¶5/¶7/¶8 verified. |
| [[Constructors]] | 20 | pass | **Deep review.** `[class.base.init]` ¶9/¶11/¶15 and `[except.ctor]` ¶3 verified. Added the C++26 erroneous-behavior label to two "indeterminate read is UB" claims. |

**Deep reviews (every claim verified):** [[Object Lifetime]], [[Virtual Functions]], [[Constructors]], against eel.is (`[basic.life]`, `[class.cdtor]`, `[class.virtual]`, `[class.base.init]`, `[except.ctor]`) and local GCC 11.4 runs.
**Fixed by Editor:** 14 surgical edits across 6 notes. Style Guide §4.7 corrected (see risk 3). Directives rewritten.
**Sent back:** none.
**Carried to tomorrow (82 drafts):** 17 Domain Maps + Map — Standard Headers, 3 Source Guides, 20 Header Cards, the Kit, and ~40 notes.

### Health and trends
- Health 84 → **≈82**. Avg rubric 19.8 → 19.7 (31 scored notes). Reviewed share 31% → 21% (more writing than auditing).
- Health was an estimate: `cc.py audit brief`/`health` crashed on the missing `CPP Compendium/RESOURCES.md`.
- Code: every example re-run behaved as claimed (8 programs, incl. ASan/UBSan runs).
- Weakest dimension: **visual**, 2/3 on all 8 notes audited.

### Top risks
1. **Audit lag.** 82 unreviewed drafts; the Editor didn't run 09-28, 09-29 or 09-30.
2. **Version and mechanism slips in Evolution tables.** 6 of 14 fixes were Evolution rows or version labels.
3. **The 09-27 toolchain rule was wrong, not the Builder.** Style Guide §4.7 now defines "this vault's toolchain" as preflight's TOOLCHAIN line.

### Decisions needed from the owner
1. **Editor schedule:** it missed 09-24 → 26 and 09-28 → 30, and this run happened in the evening (~19:25 CT), not at 7:00. Please check the scheduled task and whether the PC sleeps. A second daily Editor run is still recommended.
2. **`RESOURCES.md` was deleted (uncommitted).** Restore it, or confirm the deletion so the Builder can commit it.
3. **Practice assignments:** the Compendium links to your existing 35 Continuum projects rather than writing new assignments. Do you also want per-note exercises ("Try it" tasks inside each note)? If so, that's a new product line to open in Phase 3.
