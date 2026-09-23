---
type: system
tags: [system/style]
updated: 2026-09-23
---
# Style Guide: Voice, Reasoning and Code

> [!essence] Write like a senior engineer explaining something to a sharp colleague at a whiteboard. Start from the problem, build the idea step by step from things already known, name every moving part precisely, and stop when the reader can predict the behavior without you.

## 1 · First-principles method

Every non-trivial idea is **derived**, not announced. Use this five-step spine in *The Problem* and wherever a rule appears:

1. **Constraint.** A fact about machines, compilers, programs or people that cannot be wished away. *("Objects on the stack disappear when their scope ends.")*
2. **Consequence.** What goes wrong if we ignore it. *("A pointer to such an object outlives what it points to.")*
3. **Requirement.** What any solution must therefore do. *("Something must tie a resource's release to a moment the compiler can see.")*
4. **Design.** How C++ meets the requirement. *("Destructors run at scope exit, deterministically. So bind the resource to an object.")*
5. **Price.** What the design costs, and which tension it resolves or leaves open. *("Resources must be wrapped; ownership becomes a design question.")*

Put the derivation in a `[!principle]` callout. If you cannot derive a rule, you don't yet understand it well enough to write the note. Research more.

## 2 · Voice

- **Direct, declarative, present tense.** "The compiler generates a vtable per polymorphic class." Not "It could be said that compilers will typically…"
- **Precise vocabulary, defined on first use.** *Object*, *lifetime*, *storage*, *expression*, *value category*, *entity*, *ill-formed*, *UB*: these have exact meanings in C++, so use them exactly. When the Standard's term differs from folk usage ("the stack" vs *automatic storage duration*), give both and say which lens each belongs to.
- **Name the lens.** Say which lens a sentence speaks in: "In the abstract machine, …"; "On x86-64 with GCC, …".
- **Hedge only with evidence.** Distinguish *guaranteed by the Standard*, *implementation-defined*, and *what mainstream compilers do*. Never state an implementation habit as a language rule.
- **Short paragraphs.** Three to five sentences. One idea per paragraph. Bold the key term where it is defined.
- **Analogies are scaffolding, not foundations.** Every analogy is followed by the point where it breaks.
- **No filler.** No "In this note we will…", no "It is important to note that…", no summary that repeats the essence.
- **Second person for the reader** ("you"), plural first person for shared reasoning ("we can now see…").

## 3 · Explaining difficult things

- **Concrete before abstract.** Show a 5-line example, then generalise.
- **Contrast is information.** Explain X by what it is *not* (reference vs pointer, move vs copy).
- **Predict, then reveal.** Pose the question ("what does this print?") before giving the answer. Quizzes do this deliberately.
- **Show the invisible.** Draw what the compiler generates: the implicit `this`, the hidden vptr, the destructor calls at `}`, the temporary.
- **Cost model.** Every feature note says what it costs (time, space, compile time, cognitive load), even when the answer is "nothing".

## 4 · Accuracy discipline

1. **Verify every normative claim** against cppreference or the draft standard (eel.is/c++draft) before writing it. Cite the clause for subtle rules: `[class.copy.elision]`, `[basic.life]`.
2. **Version-label** features: "(C++17)" at first mention, and in the *Evolution* section.
3. **Compile every claim.** "This compiles", "this prints 3", "this is UB": each needs a verified block (see Code rules). `cc.py code` must pass.
4. **When sources disagree**, prefer: the Standard > cppreference > Stroustrup (Tour/PPP) > Primer (it predates C++14) > others, and say so in a `[!standard]` callout.
5. **The Primer is C++11.** Anything it says about later behavior (guaranteed copy elision, `auto` deduction for braces, etc.) must be checked against modern sources.

## 5 · Using the books (copyright)

- Read with `cc.py src find / read`, then **close the book and write in your own words**. Never paste passages, never lightly reword a paragraph, never reproduce a book's example program. Invent your own examples.
- A quotation, if ever needed, is one sentence at most, in a `[!quote]` callout with its citation. Prefer none.
- **Cite precisely:** `Primer §13.6.2 (p. 532)`, `Tour §6.2 (p. 74)`, `PPP §17.4`, `Pikus ch. 4 (p. 98)`. Page = printed page label as `cc.py src` reports it.
- The copy-guard rejects any 12-word run shared with a book.

## 6 · Code rules

- **Self-contained and minimal.** Each ```cpp block compiles alone: includes, `int main()` if it runs. 5–30 lines typical, 40 maximum. Cut everything that doesn't carry the point.
- **Modern by default.** C++20 unless the note is about an older or newer standard. Use `std::` explicitly, no `using namespace std;`. Use `{}` initialization where idiomatic, `auto` where it clarifies, and `const` everywhere it applies.
- **Annotate with circled numerals** `// ①` in code, explained in a numbered list right after the block. That keeps comments short and explanations full.
- **Show output** with `// expect: <text>` lines (checked) or a "prints:" comment when the output is nondeterministic.
- **Directives:** `// cc: ub` for undefined-behavior demos (never claim what they print), `// cc: ill-formed` for code that must *not* compile, `// cc: norun`, `// cc: std=c++23`, `// cc: fragment` (rare: only for declarations that make no sense alone). See `tools/compendium/snippets.py`.
- **Name things meaningfully.** `Buffer`, `Account`, `Sensor`, not `foo` or `A`. Each example should feel like a slice of a real program.
- **Contrast pairs:** when showing wrong vs right, place ✗ and ✓ versions next to each other, each compiled.

## 7 · Quizzes (`Check Yourself`)

```markdown
> [!quiz]- Why can't a reference be reseated?
> Because a reference is not an object: it has no storage of its own that assignment could change. `r = x` assigns *through* `r` to the referent. See [[References]] § Mechanics.
```
Mix three kinds: **recall** (definition), **reasoning** (why/what-if), **prediction** (output / bug / compile error). Answers are 1–4 sentences, and they point back into the note.

## 8 · Words to avoid

"simply", "just", "obviously", "basically", "magic", "under the covers" (say *Under the Hood* and show it), "always/never" without qualification, and "the stack/the heap" when *storage duration* is meant.
