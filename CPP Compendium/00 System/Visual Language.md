---
type: system
tags: [system/visual]
updated: 2026-09-23
---
# Visual Language: Graphic Design System

> [!essence] Every visual element carries meaning. Colour signals *kind*, shape signals *structure*, position signals *order*. A reader who has learned the system can scan any note and know what each block is before reading a word of it.

The system is implemented by the CSS snippet `.obsidian/snippets/compendium.css` (enable it in *Settings → Appearance → CSS snippets*), Mermaid class definitions, and box-drawing conventions.

## 1 · Principles

1. **Signal, not decoration.** A diagram earns its place when it shows *structure* (graph, layout, sequence) that prose would have to describe sequentially. No clip-art, no emoji.
2. **One visual per idea.** Each diagram answers one question, stated in the sentence just before it.
3. **Consistent encoding.** The same colour means the same thing in every note (§2). The same shape means the same thing in every diagram (§4).
4. **Progressive disclosure.** Essence first, model second, detail after. Quiz answers are folded. Long tables sit below the prose that motivates them.
5. **Legible in both themes.** Mermaid nodes use the dark fills with light text defined below; they read on light and dark backgrounds alike.
6. **Small multiples beat one giant diagram.** Two focused diagrams are better than one with twenty nodes. Limit: about 12 nodes per diagram.

## 2 · Semantic callouts (colour = kind)

| Callout | Colour | Meaning | Use |
|---|---|---|---|
| `> [!essence]` | indigo | The irreducible idea | Exactly one, at the top of every note |
| `> [!principle]` | teal | First-principles derivation | *The Problem*; wherever a rule is derived |
| `> [!model]` | violet | The mental model / analogy (+ where it breaks) | *Mental Model* |
| `> [!machine]` | slate | Real-machine detail: layout, asm, cost | *Under the Hood* |
| `> [!standard]` | sky | What the Standard says (paraphrased + clause) / version notes | *Mechanics*, *Evolution* |
| `> [!rule]` | green | A rule of thumb or guideline to follow | *Prevention Rules*, idioms |
| `> [!trap]` | orange | A pitfall: legal code that misleads | *Pitfalls* |
| `> [!ub]` | red | Undefined behavior | Wherever UB is possible |
| `> [!tension]` | pink | One of the Five Tensions at work | *The Problem*, maps |
| `> [!quiz]-` | amber | Self-test (always folded with `-`) | *Check Yourself* |
| `> [!history]` | grey-blue | Historical context | *Evolution* |
| `> [!source]` | bronze | Reading pointer into a book | *Sources*, guides |

Built-in `[!info]`, `[!example]`, `[!quote]` remain available for system pages.

> [!essence]
> Rendered example of the essence callout.

> [!ub] Rendered example
> Reading an object after its lifetime has ended is undefined behavior.

## 3 · Colour roles in Mermaid

Paste the class definitions you use at the end of every Mermaid block:

```text
classDef concept fill:#312e81,stroke:#818cf8,color:#eef2ff   %% an idea / abstraction (indigo)
classDef mech    fill:#134e4a,stroke:#2dd4bf,color:#f0fdfa   %% a mechanism / machine step (teal)
classDef focus   fill:#78350f,stroke:#fbbf24,color:#fffbeb   %% the subject of this note (amber)
classDef good    fill:#14532d,stroke:#4ade80,color:#f0fdf4   %% correct / safe / recommended (green)
classDef danger  fill:#7f1d1d,stroke:#f87171,color:#fef2f2   %% wrong / UB / hazard (red)
classDef muted   fill:#1e293b,stroke:#64748b,color:#e2e8f0   %% context / neighbouring idea (slate)
```

- The **note's own subject** is always `focus` (amber). There should be exactly one focal node or group.
- Mermaid `%%` comments are allowed but keep blocks clean. Use `<br/>` for line breaks and `<b>`, `<i>` for emphasis inside labels.
- Put quotes around labels that contain punctuation or parentheses: `A["f(x) returns T&&"]`.
- Write `<` and `>` inside labels as Mermaid entity codes `#lt;` and `#gt;` (e.g. `"std::optional#lt;T#gt;"`). Raw angle brackets are parsed as HTML and vanish.

## 4 · Diagram grammar (shape = structure)

| Question the diagram answers | Form | Mermaid type |
|---|---|---|
| How do ideas depend on each other? | Concept graph, arrows = "is needed for" | `flowchart LR` |
| What happens in what order between actors? | Sequence | `sequenceDiagram` |
| What states can this be in? | State machine | `stateDiagram-v2` |
| How are types related? | Class diagram | `classDiagram` |
| Which option should I pick? | Decision tree: diamonds for questions, rounded boxes for answers | `flowchart TD` |
| What is the taxonomy? | Tree | `flowchart TB` |
| What's where in memory? | **Box diagram** (below) | ```text |
| What did the compiler emit? | Annotated assembly | ```nasm / ```text |

**Node shapes in flowcharts:** `[rectangle]` = entity or concept · `(rounded)` = action or step · `{diamond}` = decision · `[(cylinder)]` = storage · `[[subroutine]]` = mechanism owned by the compiler or runtime.

## 5 · Box diagrams (memory and layout)

Use ```text blocks with box-drawing characters. Conventions:

```text
  STACK (automatic)                     HEAP (dynamic)
  addresses decrease ↓                  
 ┌────────────────────────┐            ┌──────────────────────┐
 │ main()                 │            │ int[4]  0x5591…a0    │
 │  ┌──────────────────┐  │     ┌─────▶│ [ 1 | 2 | 3 | 4 ]    │
 │  │ v : vector<int>  │  │     │      └──────────────────────┘
 │  │  data ●──────────┼──┼─────┘
 │  │  size = 4        │  │
 │  │  cap  = 4        │  │
 │  └──────────────────┘  │
 └────────────────────────┘
```

- `●──▶` is a pointer (owning or observing: say which in the caption). `╌╌▶` is a dangling or invalid pointer.
- Give **addresses** (abridged) only when they matter. Give **sizes** in bytes on the right edge when layout is the point.
- Label regions with their storage duration and the folk name: *STACK (automatic)*, *HEAP (dynamic)*, *STATIC (static storage)*.
- Maximum width: 78 characters, so diagrams don't wrap on narrow panes.

## 6 · Tables

- **Matrices** (comparisons): criteria as rows, contenders as columns. Cells start with a glyph: `✓` good, `✗` bad, `~` depends, followed by 2–6 words.
- **Rule tables** (mechanics): *Situation → Rule → Example*.
- **Timeline tables** (evolution): *Standard → Change → Why*.
- Keep tables ≤ 7 columns. Bold the header concept in the first column.

## 7 · Code presentation

- Circled-numeral annotations `// ①` explained in a list after the block (see [[Style Guide]] §6).
- Show ✗ and ✓ versions in consecutive blocks, preceded by a one-line caption in bold: **✗ Dangling:** / **✓ Owning:**.
- Assembly excerpts: ≤ 20 lines, taken from `cc.py asm`, compiler and flags stated in the caption (e.g. *GCC 14.2, -O2*).

## 8 · Page rhythm

A well-formed note scans as: essence (indigo) → problem with principle (teal) → one model diagram → rule table → machine box diagram → annotated code → traps (orange/red) → evolution table → connections list → folded quizzes (amber) → sources (bronze). About one visual element per 250 words of prose.

## 9 · Canvas

`01 Maps/Atlas.canvas` is generated by `cc.py build`: one group per domain (domain colour), cards arranged left→right by tier, card colour = status (none planned · yellow draft · green reviewed · purple evergreen · red revise). Hand-drawn canvases for a deep dive are welcome in `01 Maps/`, named `Canvas — <topic>`.
