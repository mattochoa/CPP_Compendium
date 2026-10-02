---
id: references
title: References
aliases:
- lvalue reference
- alias (C++)
- T&
type: concept
domain: D04
tier: 1
status: reviewed
standard: C++98
prereqs:
- "[[Object Lifetime]]"
related:
- "[[Pointers]]"
- "[[Pointers vs References]]"
- "[[Value Categories]]"
- "[[Temporaries and Lifetime Extension]]"
- "[[const and Const-Correctness]]"
- "[[Dangling Pointers and References]]"
practice:
- 6
tags:
- type/concept
- domain/d04
- tier/1
- tension/safety-vs-performance
- std/c++98
created: 2026-09-27
updated: 2026-09-28
reviewed: 2026-10-01
score: 19
rubric:
  accuracy: 2
  first_principles: 3
  clarity: 3
  depth: 3
  visual: 2
  code: 3
  integration: 3
---

# References

> [!essence]
> A **reference** is not an object — it is another name for one. Once bound, at initialization, it names the same object forever: reading or writing through it reads or writes the object itself, with no rebinding, no null state, and (in the abstract machine) no storage of its own.

## The Problem

A function that takes its argument by value copies it. For a small `int` that copy is free; for a `std::vector<double>` with a million elements, it is a heap allocation and a million-element copy on every call. Passing the *address* of the argument instead — a pointer — avoids the copy, but a pointer brings its own machinery along: it must be explicitly dereferenced (`*p`, `p->m`), it can be null, it can be reseated to point somewhere else mid-function, and nothing stops it from being left uninitialized.

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint.** Copying an object costs time and space proportional to its size; some objects (a `std::mutex`, an I/O stream) cannot be copied at all.
> 2. **Consequence.** Code that only needs to *read or modify* an existing object — never to hold "no object" or to switch which object it's talking about — pays for flexibility (pointer arithmetic, reseating, a null state) that it never uses, and gets a strictly weaker guarantee (a pointer might not point at anything) than the code actually needs.
> 3. **Requirement.** The language needs an indirect access path that costs no more than a pointer, is guaranteed bound to a real object once usable, and reads and writes with the exact syntax of the object itself — no `*`, no `->`.
> 4. **Design.** A **reference**, written `T&`. It is bound to its initializer once, at the point it is declared, and stays bound to that same object for its entire lifetime. Every subsequent use of the reference's name is, syntactically and semantically, a use of the object it is bound to.
> 5. **Price.** All the flexibility a pointer keeps is gone on purpose: a reference cannot be left unbound, cannot be reseated, cannot be null, and cannot be put in an array or a container of references. That rigidity is not a limitation to work around — it is the entire feature. [[Pointers vs References]] works out when that trade is worth making.

> [!tension] safety ⟷ performance
> A reference buys a pointer's performance — pass an address, not a copy — while keeping much of a plain variable's safety: it cannot exist unbound, and using its name never requires an explicit dereference that could be forgotten or miscounted. The cost side of the tension does not vanish; it moves to *construction time*, where the language demands proof (an initializer) that the trade is being made honestly.

## Mental Model

> [!model] A second name tag on the same object, not a locker with an address inside it
> Binding a reference is like putting a second name tag on a box that already has one. Both tags point at the same box; writing through either tag changes the same contents. A pointer, by contrast, is its own separate box whose contents happen to be an address — you can erase that address and write in a different one, or leave the box empty.
> **Where it breaks:** a name tag has no existence of its own to inspect — you cannot ask "where is the tag itself taped down?" `&r` never answers that question; it always gives you the box's address, because there is no second address to give. Under the Hood shows that real compilers do sometimes need a genuine second box (a hidden pointer) to *implement* the tag — the abstract model and the machine model diverge exactly there.

```text
 int a = 1, b = 2;
 int& r = a;                     ABSTRACT MACHINE: one box, two names

 automatic storage
┌────────────────────┐   ┌────────────────────┐
│ a  /  r             │   │ b                   │
│   1                 │   │   2                 │
└────────────────────┘   └────────────────────┘
        ▲
   r is not a second box; it is not an object the
   Standard requires storage for ([dcl.ref] ¶4)
```

## Mechanics

The Standard defines references in `[dcl.ref]` (declaration) and `[dcl.init.ref]` (binding rules). The practical rules:

| Situation | Rule | Example |
|---|---|---|
| Declaring a reference: `T&` | Declares an **lvalue reference** to `T`. `T&&` declares a distinct type, an **rvalue reference** (see [[Value Categories]], [[Rvalue References]]) | `int& r = i;` |
| Initializing | Must be initialized where declared — except an `extern` declaration, an in-class member declaration, or a function parameter/return type. Binding happens once, at initialization, never again (`[dcl.ref]` ¶5) | `int& r2;` — ill-formed |
| Plain `T&` | Direct-binds only to a non-bit-field lvalue whose type is reference-compatible with `T` — never to a literal or a temporary (`[dcl.init.ref]`) | `int& r = 5;` — ill-formed (In Code, Example 4) |
| `const T&` ("reference to const") | Binds to an lvalue, a literal, or a general expression of a different type. When the initializer isn't already the right type or category, the compiler materializes a temporary and binds to *that* (`[dcl.init.ref]`; see [[Value Categories]] on temporary materialization) | `const int& r = 2 + 2;` |
| A reference bound **directly** to a temporary (or its subobject) | Extends that temporary's lifetime to match the reference's own | In Code, Example 3 |
| `&r` | Yields the address of the *referent* — a reference has no address of its own to give | `&r == &a` in Example 1 |
| Reference to reference, pointer to reference, array of references | All ill-formed when written directly; a reference formed *through* a typedef, `decltype` or template parameter instead *collapses* (`[dcl.ref]` ¶5, ¶7 — C++11) | `int& &x;` — ill-formed |
| A non-static data member of reference type | Has no default; must be bound in the constructor's member-initializer list, once, like any other reference (see [[Constructors]]) | `struct S { int& r; S(int& x) : r(x) {} };` |

> [!standard] A reference is not an object, and its "lifetime" is a special case
> `[basic.life]` ¶3 states it directly: *the lifetime of a reference begins when its initialization is complete, and ends as if it were a scalar object requiring storage.* That is a deliberate fiction — `[dcl.ref]` ¶4 says it is genuinely **unspecified** whether a reference requires storage at all. The Standard gives a reference a lifetime so that rules written in terms of "lifetime" (like the ones in [[Object Lifetime]]) apply to it too, without claiming it is an object.

## Under the Hood

> [!machine] A reference parameter compiles to a hidden pointer — GCC 11.4, x86-64 Linux (Itanium ABI), `-O2`
> The abstract model says "no second box." The System V calling convention still has to move *some* bits into the callee, and for a reference it moves an address:
> ```nasm
> set_by_ref(int&):        ; void set_by_ref(int& x) { x = 99; }
>         mov  DWORD PTR [rdi], 99   ; ① write 99 through the address in rdi
>         ret
> set_by_val(int):          ; void set_by_val(int x)  { x = 99; }
>         ret                        ; ② the store to the local copy is invisible, so GCC deletes it
> ```
> ① `rdi` holds `&x`'s target address — exactly a pointer, passed in the same register a `int*` parameter would use. ② is the sharper proof of the whole derivation: mutating a by-value copy can never be observed by the caller, so an optimizing compiler is free to — and does — remove the mutation entirely. The reference version keeps its store because *only* a reference lets the caller see the change.

A reference used purely as a local alias, never having its address taken or escaping the function, usually compiles to nothing at all: the compiler substitutes the referent everywhere the reference's name appears and the "second name" evaporates, the same way `std::move` compiles to no instructions ([[Value Categories]]).

A reference **member**, by contrast, is a case `[dcl.ref]` ¶4's "unspecified" almost always resolves to "yes, storage" — a class has to hold *something* that lets its member functions find the referent later:

```text
sizeof(NoRef)=4   sizeof(HasRef)=16   sizeof(int*)=8    (GCC 11.4, x86-64 Linux, LP64)

struct NoRef  { int x; };            struct HasRef { int x; int& r; ... };
┌────────┐                           ┌────────┬────────────────────┐
│ x : 4B │                           │ x : 4B │ pad(4B)│ r : 8B ptr │
└────────┘                           └────────┴────────────────────┘
                                          16 bytes total: r costs a real pointer's worth
```

## In Code

**1 · A reference is a second name, not a rebindable box**

```cpp
#include <cstdio>

int main() {
    int a = 1, b = 2;
    int& r = a;                                            // ①
    std::printf("before: a=%d b=%d &r==&a:%d\n", a, b, (&r == &a));

    r = b;                                                  // ②
    std::printf("after:  a=%d b=%d &r==&a:%d\n", a, b, (&r == &a));
}
// expect: before: a=1 b=2 &r==&a:1
// expect: after:  a=2 b=2 &r==&a:1
```
1. `r`'s binding is fixed the instant it is initialized. There is no unbound, "not yet pointing anywhere" state to worry about.
2. `r = b` reads `b`'s value and assigns it *through* `r` into `a`. It is not a rebind: `&r` still equals `&a` on the next line, and `a` — not `r` — now holds `2`.

**2 · Pass-by-reference is the only one of the two that can be observed by the caller**

```cpp
#include <cstdio>

void reset_by_ref(int& x) { x = 0; }
void reset_by_val(int x)  { x = 0; }

int main() {
    int a = 5, b = 5;
    reset_by_ref(a);
    reset_by_val(b);
    std::printf("a=%d b=%d\n", a, b);
}
// expect: a=0 b=5
```
`x` in `reset_by_ref` is bound to `a` itself for the call's duration, so the assignment is visible after return. `x` in `reset_by_val` is a separate, temporary copy; assigning to it can change nothing the caller can see — which is exactly what Under the Hood's assembly proves the optimizer knows.

**3 · A `const` reference bound directly to a temporary keeps it alive**

```cpp
#include <cstdio>
#include <string>

std::string greeting(const std::string& name) {
    return "Hello, " + name;                                // ①
}

int main() {
    const std::string& r = greeting("Ada");                 // ②
    std::printf("%s\n", r.c_str());                         // ③
}
// expect: Hello, Ada
```
1. Both the concatenation and the returned value are temporaries.
2. `r` binds *directly* to the temporary `greeting` returns — nothing else sits between them — so `[dcl.init.ref]`'s lifetime-extension rule applies: the temporary now lives as long as `r` does.
3. Still valid. Had `r` instead been bound to the result of calling a member function *on* that temporary, extension would not apply — see [[Temporaries and Lifetime Extension]] for the full rule and its traps.

**4 · A plain `T&` refuses to bind to an rvalue — on purpose**

```cpp
// cc: ill-formed
int compute() { return 42; }

int main() {
    int& r = compute();   // error: cannot bind non-const lvalue reference to an rvalue
}
```
`compute()`'s result is a prvalue with no persistent identity for anyone to hand back. Letting `r` bind to it would let code "assign into" a value that is about to disappear and that nobody else can observe — almost certainly a bug, so the direct-binding rule in Mechanics makes it a compile error instead.

## Pitfalls

> [!trap] Assigning through a reference is not reassigning it
> `r = b;` never changes what `r` is bound to; it changes the object `r` is already bound to. Reading code that treats `=` on a reference as "now `r` means `b`" is the single most common misreading of reference syntax. See [[Pointers vs References]] for how a pointer's `p = &b;` differs.

> [!ub] Returning a reference to a local is a dangling reference the moment the function returns
> `std::string& f() { std::string s = "x"; return s; }` binds the returned reference to `s`, whose automatic storage is released at `f`'s closing brace ([[Object Lifetime]], [[Process Memory Layout — Stack, Heap, Static]]). Every use of the caller's reference afterward is undefined behavior — full treatment, detection and fixes in [[Dangling Pointers and References]].

> [!trap] There is no reference to a reference, outside templates
> `int& &r;`, arrays of references, and pointers to references are all ill-formed (`[dcl.ref]` ¶5). Generic code that writes `T&` where `T` is itself deduced as a reference type doesn't hit this error, because *reference collapsing* (C++11) resolves the combination to a plain reference before the "no references to references" rule would ever apply — see [[Forwarding References and Reference Collapsing]].

## Evolution

See [[Map — Evolution of C++]] for the language-wide timeline.

| Standard | Change | Why |
|---|---|---|
| **C++98** | References exist as lvalue references only: `T&`, with essentially today's binding, no-rebind and no-null rules (`[dcl.ref]`) | An alias mechanism with a pointer's performance and a named variable's syntax |
| **C++11** | Rvalue references `T&&` added as a distinct type; *reference collapsing* formalized (`T& &`, `T& &&`, `T&& &` all collapse to `T&`; only `T&& &&` stays `T&&`) (`[dcl.ref]` ¶7) | Move semantics ([[Value Categories]]) needed a reference kind that binds to expiring values, and templates needed a defined rule for "a reference to a deduced reference type" |
| C++17 | Guaranteed copy elision (P0135) changes *what* a reference to a prvalue initializer binds to: the prvalue materializes directly into the bound temporary, with no separate move-from-temporary step even notionally | Removes a copy/move step that earlier reference-binding rules implied but never required |
| C++26 | A `return` statement whose returned reference would bind to a *temporary* is ill-formed (P2748R5, `[stmt.return]`): `const int& f() { return 42; }` no longer compiles | Closes the always-dangling temporary case at compile time. Returning a reference to a *named local* (the Pitfall below) is not covered: it is still undefined behavior, caught only by warnings such as GCC's `-Wreturn-local-addr` |

## Connections

- **Prerequisites:** [[Object Lifetime]] — a reference's own "lifetime" is defined only by analogy to an object's, and every binding is a claim that the referent's lifetime hasn't ended.
- **Enables:** [[Pointers]] → [[Pointers vs References]] (the full decision between them) → [[Parameter Passing — Value, Reference, Pointer]] (binding is exactly what makes `T&`/`const T&` the "in-out" and "cheap read-only" parameter forms) → [[Virtual Functions]] (a reference is one of the two ways to get dynamic dispatch without slicing) → [[Constructors]] (member-initializer-list binding for reference members).
- **Siblings:** [[Value Categories]] (which expressions a plain `T&` versus a `const T&`/`T&&` may bind to) · [[Temporaries and Lifetime Extension]] (the full rule behind Example 3) · [[const and Const-Correctness]] (the const half of a reference's contract).
- **Explains:** [[Dangling Pointers and References]] (why a returned reference to a local always dangles) · [[Process Memory Layout — Stack, Heap, Static]] (where the extended temporary in Example 3 actually lives).
- **Domain:** [[Map — Objects, Memory & Lifetime]].
- **Practice:** *Continuum #6 Function Library & Header Refactor* — as you split code across headers and `.cpp` files, choose each function parameter's form (value, reference, `const` reference) deliberately instead of by habit.

## Check Yourself

> [!quiz]- Where must a reference be initialized, and what are the three exceptions to "at the point it's declared"?
> A reference's declaration must contain an initializer, except when the declaration has an explicit `extern` specifier, is a non-static class member declared inside a class definition (bound later, in a constructor's member-initializer list), or is a function parameter or return type (bound at each call). Outside those three, an uninitialized reference is ill-formed — see Mechanics.

> [!quiz]- After `int& r = a; r = b;`, is `r` now an alias for `b`? What actually happened?
> No. `r` remains bound to `a` for its entire lifetime; only the *initialization* binds a reference. `r = b;` reads `b`'s value and assigns it through `r` into `a` — an ordinary assignment to the object `r` already names. See In Code, Example 1.

> [!quiz]- In Under the Hood, GCC's `-O2` output for `set_by_val` is just a bare `ret` with no store at all. Why is that safe, and what would go wrong if the compiler tried the same trick on `set_by_ref`?
> `set_by_val`'s parameter is a copy; nothing the caller can observe depends on what happens to that copy, so the assignment to it has no observable effect and the "as-if" rule lets the compiler delete it. `set_by_ref`'s parameter is bound to the caller's own object, so the store *is* observable — deleting it would change the program's behavior, which the as-if rule forbids.

> [!quiz]- Why does `int& r = compute();` fail to compile while `const int& r = compute();` succeeds, for the same `int compute()`?
> `compute()` returns a prvalue: a value with no persistent identity. A plain `T&` may only direct-bind to a genuine, addressable lvalue, so there is nothing for it to bind to. `const T&` is permitted to bind to a temporary materialized from the prvalue instead (and to extend that temporary's lifetime to its own), which is exactly what the direct-binding rule for references to `const` allows — see Mechanics and In Code, Example 3.

## Sources

- Primer §2.3.1 "References" (pp. 50–51): the alias definition, "a reference is not an object," the must-initialize/no-rebind rules, and why there are no references to references.
- Primer §2.4.1 "References to const" (pp. 61–62): binding a `const` reference to a temporary of a different type, and why an ordinary reference can't do the same.
- Tour §1.7 "Pointers, Arrays, and References" (p. 13): references for pass-by-reference and `const` reference parameters, contrasted directly with pointers.
- Pikus, "Copying and argument passing" (p. 320): the performance case for `const T&` parameters over pass-by-value on large objects.
- cppreference, *Reference declaration*: https://en.cppreference.com/w/cpp/language/reference
- cppreference, *Reference initialization*: https://en.cppreference.com/w/cpp/language/reference_initialization
- Draft standard `[dcl.ref]` (declaration, storage, no-reference-to-reference, collapsing): https://eel.is/c++draft/dcl.ref
- Draft standard `[basic.life]` ¶3 (a reference's lifetime): https://eel.is/c++draft/basic.life
- C++ Core Guidelines F.16, F.17 (how to pass "in" and "in-out" parameters): https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
