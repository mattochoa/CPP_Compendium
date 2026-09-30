---
id: override-and-final
title: override and final
aliases:
- override specifier
- final specifier
type: concept
domain: D08
tier: 1
status: draft
standard: C++11
prereqs:
- "[[Virtual Functions]]"
related:
- "[[Virtual Dispatch — vptr and vtable]]"
- "[[Name Hiding in Derived Classes]]"
- "[[Abstract Classes and Interfaces]]"
- "[[Virtual Destructors]]"
practice:
- 18
tags:
- type/concept
- domain/d08
- tier/1
- tension/compatibility-vs-evolution
- std/c++11
created: 2026-09-30
updated: 2026-09-30
---

# override and final

> [!essence]
> `override` and `final` are C++11 declarations you attach to a member function (or, for `final`, to a class) so the *compiler* checks a claim you're making instead of trusting you: `override` claims "this matches a base class's virtual function," `final` claims "nothing further down may match this again." Neither changes what runs; each only narrows what the compiler will accept.

## The Problem

[[Virtual Functions]] established that a derived override must match its base's declaration exactly — same name, same parameter types, same cv- and ref-qualification. It also showed the trap that falls out of that rule: a declaration that is close but not exact does not fail to compile. It quietly becomes a second, unrelated function, and code calling through a base pointer or reference never sees it.

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint.** "Overrides" is a purely structural test the compiler already performs silently, and `virtual` need not even be repeated on the derived declaration for it to apply (`[class.virtual]` ¶1). The same syntax — an ordinary member function declaration — covers both a genuine override and an unrelated same-named function.
> 2. **Consequence.** A single wrong parameter type, a missing `const`, or an extra argument produces code that compiles cleanly and runs, but silently drops the intended override. Before C++11 there was also no way to say "no class below this one may reopen this name": the only tool for sealing a class against derivation was to deny it an accessible constructor, which also blocks legitimate use as a value type.
> 3. **Requirement.** At the exact point of declaration, the language needs a way to make two intentions checkable rather than assumed: *this must be an override of something that already exists*, and *this is the end of the line — nothing past here may override it, or derive from it at all*.
> 4. **Design.** C++11 adds two identifiers with special meaning, written after a member function's parameter list: `override`, which the compiler rejects unless the declaration actually overrides a base virtual (`[class.virtual]` ¶5), and `final`, which the compiler rejects if any later class tries to override it (¶4) — or, written after a class name, if any later class tries to derive from it at all.
> 5. **Price.** Two more words to place correctly, and a asymmetry between them that is easy to miss: `override` verifies a claim about the *past* (a matching declaration already exists), while `final` verifies a much weaker claim about the *present* (this declaration is virtual) and says nothing about whether it overrides anything at all.

> [!tension] compatibility ⟷ evolution
> Both words had to be added to a language whose users had spent two decades free to name variables and functions `override` or `final`. Making them reserved keywords would have silently broken that code. C++11 instead made them *identifiers with special meaning*: significant only in the one syntactic slot after a member function's declarator or after a class name, ordinary identifiers everywhere else. The language gained a checked vocabulary without retiring a single existing program.

## Mental Model

The two specifiers check in opposite directions along the same timeline: `override`, attached to a declaration, looks backward to see whether a match already exists above it; `final`, attached to a declaration, looks forward to forbid a match ever appearing below it.

```text
 override — checked HERE, looking BACKWARD
 ┌──────────┐   "does a matching virtual         ┌──────────┐
 │  Base    │    already exist above me?"        │ Derived  │
 │ virtual  │ ◀──────────────────────────────────│  f()     │
 │  f()     │                                     │ override │
 └──────────┘                                     └──────────┘

 final — checked HERE, forbidding FORWARD
 ┌──────────┐    "let nothing below me            ┌──────────┐
 │ Derived  │     ever match this again"          │ Further  │
 │  f()     │ ────────────────────────────X──────▶│  f()     │
 │  final   │                                      │ (error)  │
 └──────────┘                                      └──────────┘
```

> [!model] A signed receipt vs. a padlock
> `override` is a receipt the compiler cross-checks against an original: it refuses to stamp it unless a matching virtual declaration already exists to check it against. `final` is a padlock: it doesn't ask how the door was opened, only that nothing may open it again. A padlock can be hung on a door that was never opened by anyone before it — a brand-new virtual function can be `final` the moment it is introduced, with nothing behind it to override.
> **Where it breaks:** a padlock only guarantees the door stays *shut*; it says nothing about whether the door you locked was the right one. `final` never checks that the function it seals actually overrides anything — that check belongs to `override` alone, as the next section shows.

## Mechanics

| Situation | Rule | Example |
|---|---|---|
| `override` on a member function | Ill-formed unless the declaration overrides a virtual function of a base class — exact name, parameters, cv- and ref-qualification (`[class.virtual]` ¶5) | `void f(int) override;` errors if no base declares a matching `f` |
| `final` on a member function | Requires only that the function *be virtual* — by an explicit `virtual` or by matching a base virtual. Does **not** require it to override anything (`[class.virtual]` ¶4; cppreference, *final specifier*) | `virtual void g() final;` compiles even with no base at all |
| `final` on a class name | Forbids the class from appearing in any later derivation list; ill-formed to derive from it at all | `struct Sealed final { };` — see In Code, example 4 |
| `override final` / `final override` | Both orders are accepted on one declaration. Not redundant: `override` checks that a match exists *here*; `final` then forbids a match *below* — two different claims at once | see Check Yourself, Primer Exercise 15.12 |
| Repeating `virtual` on an override | Legal but adds nothing: the Standard's own footnote calls it "valid but redundant (has empty semantics)" (`[class.virtual]` ¶1, footnote 85) | prefer `void f() override;` over `virtual void f() override;` |
| Used outside a member-function declarator or class head | Both words are ordinary identifiers — never reserved | `int final = 3;` compiles; see In Code, example 4 |

> [!standard] `final` checks virtuality, not overriding
> cppreference states the rule plainly: "`final` specifier ensures that the function is virtual and specifies that it may not be overridden by derived classes." Nothing in that sentence, nor in `[class.virtual]` ¶4, requires the sealed function to *override* anything — only that it be virtual. A signature that is virtual only because it was explicitly declared `virtual`, and that happens not to match any base declaration, satisfies `final` completely while overriding nothing at all. `override`'s check, by contrast, is defined entirely in terms of a prior match (¶5): it cannot be satisfied by a fresh virtual function with no base counterpart.

## Under the Hood

> [!machine] `override` leaves no trace in the compiled code (GCC 11.4.0, x86-64 Linux, `-O2`, observed)
> Compiling the same class twice — once with `override` on `Circle::area`, once with the word deleted and nothing else changed — and comparing the generated assembly line by line produces **zero differences** beyond the embedded source filename:
> ```text
> $ g++ -std=c++20 -O2 -S with_override.cpp  -o a.s
> $ g++ -std=c++20 -O2 -S without_override.cpp -o b.s
> $ diff a.s b.s
> 1c1
> < 	.file	"with_override.cpp"
> ---
> > 	.file	"without_override.cpp"
> ```
> `override` is checked once, during semantic analysis, and generates no instructions, no vtable slots, and no run-time flag. It either passes and vanishes, or the build fails.

`final` on a *function* is equally invisible in that function's own vtable slot — it occupies the same slot a plain override would. Its machine-level effect shows up only in *callers* that hold a reference or pointer whose type is known to be sealed: because the compiler can prove no further override exists, it may resolve such a call directly and even inline it, skipping the vptr load entirely. That devirtualization mechanism — and the exact GCC assembly for a `final`-enabled call versus an ordinary one — belongs to [[Virtual Dispatch — vptr and vtable]], which develops it in full; this note only establishes the compile-time promise that licenses it. What `final` does *not* do is change the sealed class's own layout: `sizeof` and the vtable contents of a class are identical whether or not `final` is attached, verified here with a compiled `static_assert` comparing a sealed and an unsealed version of the same class — `final` adds a constraint the compiler enforces, not a bit anywhere in memory.

## In Code

**1 · Without either specifier, a signature mismatch silently drops the override**

```cpp
#include <iostream>

struct Account {
    virtual void apply_interest(double rate) { balance *= (1.0 + rate); }
    double balance = 100.0;
};

struct Savings : Account {
    // intended to override, but the parameter type doesn't match
    void apply_interest(int rate) { balance *= (1.0 + 2 * rate); }   // ①
};

void credit_interest(Account& a) { a.apply_interest(1); }             // ②

int main() {
    Savings s;
    credit_interest(s);
    std::cout << s.balance << '\n';                                  // ③
}
// expect: 200
```
1. `Savings::apply_interest(int)` doesn't match `Account::apply_interest(double)`, so it is not virtual at all — a second, unrelated function ([class.virtual] ¶1).
2. Called through `Account&`, only `Account`'s member is visible; the `int` argument converts to `double`, and dispatch — with nothing in `Savings`'s vtable slot but `Account`'s own function — runs `Account`'s formula.
3. Prints `200`, not the `300` the bonus formula would give: the override never fired. Neither specifier is written here, so nothing warns about it.

**2 · `final`'s blind spot: it doesn't check overriding, only virtuality**

```cpp
struct Sensor {
    virtual void calibrate(double offset) const;
};

struct Thermometer : Sensor {
    // ① compiles cleanly: this IS virtual (explicitly), so 'final' is satisfied —
    //   even though it does not override Sensor::calibrate(double) at all.
    virtual void calibrate(int offset) const final;
};

int main() {}
```
1. `final` asks only "is this function virtual?" It is, because the derived declaration says `virtual` outright. Whether it overrides anything is a separate question `final` never asks — GCC accepts this with no warning even at `-Wall -Wextra`.

**3 · `override` catches the identical mistake**

```cpp
// cc: ill-formed
struct Sensor {
    virtual void calibrate(double offset) const;
};

struct Thermometer : Sensor {
    void calibrate(int offset) const override;   // ①
};

int main() {}
```
1. Same signature mismatch as example 2, but `override` checks the thing `final` doesn't: whether a matching base virtual exists. GCC 11.4.0 rejects it — *"`void Thermometer::calibrate(int) const` marked `override`, but does not override"* — because `override`'s rule (`[class.virtual]` ¶5) is defined entirely by that backward-looking match.

**4 · `final` on a class, and both words as ordinary identifiers elsewhere**

```cpp
#include <iostream>

struct Sealed final {              // ① no class may name Sealed in a base-specifier-list
    int value = 0;
};

int main() {
    int final = 42;                // ② 'final' is not reserved outside its one syntactic slot
    int override = 7;              // ③ neither is 'override'
    std::cout << final + override + Sealed{}.value << '\n';
}
// expect: 49
```
1. `struct Bad : Sealed { };` written after this fails to compile — *"cannot derive from 'final' base 'Sealed'"* — the class-level counterpart of example 3's rejection, checked at the point of derivation rather than of overriding.
2. Outside a member-function declarator or a class head, `final` is just a name. Declaring a local variable called `final` compiles without incident.
3. Same for `override`: cppreference's own reference example even declares a member function literally named `override()`. Neither identifier was ever made a reserved keyword — see The Problem's compatibility tension.

## Pitfalls

> [!trap] `final` does not substitute for `override`
> Because `final` only requires virtuality, writing `final` alone on a function you *intend* to override buys none of the safety `override` provides against a signature typo (example 2). If the function is meant to override *and* to close the chain, write both: `void f() override final;`. `override` alone, or `override final` together, catches a mismatch; `final` alone does not.

> [!trap] A signature mismatch with neither specifier is silent, not just unchecked
> Example 1 doesn't fail to compile, warn, or behave obviously wrong at the call site that triggers it — it runs, and returns a plausible-looking number. This is the specific failure `override` exists to convert into a compile error; the general shape of the trap — a derived declaration that merely *hides* rather than overrides — is developed fully in [[Name Hiding in Derived Classes]].

> [!rule] Seal a class with `final` for a reason you can state, not by default
> The C++ Core Guidelines' C.139 counsels using `final` on classes sparingly: it freezes a hierarchy against extension a later maintainer may have had a legitimate reason to make, and an unsubstantiated performance justification is exactly what this note's *Under the Hood* section warns against manufacturing — the devirtualization gain is real (verified in [[Virtual Dispatch — vptr and vtable]]) but applies only to calls the compiler can already see through a reference or pointer of the sealed type, not to every call in the program.

## Evolution

| Standard | Change | Why |
|---|---|---|
| **C++11** | `override` and `final` introduced as identifiers with special meaning, not reserved keywords (N2928, N3206) | Catch a signature mismatch at compile time without breaking any program already using these words as ordinary names |
| C++11 (DR) | CWG 1318 clarified that in `class X final { };` (an empty member list), `final` is *always* parsed as the class-virt-specifier, never as a variable declaration | Removed a genuine parsing ambiguity in the original wording, applied retroactively |

## Connections

- **Prerequisites:** [[Virtual Functions]] — the exact-match rule these specifiers check, and the near-miss trap they exist to convert into a compile error.
- **Enables:** [[Virtual Dispatch — vptr and vtable]] (the devirtualization a `final` class licenses, developed with real GCC assembly) · [[Name Hiding in Derived Classes]] (what a signature mismatch actually produces when neither specifier catches it) · [[Abstract Classes and Interfaces]] (a pure virtual function can itself be marked `override` or `final` at the point it is refined).
- **Siblings:** [[Virtual Destructors]] — `override` applies to destructors exactly as to ordinary virtuals, and is the cheapest way to confirm a destructor is virtual at all.
- **Domain:** [[Map — Inheritance & Polymorphism]].
- **Practice:** *Continuum #18 Shape Hierarchy & Polymorphic Area Calculator*: mark every intended override with `override` and deliberately introduce one signature typo to watch the compiler catch it.

## Check Yourself

> [!quiz]- What does `override` verify that `final` does not?
> `override` verifies that the declaration actually overrides a virtual function already declared in a base class — an exact match of name, parameters, and cv-/ref-qualification. `final` only verifies that the function is virtual; it says nothing about whether it overrides anything, so it can be attached to a brand-new virtual function with no base counterpart at all.

> [!quiz]- Why can `final` be legally attached to a virtual function that is being introduced for the first time, with no base class involved?
> Because `final`'s only requirement is virtuality, not overriding (`[class.virtual]` ¶4). A class can declare `virtual void f() final;` from scratch, meaning "this function is virtual, and no derived class may ever override it" — a real, if unusual, design: a hook meant to exist for uniformity but never specialized further.

> [!quiz]- Predict: does `struct D : B { virtual void f(int) const final; };` compile if `B` declares only `virtual void f(double) const;`? Does `D::f` override `B::f`?
> Yes, it compiles — `final` only requires virtuality, which the explicit `virtual` supplies. No, it does not override `B::f`: the parameter types differ, so by `[class.virtual]` ¶2 this is an unrelated function that happens to share a name, now sealed against further overriding despite never having overridden anything.

> [!quiz]- Primer's Exercise 15.12 asks whether it is ever useful to declare a function both `override` and `final`. What's the answer?
> Yes. The two specifiers check different things: `override` confirms this declaration matches a virtual function above it; `final` forbids any declaration below it from matching this one. Writing `void f() override final;` states both at once — "this genuinely overrides, and the chain stops here" — which neither word alone can say.

## Sources

- Primer §15.2.2 "Preventing Inheritance by Defining a Class as `final`" (p. 600): the class-level specifier, `NoDerived`/`Last` examples, and the resulting compile errors.
- Primer §15.3 "The `final` and `override` Specifiers" (pp. 606–607) and Exercise 15.12 (p. 608): the function-level specifiers, the `D1`/`D2`/`D3` worked examples this note's `Sensor`/`Thermometer` examples are modeled on, and the override-plus-final question.
- Tour §5.3 "Abstract Types" (p. 61) and §5.5 "Class Hierarchies" (p. 64): `override` used idiomatically in a from-scratch hierarchy, from the language's designer.
- Pikus ch. 10 "Compiler Optimizations in C++", § Function inlining (p. 357): the devirtualization concept this note's *Under the Hood* section points onward to.
- cppreference, *`override` specifier*: https://en.cppreference.com/w/cpp/language/override
- cppreference, *`final` specifier*: https://en.cppreference.com/w/cpp/language/final
- Draft standard `[class.virtual]` ¶1 (footnote 85, redundant `virtual`), ¶2 (the matching rule), ¶4 (`final`), ¶5 (`override`): https://eel.is/c++draft/class.virtual
- CWG Issue 1318, *`final` parsing ambiguity*: https://cplusplus.github.io/CWG/issues/1318.html
- C++ Core Guidelines C.128 (specify exactly one of `virtual`, `override`, `final`) and C.139 (use `final` on classes sparingly): https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
