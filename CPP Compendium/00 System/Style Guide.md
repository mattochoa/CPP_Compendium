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
5. **The Primer is C++11.** Anything it says about later behavior (guaranteed copy elision, `auto` deduction for braces, etc.) must be checked against modern sources. It is also loose in places even for C++11 (it calls out-of-range conversion to a signed type "undefined"; the Standard never did).
6. **Say which standard a rule holds for when the rule has moved.** Evaluation order (`i = i++ + 1` is UB only through C++14), out-of-range signed conversion (implementation-defined through C++17, modulo 2^N since C++20), the translation phases (nine through C++23, eight in the C++26 draft), copy elision (permitted vs. mandatory). eel.is tracks the *current working draft* (C++26 content and later), not C++23: when a paragraph number or phase count differs from C++23, give both.
7. **Label tool evidence honestly.** Every asm listing, `nm`/`-E` count or sanitizer result names compiler, version and platform ("GCC 14, x86-64 Linux, Compiler Explorer"). "This vault's toolchain" means whatever compiler `cc.py preflight` reports as TOOLCHAIN for that run (it changes: 09-27 → 10-01 runs reported GCC 11.4 on x86-64 Ubuntu 22.04 with ASan/UBSan; from 10-02 preflight reports MinGW-w64 GCC 16.1 on Windows, which is LLP64 and links only trap-mode UBSan). So never write "this vault's toolchain" alone: always name compiler, version and platform, so the label stays true after the next change. **Code that runs must not assume LP64**: `long` is 32 bits on Windows, so any value that can exceed 2³¹ uses `long long` or a `<cstdint>` type (two examples broke on 10-02 for this reason). Say *observed* only for what `cc.py` or Compiler Explorer actually produced; everything else is reported behavior ("on Linux/macOS, ASan reports…"). Never claim a tool catches a bug class its documentation doesn't cover: UBSan does not check strict aliasing, and ASan cannot see an overrun that stays inside an object's own SSO buffer.
8. **Label implementation-specific layouts.** `sizeof`, member offsets, SSO capacity and mode bits, vtable layout: name the ABI or library (LP64 vs. LLP64; libstdc++ vs. libc++ vs. MSVC STL; Itanium vs. MSVC ABI). A diagram that assumes `long` is 8 bytes is wrong on 64-bit Windows.

## 5 · Using the books (copyright)

- Read with `cc.py src find / read`, then **close the book and write in your own words**. Never paste passages, never lightly reword a paragraph, never reproduce a book's example program. Invent your own examples.
- A quotation, if ever needed, is one sentence at most, in a `[!quote]` callout with its citation. Prefer none.
- **Cite precisely:** `Primer §13.6.1 (p. 532)`, `Tour §6.2 (p. 74)`, `PPP §17.4` (the PPP edition has no printed page labels: cite the section), `Pikus ch. 4 (p. 113)`. Page = printed page label as `cc.py src` reports it. Cite the page where the point is made, not only where the section starts (e.g. `Primer §12.1.2 (p. 463)`).
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

## Protocol changelog
- 2026-09-23 (Editor #1): §5 citation examples corrected (§13.6.2 starts on p. 534, not 532; Pikus ch. 4 starts on p. 113); PPP section-only citation made explicit; "cite the page where the point is made" added.
- 2026-09-27 (Editor #2): §4 rules 6–8 added (version span for rules that moved between standards; honest tool-evidence labelling; ABI/library labels for layouts), after the same defect classes appeared in 11 of 20 audited notes. §4.5 notes the Primer's signed-conversion error.
- 2026-10-02 (Editor #3): §4.7 "this vault's toolchain" redefined as the TOOLCHAIN line preflight reports. The 09-27 wording (MinGW only) did not match where the Builder actually compiles (GCC 11.4 on Linux, sanitizers available), so labels like "this vault's toolchain (GCC 11.4, x86-64 Linux, ASan+UBSan)" are correct, not defects.
- 2026-10-02 (Editor #4): 4.7 updated for the switch to MinGW-w64 GCC 16.1 (Windows, LLP64); added the no-LP64-assumption rule after `long` overflow broke runnable examples in The Call Stack and Stack Frames and Performance — Measure, Don't Guess.
