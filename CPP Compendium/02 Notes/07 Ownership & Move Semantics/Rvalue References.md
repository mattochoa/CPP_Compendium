---
id: rvalue-references
title: Rvalue References
aliases:
- rvalue reference
type: concept
domain: D07
tier: 2
status: draft
standard: C++11
prereqs:
- "[[Value Categories]]"
related:
- "[[Move Semantics]]"
- "[[Copy Semantics — Deep vs Shallow Copy]]"
- "[[Forwarding References and Reference Collapsing]]"
- "[[move and forward — Casts, Not Actions]]"
practice:
- 22
tags:
- type/concept
- domain/d07
- tier/2
- tension/value-vs-identity
- tension/safety-vs-performance
- std/c++11
created: 2026-09-29
updated: 2026-09-29
---

# Rvalue References

> [!essence]
> An **rvalue reference**, written `T&&`, is a reference type that binds only to rvalues: expressions the compiler can prove have no other user. Binding one is not an action but a **permission** — it lets the bound function steal the referred-to object's resources instead of copying them — and that permission is the entire mechanism overload resolution uses to route a call toward a cheap move instead of a safe copy.

## The Problem

[[Value Categories]] classifies every expression as movable or not, but a classification inside the compiler's type checker changes nothing on its own. A function's parameter list is the only place a program can *act* on that classification, and before C++11 it had exactly one reference type to declare a parameter with: `T&` (or its `const` form).

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint.** A plain reference, `T&`, binds only to lvalues; `const T&` binds to anything but forbids mutation through it ([[References]]). Neither can express "bind to a temporary, and let me modify it."
> 2. **Consequence.** A function that wanted to accept a temporary *and* mutate it — most importantly, steal its heap buffer instead of copying it — had no reference type to declare. The only option was to take the parameter by value, which itself performs a copy (or, later, a move it couldn't yet express) to get the argument into the parameter slot. Resource-owning classes paid a full deep copy every time a temporary was involved, even though the temporary was seconds from destruction anyway.
> 3. **Requirement.** The language needs a second reference type: one that binds only to expressions with no other user, and that permits mutation through it, so the bound function may safely reach in and take what it needs.
> 4. **Design.** C++11 adds `T&&`, declared with `&&` instead of `&`. It is a distinct type from `T&` ([dcl.ref] ¶2), it binds to rvalues (prvalues and xvalues) but is ill-formed on a plain lvalue, and — unlike `const T&` — it is not `const`. Overload resolution then does the rest for free: given both a `const T&` and a `T&&` overload, an rvalue argument prefers `T&&` ([[Value Categories]] §Mechanics). A move constructor or `push_back(T&&)` overload is simply a function that declares "if you give me something disposable, I will not copy it."
> 5. **Price.** A second reference type to learn, with a binding rule that has one sharp corner: a *named* rvalue reference is itself an lvalue inside the function that named it (see Pitfalls). Propagating the permission onward therefore needs `std::move` again, by hand, every single time — and inside a template, `T&&` stops meaning "rvalue reference" altogether and becomes a *forwarding reference* with its own rule ([[Forwarding References and Reference Collapsing]]).

> [!tension] value ⟷ identity
> `T&` and `const T&` see an object only as an **identity** you must not damage. `T&&` is the language's way of saying: *this specific expression is a value with no identity worth preserving — treat the object behind it as disposable.* The type of the reference, chosen at the call site, decides which lens applies.

> [!tension] safety ⟷ performance
> A deep copy is always safe. Stealing a resource is only safe when nobody else can observe the theft. `T&&` is how the compiler enforces that precondition statically and for free: if an expression cannot bind to `T&&`, the language has already proven the steal is unsafe. This is the [[Map — What C++ Is|zero-overhead principle]] applied to a single bit of information — "is anyone else still using this?" — costed entirely at compile time.

## Mental Model

```text
   WHERE THE EXPRESSION CAME FROM                    WHAT IT BINDS
  ┌────────────────────────────────┐
  │ a temporary:  make_widget()    │
  │ a cast:       std::move(a)     │── claim slip ──▶   T&&   "yours to steal"
  │                       (rvalue) │
  └────────────────────────────────┘
  ┌────────────────────────────────┐
  │ a name:  a, w, *p, arr[i]      │── plain alias ─▶   T&    "look, don't take"
  │                       (lvalue) │
  └────────────────────────────────┘
```

> [!model] The claim slip, and where it breaks
> An rvalue reference is a **claim slip**: whoever holds it may take the contents of the box it is taped to, because no one else has a claim. Tape the slip to a *named* box — `T&& w = ...` — and something changes: the box now has a name, `w`. **A named box is never treated as unclaimed automatically.** Inside the function, the expression `w` is a name, hence an lvalue, and passing it onward binds `T&`, not `T&&` — the slip does not travel with the name. To send it on, you must tape a fresh slip yourself: `std::move(w)`.

## Mechanics

| Situation | Rule | Example |
|---|---|---|
| Declaring `T&&` | A distinct reference type from `T&`, called an rvalue reference ([dcl.ref] ¶2) | `int&& rr = 42;` |
| Binding to a prvalue or xvalue | Direct-binds; the object has no other user for the duration of the binding | `int&& rr = x + 1;` (prvalue) |
| Binding to a plain lvalue | Ill-formed — there is no implicit lvalue-to-rvalue-reference conversion | `int&& rr = x;` — error |
| A named rvalue-reference **parameter or variable**, used in an expression | Is itself an lvalue: it has a name, hence identity | `void f(Widget&& w) { g(w); }` calls `g(Widget&)` |
| Overload set with `T&`, `const T&`, `T&&` | An rvalue argument prefers `T&&` over `const T&` (`[over.ics.rank]`) | see *In Code*, Example 2 |
| `T&&` where `T` is a template parameter deduced from the call | A **forwarding reference**, not a plain rvalue reference — binds to *anything* | `template<class T> void f(T&& x)` |

> [!standard] Reference collapsing (`[dcl.ref]` ¶7)
> A bare rvalue reference is not itself a template feature, but references produced *through* a template or `typedef` obey a collapsing rule: `T& &`, `T& &&`, and `T&& &` all collapse to `T&`; only `T&& &&` collapses to `T&&`. Combined with template argument deduction, this single rule is what makes forwarding references and `std::forward` well-defined — see [[Forwarding References and Reference Collapsing]]. The feature as a whole (`T&&`, move construction, `std::move`) is tracked by the feature-test macro `__cpp_rvalue_references` (`200610L`, C++11).

**Overload resolution routes on the argument's category, not on any property of the type:**

```mermaid
flowchart LR
    ARG["call-site argument"]:::muted --> Q{"lvalue or rvalue?"}
    Q -->|lvalue: a name| TR["T&<br/>(or const T&)"]:::concept
    Q -->|rvalue: temporary or<br/>std::move(x)| BOTH{"both T&& and<br/>const T& viable?"}
    BOTH -->|yes| FOCUS["T&& wins<br/>(better match)"]:::focus
    BOTH -->|only const T& exists| FALL["const T& used<br/>(falls back to copy)"]:::concept
    classDef concept fill:#312e81,stroke:#818cf8,color:#eef2ff
    classDef focus fill:#78350f,stroke:#fbbf24,color:#fffbeb
    classDef muted fill:#1e293b,stroke:#64748b,color:#e2e8f0
```

## Under the Hood

> [!machine] A reference costs nothing at run time — both kinds cost the *same* nothing
> Neither `T&` nor `T&&` exists as a distinct run-time entity: a reference is not an object with its own representation, and both compile to a plain address passed in a register. Two functions differing only in reference kind, GCC 11.4.0, x86-64 Linux, `-O2`:
> ```nasm
> by_lvalue_ref(Widget&):
>         mov DWORD PTR [rdi], 1
>         ret
> by_rvalue_ref(Widget&&):
>         mov DWORD PTR [rdi], 1
>         ret
> ```
> Identical instructions. `T&&` versus `T&` is a fact the *compiler's overload resolution* uses; nothing in the generated code records which one got you here. The cost of "moving" is never in the reference — it is in whatever the function body chooses to do once it holds one, which is why a move constructor is only as cheap as its own steal-the-pointer logic ([[Move Semantics]]).

## In Code

**1 · The one thing `T&&` refuses**

```cpp
// cc: ill-formed
#include <string>

int main() {
    std::string s = "value";
    std::string&& rr = s;   // ① error: cannot bind an rvalue reference to an lvalue
    (void)rr;
}
```
1. `s` is a name, so the expression `s` is an lvalue ([[Value Categories]]). `T&&` binds only rvalues. The fix is `std::string&& rr = std::move(s);`, which casts `s` to an xvalue first — it does not move anything by itself, it only grants permission.

**2 · The same object, two expressions, two constructors**

```cpp
#include <iostream>
#include <utility>

class Buffer {
public:
    explicit Buffer(int n) : data_(new int[n]{}), size_(n) {}
    Buffer(const Buffer& other)                                    // ①
        : data_(new int[other.size_]), size_(other.size_) {
        std::cout << "copy: allocates " << size_ << " ints\n";
        for (int i = 0; i < size_; ++i) data_[i] = other.data_[i];
    }
    Buffer(Buffer&& other) noexcept                                // ②
        : data_(other.data_), size_(other.size_) {
        std::cout << "move: steals the pointer, allocates nothing\n";
        other.data_ = nullptr;                                     // ③
        other.size_ = 0;
    }
    ~Buffer() { delete[] data_; }
private:
    int* data_;
    int size_;
};

int main() {
    Buffer a(1000);
    Buffer b = a;              // ④ a is an lvalue -> binds Buffer(const Buffer&)
    Buffer c = std::move(a);   // ⑤ std::move(a) is an xvalue -> binds Buffer(Buffer&&)
}
// expect: copy: allocates 1000 ints
// expect: move: steals the pointer, allocates nothing
```
1. Takes `const Buffer&`: binds any `Buffer`, but cannot mutate it, so it must copy.
2. Takes `Buffer&&`: binds only a disposable `Buffer`, and being non-`const`, may mutate — here, steal — it.
3. Leaving `other` in a valid, destructible, empty state is the move constructor's half of the bargain ([[The Moved-From State]]).
4. `a` is a name: an lvalue. Only `Buffer(const Buffer&)` matches.
5. `std::move(a)` is a cast to `Buffer&&`: an xvalue. `Buffer(Buffer&&)` is preferred over `Buffer(const Buffer&)` whenever both could bind.

**3 · Declaring `T&&` does not make the body move anything**

```cpp
#include <iostream>
#include <string>
#include <utility>

class Tag {
public:
    explicit Tag(std::string s) : text_(std::move(s)) {}
    Tag(const Tag& other) : text_(other.text_) { std::cout << "Tag copied\n"; }
    Tag(Tag&& other) noexcept : text_(std::move(other.text_)) { std::cout << "Tag moved\n"; }
private:
    std::string text_;
};

class Record {
public:
    Record(std::string label) : label_(std::move(label)), tag_(label_) {}
    Record(Record&& other) noexcept                                        // ①
        : label_(std::move(other.label_)), tag_(other.tag_) {}             // ②
private:
    std::string label_;
    Tag tag_;
};

int main() {
    Record r1("A");
    Record r2(std::move(r1));   // ③
}
// expect: Tag copied
```
1. `Record`'s move constructor takes `Record&&` — the *caller's* argument, `r1` via `std::move`, correctly binds here.
2. But inside the body, `other` is a name: an lvalue. `other.label_` is a member of an lvalue and so is itself an lvalue — `std::move` rescues that one. `other.tag_`, left bare, is also an lvalue, so `tag_(other.tag_)` calls `Tag(const Tag&)`, not `Tag(Tag&&)`.
3. `Record`'s own move constructor did run — the bug is one level down, in what it forgot to do with a member.

## Pitfalls

> [!trap] A `T&&` parameter is only a promise from the caller
> Declaring `Record(Record&& other)` only tells the *caller's* argument how to bind. Every use of `other` *inside* the body is a named expression — an lvalue — so passing a member of `other` onward silently copies unless you write `std::move(other.member)` yourself, every time. See *In Code*, Example 3. This is the single most common reason a hand-written move constructor is no faster than a copy constructor.

> [!ub] Returning `T&&` to a local
> `T&&` extends the lifetime of a temporary bound *directly* to it, but a function that returns `Widget&& f() { Widget w; ...; return std::move(w); }` returns a reference to `w`, which is destroyed when `f` returns. The caller receives a dangling reference — exactly the failure mode of returning `T&`. See [[Dangling Pointers and References]].

> [!trap] `T&&` in a template is not this note
> `template<class T> void f(T&& x)` looks identical to a plain rvalue reference but binds to lvalues *and* rvalues — it is a **forwarding reference**, governed by reference collapsing, not the binding rule in *Mechanics*. See [[Forwarding References and Reference Collapsing]].

## Evolution

See [[Map — Evolution of C++]] for the language-wide timeline.

| Standard | Change | Why |
|---|---|---|
| C++98/03 | Only `T&` and `const T&` exist | No reference type could bind a temporary *and* permit mutation through it, so stealing a temporary's resources had no expressible syntax |
| **C++11** | `T&&` introduced as a distinct reference type; enables move constructors, move assignment, `std::move`; reference collapsing formalized for templates (`[dcl.ref]`) | Move semantics needed a compile-time-checkable "no other user" signal |
| C++17 | Guaranteed copy elision (P0135) removes many of the move-constructor calls a returned prvalue used to require | See [[Value Categories]] *Evolution* — a prvalue now initializes its result object directly, without ever binding a reference |
| C++20/23 | Implicit move extended to more `return`/`throw` forms (P1825); move-eligible names in `return` treated as xvalues (P2266) | Fewer places a programmer must write `std::move` by hand on a local about to go out of scope |

## Connections

- **Prerequisites:** [[Value Categories]] — establishes what an rvalue *is* before this note gives it a reference type to bind to.
- **Enables:** [[Move Semantics]] (turns the binding into a policy — what a move constructor actually *does* once it holds the reference) → [[move and forward — Casts, Not Actions]] (the casts that manufacture the rvalues this note's rules bind to) → [[Forwarding References and Reference Collapsing]] (the template-only binding rule that looks identical but isn't).
- **Siblings:** [[References]] (the lvalue-reference half of the same language feature) · [[Copy Semantics — Deep vs Shallow Copy]] (the cost `T&&` exists to avoid).
- **Hazards:** [[Dangling Pointers and References]] (returning `T&&` to a local) · [[The Moved-From State]] (what a "stolen" object must still support).
- **Domain:** [[Map — Ownership & Move Semantics]].
- **Practice:** *Continuum #22 Rule-of-Five Resource Manager* — write a move constructor for a resource-owning class, then instrument it (as in *In Code*, Example 2) to confirm which call sites actually bind `T&&`.

## Check Yourself

> [!quiz]- What must be true of an expression for `T&&` to bind to it, and what does binding grant the function that holds the reference?
> The expression must be an rvalue (a prvalue or an xvalue) — one the compiler can prove has no other user for the binding's duration. Binding grants *permission*, not action: the function may mutate or steal from the referred-to object, but nothing is moved unless the function body actually does so.

> [!quiz]- `void f(Widget&& w) { store(w); }` where `store` overloads on `Widget&` and `Widget&&`. Which overload runs, and why?
> `store(Widget&)`. Inside `f`, `w` is a name, hence an lvalue — the fact that its *declared type* is `Widget&&` only describes how the caller's argument bound; it says nothing about what `w` is once you write it as an expression. To forward the permission, write `store(std::move(w))`.

> [!quiz]- Predict: using the `Buffer` class from *In Code*, Example 2, what happens if you delete the `Buffer(Buffer&&)` overload entirely and then run `Buffer c = std::move(a);`?
> It still compiles and still constructs `c` — but now the only remaining constructor is `Buffer(const Buffer&)`, and `const T&` accepts an rvalue argument as a fallback. `std::move(a)` binds `const Buffer&`, and `c` is built with a full copy: `std::move` requests permission to steal, but nothing forces a class to accept the offer.

## Sources

- Primer §13.6.1 "Rvalue References" (pp. 532–533): the core binding rules — `T&&` binds only rvalues, cannot bind a named variable even of rvalue-reference type, and why "lvalues persist, rvalues are ephemeral" is the justification for allowing the steal.
- Tour §6.2.2 "Moving Containers" (pp. 76–78): the motivating case (`Vector operator+`) for why returning by value needed a move constructor, and the observation that binding `&&` marks something no other party can reach, which is precisely what makes taking its contents safe.
- cppreference, *Reference declaration* — Rvalue references, Reference collapsing, Forwarding references: https://en.cppreference.com/w/cpp/language/reference
- Draft standard `[dcl.ref]` (rvalue vs. lvalue references, ¶2; reference collapsing, ¶7): https://eel.is/c++draft/dcl.ref
- C++ Core Guidelines F.18 ("For 'will-move-from' parameters, pass by `X&&` and `std::move` the parameter") and F.19 ("For 'forward' parameters, pass by `TP&&` and only `std::forward` the parameter"): https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
