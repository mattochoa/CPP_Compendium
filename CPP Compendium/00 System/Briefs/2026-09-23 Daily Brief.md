---
type: brief
tags:
- system/brief
date: 2026-09-23
health: 97
---

# Daily Brief · 2026-09-23

> [!essence] At a glance
> **Health 97/100** (was 94) · coverage 6/291 (2%) · avg rubric 19.5/21 · avg lint 100 · orphans 0 · code 20/20 PASS
> The six exemplar notes all pass (19–20/21) after 11 small fixes. Two tooling bugs were fixed: one made every code check fail, the other hid notes with "—" in their titles from the audit. The Builder hasn't produced a note yet, and Phase 1 (Domain Maps) starts with its next run.

## Yesterday's output
- Builder runs: **0**. The Ledger holds only the owner's setup run. The 08:26 UTC Builder run overlapped this audit's lock.
- Velocity: n/a (plan ≈ 24 notes/day). Phase: **1 · Frame** (1 of 17 Domain Maps written).

## Audit results
| Note | Score /21 | Verdict | Key finding |
|---|---|---|---|
| [[Value Categories]] | 20 | pass | Moved-from rule oversimplified ("only assign or destroy"); member-access row lacked its conditions. Fixed. Asm verified on Compiler Explorer. |
| [[RAII]] | 20 | pass | Tour citation named §4.3 for a passage that is in §4.2. Fixed. |
| [[Virtual Dispatch — vptr and vtable]] | 20 | pass | Correct. It was an orphan, and is now linked from the D04 Map. |
| [[Dangling Pointers and References]] | 19 | pass | Mixed up "lifetime ends" and "storage released"; parameter destruction timing is implementation-defined `[expr.call]`; `string_view` quiz named the wrong function. All fixed. |
| [[Pointers vs References]] | 19 | pass | Correct. PPP cited by chapter only (fixed). Depth 2: queued for DEEPEN. |
| [[Map — Objects, Memory & Lifetime]] | 19 | pass | Correct; sources verified. Added the inbound vptr link. |

**Deep reviews (every claim verified):** [[Value Categories]], [[RAII]], [[Dangling Pointers and References]] (checked against eel.is `[expr.call]`, cppreference, book indexes and Compiler Explorer).
**Fixed by Editor:** 11 surgical edits across 5 notes, and 3 system docs (Style Guide citation examples were wrong: `Primer 13.6.2` starts on p. 534, and Pikus ch. 4 starts on p. 113, not p. 98).

## Health and trends
- Health 94 → **97** (orphan removed). Lint 100 on every note. Copy-guard clean.
- Code: 5/17 → **20/20 PASS**. Cause: the local MinGW g++ has no ASan/UBSan libraries, so every linked block failed. `snippets.py` now probes and falls back to UBSan trap mode.
- Audit scope: 4 → **6 notes**. Cause: git octal-escaped the "—" in paths, so `worksheet` skipped those notes. Fixed with `core.quotepath=false` plus UTF-8 decoding in `gitops.py`.

## Top risks
1. **Weaker UB detection on Windows.** Without ASan, `// cc: ub` demos of use-after-free can no longer be *observed* failing. This matters because 3 of 17 blocks are UB demos. Mitigation: Directive 5. Real fix: an owner decision (below).
2. **Builder hasn't run yet.** If the 09:12 UTC run doesn't produce a Map, Phase 1 slips.
3. **Citation drift.** 4 of 6 exemplars had imprecise locations, and the house example taught the error. The Style Guide is corrected and the issue is on the Watchlist.

## Today's plan for the Builder
- Pins: `map-d00` → `map-d07` → `map-d08`, then the remaining 13 Maps (wave 0). Target: all 16 today.
- Then wave 1, opening with the three Source Guides.
- DEEPEN queue: `pointers-vs-references` (depth), `dangling-pointers-and-references` (visual).
- Watchlist: citation locations · integration (≥ 2 inbound links) · exact library mechanics.

## Decisions needed from the owner
1. **Sanitizer toolchain.** Should code checks get full ASan? Options: (a) install LLVM/clang with its sanitizer runtime on Windows; (b) route `cc.py code` through the Ubuntu-24.04 WSL distro already installed. I recommend (b). (c) Accept UBSan-only checking.
2. **`RESOURCES.md` (0 bytes) at the vault root** came in with the "Quck Sync" commit. Keep it, fill it, or remove it? I left it untouched.
3. FYI: this audit ran at 03:24 CT, ahead of its 07:14 CT schedule, so the scheduled run will find only today's Builder output. No action is needed unless the early run was unintended.
