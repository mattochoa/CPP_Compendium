---
type: home
tags: [system/home]
cssclasses: [cc-home]
---
# The CPP Compendium

> [!essence]
> A conceptual atlas of C++. Every feature is explained as **the answer to a problem**, seen through **three lenses** (the source you write, the abstract machine that defines its meaning, and the real machine that runs it), and placed on **one map** of the language.

## The frame

Every note is written inside the same two frames, so hundreds of notes read as one work. Details are in the [[Charter]].

```mermaid
flowchart LR
    S["<b>Source</b><br/>what you write"]:::concept -- "the Standard gives meaning" --> A["<b>Abstract Machine</b><br/>what it means"]:::focus
    A -- "the compiler lowers it (as-if)" --> R["<b>Real Machine</b><br/>what executes"]:::mech
    classDef concept fill:#312e81,stroke:#818cf8,color:#eef2ff
    classDef focus fill:#78350f,stroke:#fbbf24,color:#fffbeb
    classDef mech fill:#134e4a,stroke:#2dd4bf,color:#f0fdfa
```

> [!tension] The Five Tensions: every C++ design decision takes a position on these
> **abstraction ⟷ control** · **value ⟷ identity** · **compile time ⟷ run time** · **safety ⟷ performance** · **compatibility ⟷ evolution**

## The Atlas

Open **[[Atlas.canvas|the Atlas canvas]]** to see the whole language on one board. Each domain answers one question:

<!-- cc:auto:home-domains -->
| | Domain | The question it answers | Progress |
|---|---|---|---|
| `D00` | [[Map — What C++ Is\|What C++ Is]] | What contract does C++ make between the programmer, the compiler and the machine? | `█░░░░░░░` 1/9 |
| `D01` | [[Map — Program Structure & Build\|Program Structure & Build]] | How does text in many files become one running program? | `░░░░░░░░` 1/18 |
| `D02` | [[Map — Types & Values\|Types & Values]] | How are meaning and operations attached to raw bits? | `░░░░░░░░` 1/25 |
| `D03` | [[Map — Expressions & Control\|Expressions & Control]] | How does a program compute a value and decide what to do next? | `█░░░░░░░` 1/12 |
| `D04` | [[Map — Objects, Memory & Lifetime\|Objects, Memory & Lifetime]] | Where does an object live, how long does it live, and who can reach it? | `█░░░░░░░` 4/26 |
| `D05` | [[Map — Functions\|Functions]] | How is computation named, parameterised, reused and passed around? | `░░░░░░░░` 1/16 |
| `D06` | [[Map — Classes & Encapsulation\|Classes & Encapsulation]] | How do we build new types that protect their own invariants? | `░░░░░░░░` 1/19 |
| `D07` | [[Map — Ownership & Move Semantics\|Ownership & Move Semantics]] | Who is responsible for releasing a resource, and how does responsibility transfer? | `█░░░░░░░` 2/19 |
| `D08` | [[Map — Inheritance & Polymorphism\|Inheritance & Polymorphism]] | How can one piece of code work with many types chosen at run time? | `█░░░░░░░` 2/15 |
| `D09` | [[Map — Generic Programming\|Generic Programming]] | How can one piece of code work with many types chosen at compile time? | `░░░░░░░░` 1/16 |
| `D10` | [[Map — Standard Library\|Standard Library]] | Which solved problems ship with the language, and how are they composed? | `░░░░░░░░` 1/30 |
| `D11` | [[Map — Errors & Contracts\|Errors & Contracts]] | What happens when an operation cannot do what it promised? | `█░░░░░░░` 1/11 |
| `D12` | [[Map — Concurrency\|Concurrency]] | How do multiple threads of execution share memory without corrupting it? | `░░░░░░░░` 1/17 |
| `D13` | [[Map — Performance & the Machine\|Performance & the Machine]] | What does the hardware actually do with our code, and how do we make it fast? | `█░░░░░░░` 1/15 |
| `D14` | [[Map — Tooling & Engineering\|Tooling & Engineering]] | Which tools turn correct-looking code into verified, maintainable software? | `█░░░░░░░` 1/11 |
| `D15` | [[Map — Design & Idioms\|Design & Idioms]] | Which recurring shapes of solution survive contact with real programs? | `░░░░░░░░` 0/14 |
| `D16` | [[Map — Evolution of C++\|Evolution of C++]] | How did the language get here, and where is it going? | `░░░░░░░░` 0/10 |
| `SRC` | Sources | What should be read, in what order, and for what? | `░░░░░░░░` 0/5 |
| `PRX` | Practice | How does knowledge become skill? | `██░░░░░░` 1/4 |
| `HDR` | [[Map — Standard Headers\|Standard Headers]] | Where does each standard facility live, and what exactly does its header promise? | `██░░░░░░` 17/58 |
<!-- cc:end -->

## Progress

<!-- cc:auto:home-stats -->
| Planned | Draft | Revise | Reviewed | Evergreen | Total | Builder runs | Editor runs |
|---|---|---|---|---|---|---|---|
| 312 | 33 | 0 | 5 | 0 | 350 | 20 | 1 |

`██░░░░░░░░░░░░░░░░░░` **11%** of the Atlas written · last build 2026-09-23
<!-- cc:end -->

**Up next (Builder queue):**
<!-- cc:auto:home-next -->
1. [[Map — Design & Idioms]] · *map* · `D15` — wave 0
2. [[Map — Evolution of C++]] · *map* · `D16` — wave 0
3. [[Guide — cppreference, the Draft Standard and the Core Guidelines]] · *guide* · `SRC` — wave 1
4. [[Guide — C++ Primer (5th ed)]] · *guide* · `SRC` — wave 1
5. [[Guide — A Tour of C++ (3rd ed)]] · *guide* · `SRC` — wave 1
6. [[STL Architecture — Containers, Iterators, Algorithms]] · *concept* · `D10` — wave 1
<!-- cc:end -->

**Recently written:**
<!-- cc:auto:home-recent -->
- ◐ [[Map — Tooling & Engineering]] · *map* · updated 2026-09-23
- ◐ [[Map — Program Structure & Build]] · *map* · updated 2026-09-23
- ◐ [[Map — Errors & Contracts]] · *map* · updated 2026-09-23
- ◐ [[Map — Performance & the Machine]] · *map* · updated 2026-09-23
- ● [[Map — Objects, Memory & Lifetime]] · *map* · updated 2026-09-23
- ◐ [[Map — Concurrency]] · *map* · updated 2026-09-23
- ◐ [[Map — Ownership & Move Semantics]] · *map* · updated 2026-09-23
- ● [[RAII]] · *idiom* · updated 2026-09-23
- ◐ [[Map — What C++ Is]] · *map* · updated 2026-09-23
- ◐ [[Map — Standard Headers]] · *map* · updated 2026-09-23
<!-- cc:end -->

## Start here

| If you want to… | Go to |
|---|---|
| Understand the strategy and the frame | [[Charter]] |
| Learn how notes are structured | [[Framework]] · [[Style Guide]] · [[Visual Language]] |
| See the best examples of each note type | [[Value Categories]] · [[Virtual Dispatch — vptr and vtable]] · [[RAII]] · [[Dangling Pointers and References]] · [[Pointers vs References]] · [[Map — Objects, Memory & Lifetime]] |
| Practise | [[Continuum Bridge]] (the 35 CPP Project Continuum projects ↔ concepts) |
| Read the books well | the `Guide —` notes in `03 Sources` |
| Check status | [[Coverage]] · the `00 System/Dashboards` bases · latest brief in `00 System/Briefs` |
| Steer the agents | edit [[Directives]] (pins, focus, holds): the Builder obeys it every hour |

## How the Compendium grows

An hourly **Builder** writes and verifies one note per run ([[Run Protocol]]). A daily **Editor-in-Chief** audits the work against a rubric, fixes or returns it, reorders the queue and publishes a **Daily Brief** ([[Audit Protocol]]). Every change is a git commit, recorded in the Ledger (`00 System/Ledger`).

> [!rule] You can edit anything, any time
> Your edits always win. Agents never overwrite a note you have uncommitted changes in, and they commit your edits as they are.
