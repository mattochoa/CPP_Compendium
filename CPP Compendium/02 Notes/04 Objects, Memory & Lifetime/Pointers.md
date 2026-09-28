---
id: pointers
title: Pointers
aliases:
- raw pointer
- T*
type: concept
domain: D04
tier: 1
status: draft
standard: C++98
prereqs:
- "[[The C++ Object Model — What an Object Is]]"
- "[[Object Lifetime]]"
related:
- "[[References]]"
- "[[Pointers vs References]]"
- "[[Dynamic Memory — new and delete]]"
- "[[Pointer Arithmetic and Arrays]]"
- "[[nullptr and Null Pointers]]"
- "[[Owning vs Observing Pointers]]"
- "[[Dangling Pointers and References]]"
- "[[const and Const-Correctness]]"
practice:
- 11
tags:
- type/concept
- domain/d04
- tier/1
- tension/value-vs-identity
- tension/safety-vs-performance
- std/c++98
- std/c++11
- std/c++20
created: 2026-09-27
updated: 2026-09-28
---

# Pointers

> [!essence]
> A **pointer** is an object whose value is an address: it names another object or function indirectly, the way a street address names a house without being the house. Unlike a reference, a pointer is itself a full object — it has its own storage, it can be left unbound, reseated, compared, and stepped through an array — and everything a reference gives you for free, a pointer gives you only if you ask for it and check it.

## The Problem

A name bound at compile time can reach exactly the object it was declared for, and only for as long as that name is in scope. That is enough for straight-line code, but not for a program that has to build a structure whose shape isn't known until it runs: a list that grows, a tree whose branches are discovered one node at a time, a loop that walks along an array by stepping to "the next one," a slot that might legitimately hold no object at all. None of that is expressible with names alone, and — before references exist as a language feature — it isn't expressible with an alias either, because an alias is bound once and never moves.

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint.** A name or an alias reaches exactly one object, fixed at compile time or at binding. Code that must decide *at run time* which object to reach next — or whether there is one at all — has nothing to decide it with.
> 2. **Consequence.** Every data structure whose links change while the program runs (a list, a tree, a cursor walking an array) needs a value that can be *re-aimed*, and every optional relationship (a node with no next, a search that may fail) needs a value that can legitimately mean "nothing."
> 3. **Requirement.** The language needs an access path that is itself an ordinary, storable, reassignable value — one that can be computed, copied into a data structure, changed to name a different object, and compared against "no object" — while still telling the compiler what type sits at the far end, so the right code gets generated at the point of use.
> 4. **Design.** The **pointer**, `T*`: an object whose value is the address of a `T` (or of the position just past an array of `T`, or a special *null* value, or something else again — the four states Mechanics develops). Declaring one asks for indirect, type-checked access to a `T` wherever one turns out to live.
> 5. **Price.** A pointer is exactly as flexible as the requirement demanded, and the language enforces almost none of it. It can be left unset, aimed at nothing, reseated to point anywhere, or walked past the end of what it was given — and unlike a reference, which the compiler refuses to leave unbound, none of that is a compile error. The rest of this domain — [[Dangling Pointers and References|dangling]], [[Reading Uninitialized Variables|uninitialized reads]], [[Owning vs Observing Pointers|ownership]] — is the discipline that pays for the flexibility this note derives.

> [!tension] value ⟷ identity
> A pointer's *value* is an address — copyable, comparable, storable, exactly like an `int`. What that address names is a specific object's *identity*, which the type system tracks (the pointer's type says what's there) but the language never verifies against reality (nothing confirms the object is still alive). A pointer is where C++ lets you hold an identity as cheaply as a value, and asks you to keep the bookkeeping honest yourself.

## Mental Model

> [!model] A pointer is a second box, holding an address written on a slip of paper
> A reference is a second name tag on the same box. A pointer is a genuinely separate box, somewhere else in memory, whose *contents* happen to be another box's street address. You can read that address, copy it into a third box, cross it out and write a different address in its place — none of that touches the house at the far end. Reading through the pointer means walking to the address written inside it and looking there instead.
> **Where it breaks:** the analogy suggests the address is always someone's real house. A pointer's box can just as easily hold a torn-up scrap (an address that used to be valid), a blank slip (null), or — if nobody ever wrote anything on it — nothing legible at all (uninitialized). The box doesn't know the difference; only the type system's rules, developed below, do.

```text
 int a = 1;                    ABSTRACT MACHINE: p is a second, separate object
 int* p = &a;

 automatic storage
┌─────────────────────┐        ┌─────────────────────┐
│ p                    │        │ a                    │
│  value: ●────────────┼───────▶│   1                  │
└─────────────────────┘        └─────────────────────┘
   ▲          │
   │          └── p's VALUE (what it holds) == &a
   └── &p: p's OWN address — a second, distinct object exists
```

Contrast this with [[References|a reference]]: there, `&r` cannot yield a second address, because the abstract machine promises there is no second object to give one. Here, `&p` is a perfectly ordinary, distinct address — proof, at the level of the model, that a pointer is a full citizen of the object world and a reference is not.

## Mechanics

Every value of pointer type is one of exactly four kinds (`[basic.compound]`; paragraph numbers below are the current working draft's, not necessarily C++23's):

| Pointer's value | What it means | What's legal to do with it |
|---|---|---|
| **Points to** an object or function | Holds that object's (or function's) address | Dereference, compare, copy, do arithmetic within its array |
| **Points past the end** of an object | The address just after it — even a lone, non-array object counts as a 1-element array for this rule (`[basic.compound]` ¶3) | Compare, copy — **never** dereference |
| **Null** | A dedicated "names nothing" value, distinct for every pointer type | Compare (`if (p)` is `false`), copy, reassign |
| **Invalid** | A determinate address that fails the validity conditions — e.g. its target's lifetime has ended (`[basic.life]`) | Comparison, arithmetic and boolean conversion are merely **implementation-defined**; **dereferencing is undefined** (`[basic.compound]` ¶6) |

> [!standard] "Invalid" is not automatically undefined — dereferencing it is
> It is tempting to read "invalid pointer" as "undefined behavior waiting to happen." The current Standard is more specific: using an invalid pointer value in an indirection (`*p`, `p->m`) is undefined, but using the *same* invalid value in a comparison, in pointer arithmetic, or converting it to `bool` is only **implementation-defined** — some real, if unspecified, outcome, never a licence for anything (`[basic.compound]` ¶6). Only the act of reading *through* it, or `delete`-ing it, crosses into UB.

The other core operations, in one table:

| Situation | Rule | Example |
|---|---|---|
| Declaring a pointer: `T*` | The `*` binds to **one declarator**, not the base type — a common misreading | `int* p1, p2;` — only `p1` is a pointer; `p2` is a plain `int` (Primer §2.3.3, p. 57; In Code, Example 1) |
| Initializing from an object | The address-of operator `&` yields a pointer to its operand | `int* p = &a;` |
| Dereferencing: `*p` | Yields the object `p` points to — legal only for a pointer in the "points to" state | `*p = 0;` writes through `p` into `a` |
| Reassigning: `p = &b;` | Changes what `p` holds, never the previously-addressed object — the opposite of assigning *through* a reference | See In Code, Example 2 |
| Pointer to pointer: `T**` | An ordinary pointer whose pointee type is itself `T*`; dereference once per `*` | `int** pp = &p; **pp` reaches the `int` |
| `void*` | Can hold the address of any object, but names no type at that address: no dereference, no arithmetic. Guaranteed the same representation and alignment as `char*` (`[basic.compound]` ¶9) | See In Code, Examples 3–4 |
| Pointer to `const T` vs. `const` pointer | `const T*` — can't modify through the pointer, can reseat it. `T* const` — can modify the target, can't reseat. Read right-to-left | [[const and Const-Correctness]] develops both fully |
| Comparison: `==`, `!=`, `<` | Compares **addresses**, not what's stored there; ordering across unrelated objects is unspecified, not undefined | Full treatment in [[Pointers vs References]] |

## Under the Hood

> [!machine] A pointer parameter is one address in one register — GCC 11.4, x86-64 Linux (Itanium ABI), `-O2`
> ```nasm
> set_through_ptr(int*):    ; void set_through_ptr(int* p) { *p = 99; }
>         movl  $99, (%rdi)    ; ① write straight through the address in rdi
>         ret
> address_of(int&):         ; int* address_of(int& x) { return &x; }
>         movq  %rdi, %rax     ; ② the reference's address becomes the return value, unchanged
>         ret
> ```
> ① `*p = 99` needs no test, no indirection beyond the CPU's own addressing mode: the address already sitting in `rdi` is used directly as the store's target. ② A reference parameter *already arrives as a plain address* — turning it into a `T*` costs nothing, which is the machine-level reason `[[Pointers vs References]]` calls the two "the same address, different contract."

The Mental Model's two boxes are real, and — on this toolchain — a data pointer's size doesn't depend on what it points to:

```text
sizeof(int*)=8  sizeof(double*)=8  sizeof(void*)=8   (GCC 11.4, x86-64 Linux, LP64)

 automatic storage                        8 bytes, whatever T is
┌───────────────────────┐
│ p : int*     (its own  │
│  address, &p)          │
│  value ●───────────┐   │
└────────────────────┼───┘
                      ▼
              ┌─────────────┐
              │ a : int     │
              │   = 1       │
              └─────────────┘
```
That uniform size is a fact about *this* ABI (Itanium, x86-64, LP64), not a language guarantee — `[basic.compound]` ¶3 says only that "the value representation of pointer types is implementation-defined." A function pointer or a pointer-to-member is not promised the same size or bit layout as a data pointer at all; only `void*` gets an explicit guarantee (same representation as `char*`, ¶9).

## In Code

**1 · The declarator misconception, made to fail**

```cpp
#include <cstdio>
#include <type_traits>

int main() {
    int a = 1;
    int* p1 = &a, p2 = a;   // ① the * belongs to p1's declarator alone
    std::printf("%d %d\n",
                 std::is_same_v<decltype(p1), int*>,
                 std::is_same_v<decltype(p2), int>);
}
// expect: 1 1
```
1. The naive expectation is that `int*` is "the type" for the whole line, so `p2` should be a pointer too. It isn't: `p2 = a` copies `a`'s value into a plain `int`. `decltype` confirms both types directly, rather than trusting the appearance of the line (Primer §2.3.3, p. 57).

**2 · A pointer has its own address, distinct from the address it holds**

```cpp
#include <cstdio>

int main() {
    int a = 1, b = 2;
    int* p = &a;
    std::printf("*p=%d  p==&a:%d  &p==p:%d\n",
                 *p, p == &a,
                 static_cast<void*>(&p) == static_cast<void*>(p));   // ①

    p = &b;                                                         // ②
    std::printf("*p=%d  a=%d\n", *p, a);

    int** pp = &p;                                                  // ③
    std::printf("**pp=%d\n", **pp);
}
// expect: *p=1  p==&a:1  &p==p:0
// expect: *p=2  a=1
// expect: **pp=2
```
1. `&p` (where `p` itself lives) and `p` (the address `p` holds) are two different addresses — the two boxes of the Mental Model, made concrete.
2. Reassigning `p` changes what it points to; `a` is untouched. Compare [[References]]'s Example 1, where the analogous line changes the *referent's value* instead.
3. `pp` holds `p`'s own address; two dereferences reach `a`'s value.

**3 · `void*` erases the type — so it also erases what you can do**

```cpp
// cc: ill-formed
#include <cstdio>

int main() {
    double d = 3.5;
    void* pv = &d;         // ① any object pointer converts to void* implicitly
    std::printf("%f\n", *pv);   // error: pointer to incomplete type 'void'
}
```
1. `void*` can *hold* the address of anything, but there is no type at the far end for `*pv` to yield — the compiler has nothing to dereference into, so this is rejected before it ever runs.

**4 · Getting the type back needs an explicit cast — unlike C**

```cpp
#include <cstdio>

int main() {
    double d = 3.5;
    void* pv = &d;
    double* back = static_cast<double*>(pv);   // ① void* → T* is never implicit in C++
    std::printf("%.1f\n", *back);
}
// expect: 3.5
```
1. C lets a `void*` convert back to any object-pointer type implicitly; C++ requires an explicit cast, because the compiler has no way to check that `pv` genuinely addresses a `double` — the programmer states that claim explicitly instead of it happening silently.

## Pitfalls

> [!ub] An uninitialized pointer is worse than merely invalid
> A block-scope pointer with no initializer holds an **indeterminate** value, not a real-but-stale address. Producing an indeterminate value by evaluation — which includes simply *reading* the pointer, as in `int* q = p;` — is undefined behavior in its own right (cppreference, *Default-initialization*), before the separate question of whether the address it happens to contain is even valid. Primer's advice is unconditional: initialize every pointer, to a real address or to `nullptr`, the moment it's declared (Primer §2.3.2, p. 54). [[Reading Uninitialized Variables]] develops this failure mode in full.

> [!ub] Dereferencing null or dangling
> Both are pointer values that fail the "points to an object" state — one by construction, one by the target's lifetime ending underneath it. The language performs no check at the dereference; [[Dangling Pointers and References]] is the complete treatment of the second case, including detection and fixes.

> [!trap] Walking past the array is UB the moment it's computed, not the moment it's read
> `arr + n` for an `n`-element array is the one legal one-past-end position; anything further is undefined the instant the address is formed, whether or not it's ever dereferenced. [[Pointer Arithmetic and Arrays]] is the full rule, with the exact clause and a sanitizer that stays silent about it.

> [!trap] A `void*` that used to be a different type, cast back, can violate strict aliasing
> Converting through `void*` doesn't make an object's *actual* type stop mattering: reading it back as an unrelated type is a separate hazard from the ones this note covers. [[Strict Aliasing and Type Punning]] is where that rule lives.

## Evolution

See [[Map — Evolution of C++]] for the language-wide timeline.

| Standard | Change | Why |
|---|---|---|
| C / **C++98** | The four-state pointer-value model; `0` or the `NULL` macro as the null pointer constant; `void*` converts implicitly from any object pointer but back only with a cast | A typed, reseatable, "maybe nothing" access path, inherited directly from C |
| **C++11** | `nullptr` and `std::nullptr_t` (cppreference, *`nullptr`*) | `0`/`NULL` are integers in disguise: they silently prefer an `int` overload over a pointer overload. `nullptr` has its own type, so overload resolution can never confuse "no object" with the number zero |
| C++17 | `std::launder` (`<new>`) added, for the narrow case of retrieving a valid pointer to an object created by placement-`new` over old storage of the same type | Needed once [[Object Lifetime|guaranteed transparent replacement]] made "same address, new object" a defined situation the optimizer could otherwise reason past |
| **C++20** | Built-in `operator<=>` defined for pointer types, yielding `std::strong_ordering` for a shared *composite pointer type* (cppreference, *Comparison operators*) | Gives pointers a single three-way comparison consistent with the existing `==`/`<` rules, instead of requiring both spelled out |

## Connections

- **Prerequisites:** [[The C++ Object Model — What an Object Is]] — an address is a property of where an object's storage lives · [[Object Lifetime]] — a pointer's "points to an object" state is a claim about lifetime the language never checks for you.
- **Enables:** [[Pointers vs References]] (the full contrast with the other access path) → [[Parameter Passing — Value, Reference, Pointer]] (this note's "an object holding an address" is exactly the third parameter form, the one that can be null) → [[Virtual Functions]] (dynamic dispatch is only reachable through a pointer or a reference — never through the object's own name) → [[Dynamic Memory — new and delete]] (a pointer is exactly what `new` returns and `delete` consumes) → [[Pointer Arithmetic and Arrays]] (the one-past-the-end rule this note only states) → [[nullptr and Null Pointers]] (the null-pointer-constant story in full) → [[Owning vs Observing Pointers]] (who, if anyone, may `delete` through one).
- **Siblings:** [[References]] (no separate storage, can't be null, can't reseat — everything a pointer can do that a reference can't, and the reverse) · [[const and Const-Correctness]] (pointer-to-`const` vs. `const` pointer, read right-to-left) · [[Process Memory Layout — Stack, Heap, Static]] (the regions the addresses a pointer actually holds belong to).
- **Explains:** [[Virtual Dispatch — vptr and vtable]] — the vptr every polymorphic object carries is, physically, a hidden pointer member, laid out and rewritten exactly as this note's Under the Hood describes for any other pointer.
- **Hazards:** [[Dangling Pointers and References]] · [[Reading Uninitialized Variables]] · [[Strict Aliasing and Type Punning]].
- **Domain:** [[Map — Objects, Memory & Lifetime]].
- **Practice:** *Continuum #11 Pointer & Array Internals Lab* — print `p`, `&p`, and `*p` side by side and confirm which ones move when you reseat `p` versus assign through it.

## Check Yourself

> [!quiz]- What are the four values a pointer can hold, and which of them are legal to *compare* but never to *dereference*?
> Points-to-an-object, points-past-the-end, null, and invalid. All four are legal in a comparison; only "points to an object" is safe to dereference — the other three are either meaningless to read through (past-the-end, null) or undefined the moment you try (invalid). See Mechanics.

> [!quiz]- Why does `int* p1, p2;` declare only `p1` as a pointer?
> A declarator's `*` modifies the single name it's attached to, not the statement's base type. The base type here is `int`; `p1`'s declarator adds the pointer, `p2`'s doesn't. See In Code, Example 1, and Primer §2.3.3.

> [!quiz]- After `int* p = &a; p = &b;`, has `a` changed? What about after `int& r = a; r = b;`?
> `a` is untouched by `p = &b;` — reassigning a pointer changes what it holds, never the object it used to address. `r = b;`, by contrast, assigns `b`'s *value* into `a` through the reference, because a reference has no "reseat" operation at all. See In Code, Example 2, and [[References]].

> [!quiz]- Why does `void* pv = &d;` compile but `*pv` does not, and what fixes it?
> `void*` can hold any object's address, but names no type at the far end, so the compiler has nothing to dereference into — `void` isn't an object type. `static_cast<double*>(pv)` supplies the missing type explicitly, which is required in C++ (unlike C, where the conversion back is implicit). See In Code, Examples 3–4.

## Sources

- Primer §2.3.2 "Pointers" (pp. 52–54): the object-vs-reference framing, the four-state pointer-value model, the "always initialize pointers" advice. Primer §2.3.2 "`void*` Pointers" (p. 56): what operations `void*` permits. Primer §2.3.3 "Understanding Compound Type Declarations" (pp. 57–58): the `int* p1, p2;` misconception; pointers to pointers. Primer §2.4.2 "Pointers and `const`" (pp. 62–63): pointer-to-`const` vs. `const` pointer.
- Tour §15.2 "Pointers" (p. 196): the generalized notion of "pointer" spanning `T*`, `T&`, smart pointers, `span`, and iterators, and the owning/non-owning distinction.
- PPP §16.2 "Pointers and references" (ch. 16 "Arrays, Pointers, and References"): both built from a memory address, differing only in what the language then lets you do with it.
- cppreference, *Pointer declaration* (incl. §*Null pointers*, §*Invalid pointers*): https://en.cppreference.com/w/cpp/language/pointer · *`nullptr`*: https://en.cppreference.com/w/cpp/language/nullptr · *Default-initialization*: https://en.cppreference.com/w/cpp/language/default_initialization · *Comparison operators* (pointer `<=>`): https://en.cppreference.com/w/cpp/language/operator_comparison
- Draft standard `[basic.compound]` ¶3, ¶6, ¶9 (the four-state model, validity, `void*`'s guaranteed representation): https://eel.is/c++draft/basic.compound — paragraph numbers are the current working draft's.
- C++ Core Guidelines F.22 ("Use `T*` or `owner<T*>` to designate a single object"), R.3 ("A raw pointer is non-owning"): https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
