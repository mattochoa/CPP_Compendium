---
id: object-lifetime
title: Object Lifetime
type: concept
domain: D04
tier: 1
status: reviewed
standard: C++98
prereqs:
- "[[Storage Duration]]"
- "[[The C++ Object Model — What an Object Is]]"
related:
- "[[References]]"
- "[[Pointers]]"
- "[[Virtual Functions]]"
- "[[Constructors]]"
- "[[Value Categories]]"
- "[[Temporaries and Lifetime Extension]]"
- "[[Dangling Pointers and References]]"
- "[[Placement new and Manual Lifetime]]"
practice:
- 11
tags:
- type/concept
- domain/d04
- tier/1
- tension/abstraction-vs-control
- std/c++98
- std/c++20
created: 2026-09-27
updated: 2026-09-29
reviewed: 2026-10-01
score: 20
rubric:
  accuracy: 3
  first_principles: 3
  clarity: 3
  depth: 3
  visual: 2
  code: 3
  integration: 3
---

# Object Lifetime

> [!essence]
> An object's **lifetime** is the runtime span in which its type's guarantees actually hold: it begins only once storage exists *and* initialization has completed, and it ends the instant a class type's destructor call **starts** — not when its storage disappears. Nearly every rule about safe access, virtual dispatch during construction, and undefined behavior is really a rule about which side of that boundary an expression falls on.

## The Problem

[[Storage Duration]] fixes *where* an object's bytes come from and how long the underlying memory persists. That answers less than it seems to. A block of bytes with the right size and alignment for a `std::string` is not yet a `std::string`: nothing has run the constructor that sets up its internal pointer, its length, and its small-buffer-or-heap invariant. The same bytes, after that object's destructor has torn those invariants back down, are once again just bytes — even though, for an automatic-duration object, the storage itself might not be reclaimed until the very next line.

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint.** Storage merely reserves bytes. A type's guarantees — a valid internal pointer, a correctly set vptr, an `int` holding a defined value instead of indeterminate bits — exist only for the span during which that type's constructor has finished and its destructor has not yet started.
> 2. **Consequence.** If "the object exists" meant nothing more than "its storage exists," code could read a member before any constructor ran, or call a member function after the destructor had already dismantled the invariants — and get a plausible-looking, wrong answer instead of a caught error.
> 3. **Requirement.** The language needs a second clock, layered on top of storage duration, that names the precise instant a type's guarantees start holding and the precise instant they stop — independent of when the underlying bytes are actually reclaimed.
> 4. **Design.** `[basic.life]` defines exactly that: an object's **lifetime** begins once storage of the right size and alignment exists *and* its initialization is complete, and ends when a non-class object is destroyed or, for a class type, the **moment its destructor call starts**. Storage may easily outlive both endpoints.
> 5. **Price.** What used to feel like one variable "coming and going" now has (at least) two clocks and four moments to keep straight: storage begins, lifetime begins, lifetime ends, storage ends. The gap between the middle two is exactly where a whole class of legal-looking code quietly does the wrong thing (Pitfalls).

> [!tension] abstraction ⟷ control
> The Standard draws lifetime's boundary at a precise instant that reasoning can rely on absolutely — yet nothing is written to memory to mark that instant. An object's bytes look identical the cycle before its constructor finishes and the cycle after; identical again the cycle before its destructor starts and the cycle after. The one place C++ *does* pay to make this boundary real at run time is the vptr rewrite inside every destructor (Under the Hood): proof that "zero-cost abstraction" means the cost is exactly as much control as a guarantee requires, and no more.

## Mental Model

> [!model] Two clocks on the same object, only one of which you set
> [[Storage Duration|Storage duration]] is the outer clock: fixed the moment you choose *how* to declare or allocate something, and nothing during the object's existence can change it. Lifetime is the inner clock nested inside it — it starts only once the *whole* initialization has finished, and it can stop early, well before storage is reclaimed, the moment destruction begins or something else claims the same bytes.
> **Where it breaks:** a clock ticks audibly between events; the compiler marks none of this in the emitted code. The only way to know you've stepped outside an object's lifetime is to already know the rule — there is no runtime tag to consult.

```text
 storage begins                                                storage ends
      │                                                              │
      ▼                                                              ▼
      ┌───────────┬────────────────────────────────────┬────────────┐
      │ no object │          OBJECT LIFETIME            │ no object  │
      │ yet       │   (the type's guarantees hold)      │ any more   │
      └───────────┴────────────────────────────────────┴────────────┘
                  ▲                                      ▲
           lifetime begins                          lifetime ends
        (initialization complete,               (destructor call starts —
          [basic.life] ¶2)                     class types; object destroyed
                                                  outright — non-class types)
```

The four moments are independent in principle. In an ordinary automatic variable they collapse to two visible events (declaration, closing brace); Examples 2 and 3 below are exactly the cases where they pull apart.

## Mechanics

| Situation | Rule | Example |
|---|---|---|
| Non-class object (`int`, a pointer, …) | Lifetime begins once storage and initialization are complete; ends when the object is destroyed — for these types that coincides with storage no longer denoting it (`[basic.life]` ¶2) | `int n = 5;` — lifetime starts at the `=`, ends at `}` |
| Class-type object | Lifetime begins the same way; ends the instant its **destructor call starts**, not when the destructor finishes running (`[basic.life]` ¶2.4) | Example 1 — inside `~Base()`, the `Derived` part's lifetime has already ended |
| Reference | Begins when its own initialization (the binding) completes; ends "as if it were a scalar object requiring storage" — but a reference is never itself an object ([[The C++ Object Model — What an Object Is]]) | `int& r = n;` — `r`'s lifetime tracks the reference, not `n` |
| An object's storage is reused before its scope ends | A placement-`new` that targets an object's storage ends that object's lifetime immediately, regardless of what the enclosing braces say (`[basic.life]` ¶2.5, ¶9–10) | Example 2 |
| An object under construction or destruction | Its own bases/members aren't fully "there" yet from outside; `[class.cdtor]` gives a narrower, own-class-only view for member access, virtual calls, `dynamic_cast` and `typeid` | Example 1 |
| Ending a non-trivially-destructible object's lifetime without calling its destructor | Defined only if another object of the *original* type occupies that storage before the implicit destructor call would fire; otherwise undefined behavior (`[basic.life]` ¶11) | Example 3 |

> [!standard] Lifetime begins after initialization completes, not after storage exists
> `[basic.life]` ¶2 is explicit: the lifetime of an object of type `T` begins only once "storage with the proper alignment and size for type `T` is obtained, **and** its initialization (if any) is complete." Even a scalar with no initializer at all — `int n;` — still counts, via *vacuous initialization*: default-initializing a type with a trivial constructor performs no action but is still "complete" the instant the declaration is reached. The one carve-out is a union member, whose lifetime begins only once it becomes the union's active member (`[class.union]`). Which of the six named forms an initializer takes — default, value, direct, copy, list or aggregate — is exactly what [[The Forms of Initialization]] works out; each one satisfies this same "initialization is complete" clause, just by a different route.

> [!standard] `[class.cdtor]`'s own-class view during construction and destruction
> `[class.cdtor]` ¶4: when a virtual function is called — directly or through another function — from a constructor or destructor of an object currently under construction or destruction, "the function called is the final overrider in the constructor's or destructor's class and not one overriding it in a more-derived class." This is not a quirk of one compiler: it is what the Standard requires, because the more-derived part's lifetime has either not started yet (during construction) or has already ended (during destruction) at that point. [[Virtual Functions]] and [[Constructors]] develop the mechanism this rule protects; this note only fixes *why* the rule has to exist.

## Under the Hood

> [!machine] The vptr is rewritten at the top of every destructor — GCC 11.4, x86-64 Linux (Itanium ABI), `-O0`
> `[class.cdtor]`'s rule needs a real mechanism, and GCC's is visible in the unoptimized assembly for a two-level hierarchy (`Derived : Base`, both with a virtual `announce()`). At the very start of `Derived`'s own destructor, before it calls `Base`'s:
> ```nasm
> _ZN7DerivedD2Ev:                  ; Derived's own destructor body
>     leaq  16+_ZTV7Derived(%rip), %rdx
>     movq  -8(%rbp), %rax
>     movq  %rdx, (%rax)            ; ① write Derived's own vtable pointer into the object
>     movq  -8(%rbp), %rax
>     movq  %rax, %rdi
>     call  _ZN4BaseD2Ev            ; then run Base's destructor
> ```
> and `Base`'s destructor repeats the same move with *its own* vtable, before calling `announce`:
> ```nasm
> _ZN4BaseD2Ev:
>     leaq  16+_ZTV4Base(%rip), %rdx
>     movq  -8(%rbp), %rax
>     movq  %rdx, (%rax)            ; ② overwrite with Base's own vtable pointer
>     movq  -8(%rbp), %rax
>     movq  %rax, %rdi
>     call  _ZNK4Base8announceEv    ; ③ a direct call — no vtable indirection at all
> ```
> ① and ② are the concrete, compiled answer to "where does the abstract lifetime boundary live in memory": every destructor re-tags the object with its *own* class's vtable on entry, walking downward from most-derived to base. By the time `Base`'s body runs, the object's vptr no longer points at `Derived`'s vtable — so at ③ the compiler doesn't even need an indirect call: it already knows exactly which `announce` applies and calls it directly. This is GCC's Itanium-ABI convention for realizing `[class.cdtor]`'s rule, not a Standard requirement in itself; the Standard mandates only the *behavior* Example 1 observes.

## In Code

**1 · A virtual call from a destructor never reaches a more-derived override**

```cpp
#include <cstdio>

struct Base {
    virtual void announce() const { std::printf("Base::announce\n"); }   // ①
    virtual ~Base() { announce(); }                                       // ②
};

struct Derived : Base {
    void announce() const override { std::printf("Derived::announce\n"); }
};

int main() {
    Base* b = new Derived();
    delete b;                    // ③
}
// expect: Base::announce
```
1. The naive expectation: `announce` is virtual, so a call through a `Base*` to a `Derived` object should print `"Derived::announce"`.
2. `~Base()`'s body calls `announce()` on `*this`. By the time this line runs, `~Derived()` has already completed, so `Derived`'s part of the object has already ended its lifetime.
3. `delete` runs `~Derived()` first, then `~Base()`. Inside `~Base()`, `[class.cdtor]` requires the call to resolve to `Base::announce` — matching Under the Hood's assembly evidence exactly, not a compiler quirk.

**2 · Placement-`new` ends an object's lifetime before its storage duration does**

```cpp
#include <cstdio>
#include <new>

struct Counter { int value; };

int main() {
    Counter c{1};
    Counter* p = &c;
    std::printf("before: %d\n", p->value);

    new (p) Counter{99};                 // ① ends c's lifetime, starts a new one, same bytes
    std::printf("after:  %d\n", p->value);            // ② p and c now name the new object
    std::printf("same address: %d\n",
                 static_cast<void*>(p) == static_cast<void*>(&c));
}
// expect: before: 1
// expect: after:  99
// expect: same address: 1
```
1. `Counter` has a trivial destructor, so ending `c`'s lifetime this way is well-defined (`[basic.life]` ¶11 only bites for *non*-trivial destructors — see Example 3). The new object's storage exactly overlays the old one and is of the same type, so `c` is *transparently replaceable* by it (`[basic.life]` ¶9).
2. `[basic.life]` ¶10: once a transparently-replaceable object is created in the old one's storage, the old pointer, reference, and even the old *name* automatically refer to the new object. Nothing here is UB, and nothing needed a new variable.

**3 · Skipping a non-trivial destructor before storage is reused: undefined behavior**

```cpp
// cc: ub
#include <cstdio>
#include <new>
#include <string>

struct Loud {
    std::string tag;
    ~Loud() { std::printf("~Loud(%s)\n", tag.c_str()); }   // non-trivial destructor
};
struct Silent { int x; };

void f() {
    Loud a{"first"};
    new (&a) Silent{42};   // ① ends a's lifetime without ever calling ~Loud
}                          // ② the implicit ~Loud() still fires here
int main() { f(); }
```
1. `Loud`'s destructor never ran; its storage was simply reused for an unrelated `Silent`.
2. `[basic.life]` ¶11: because `Loud` has a non-trivial destructor and no object of the *original* type (`Loud`) occupies that storage when the block's implicit destructor call fires, the program is undefined the instant `f` returns. This vault's toolchain (GCC 11.4, x86-64 Linux, ASan+UBSan) observed the implicit `~Loud()` call reading `tag` out of what is actually a `Silent`'s bit pattern, and crashing with `AddressSanitizer: SEGV` inside `std::string`'s internals. A different standard library, or the same one built differently, is free to fail in an unrelated way, hang, or appear to work — that is what "undefined" means; never read this crash as a guarantee.

## Pitfalls

> [!ub] A pointer that still compiles is not proof of a live object
> Nothing in a pointer's or reference's own representation records whether its target's lifetime has ended — dereferencing one after that point is undefined the instant it happens, whether or not the underlying storage has been reused yet. [[Dangling Pointers and References]] develops detection and prevention; this note only fixes why the language performs no such check at all.

> [!trap] Calling an overridable function from a base's constructor or destructor never reaches the derived override
> This is not a bug to work around case by case — it is what `[class.cdtor]` requires, because the derived part genuinely isn't there yet (construction) or is already gone (destruction). Treat any virtual call reachable from a constructor or destructor as calling *that class's own* version, full stop. See [[Virtual Functions]].

> [!ub] Reusing an object's storage without running its destructor is fine only for trivial destructors
> Example 2 (trivial `Counter`) is well-defined; Example 3 (`Loud`, holding a `std::string`) is undefined the moment the skipped destructor would have implicitly fired. [[Placement new and Manual Lifetime]] is the full treatment of doing this deliberately and safely — it always ends with an explicit destructor call before the storage is reused or released.

## Evolution

See [[Map — Evolution of C++]] for the language-wide timeline.

| Standard | Change | Why |
|---|---|---|
| **C++98** | Object lifetime already has its own dedicated clause, with substantially today's rule: begins after storage-and-initialization, ends at destructor call / object destruction / storage reuse | The object model needed an exact, load-bearing boundary from the moment "object" itself was formalized ([[The C++ Object Model — What an Object Is]]) |
| C++11 | [[Value Categories|Value categories]] give the *compiler* a compile-time signal (xvalue) tied to an object's *imminent* lifetime end, for move semantics; `[basic.life]`'s own wording is substantively unchanged | "Expiring" became something overload resolution could act on — but *when* lifetime actually ends stayed a runtime fact, never revised by an expression's category |
| **C++20** | *Implicitly created objects* (P0593R6) extend "lifetime begins" to storage an implementation populates with no `new`-expression or declaration at all — e.g., after `std::memcpy` into a `std::byte` buffer | Gave long-standing low-level idioms (`malloc`-then-populate, byte-copying a struct) a defined lifetime story instead of relying on undefined behavior compilers happened not to punish |
| C++26 (working draft) | `[class.cdtor]`'s virtual-call carve-out is extended to cover contract-assertion evaluation (postconditions of a constructor, preconditions of a destructor) alongside ordinary virtual calls | Contracts can themselves invoke virtual functions on the object under construction; eel.is tracks this working-draft text, not yet C++23 |

## Connections

- **Prerequisites:** [[Storage Duration]] — the outer clock this note's lifetime nests inside · [[The C++ Object Model — What an Object Is]] — lifetime is one of the six properties every object has.
- **Enables:** [[References]] → [[Pointers]] (every access path's contract is "the target's lifetime hasn't ended") → [[Virtual Functions]] (the `[class.cdtor]` carve-out Example 1 demonstrates) → [[Constructors]] (what "initialization is complete" actually requires).
- **Siblings:** [[Value Categories]] (an xvalue signals an imminent end to lifetime, at compile time, without changing when it actually happens) · [[Temporaries and Lifetime Extension]] (a reference can stretch a temporary's lifetime to its own, the one case where the clocks are deliberately tied together).
- **Explains:** [[Dangling Pointers and References]] · [[Placement new and Manual Lifetime]] (the deliberate, safe version of Examples 2–3).
- **Domain:** [[Map — Objects, Memory & Lifetime]].
- **Practice:** *Continuum #11 Pointer & Array Internals Lab* — print an object's address before construction, immediately after construction, and immediately after destruction, and confirm the *bytes* are unmoved even though the *object* the middle print saw no longer exists at the third.

## Check Yourself

> [!quiz]- What two conditions must both hold for an object's lifetime to begin, and which one is easy to forget?
> Storage of the right size and alignment must exist, **and** its initialization (if any) must be complete — `[basic.life]` ¶2. The second condition is the one people forget: allocating or declaring storage is not enough by itself; even a no-op default-initialization of a trivial type has to formally "complete" first.

> [!quiz]- Why does `[class.cdtor]` resolve a virtual call from `~Base()` to `Base`'s own override, rather than the most-derived one?
> Because by the time `~Base()`'s body runs, `~Derived()` has already finished: the `Derived` part of the object has already ended its lifetime. Calling `Derived::announce` would need state that no longer exists, so the Standard defines the call to resolve within the class currently under destruction — see Example 1 and its assembly evidence in Under the Hood.

> [!quiz]- Predict: after `new (p) Counter{99};` reuses `c`'s storage (Example 2), is `&c == p` still `true`, and why doesn't this need `std::launder`?
> Yes. `[basic.life]` ¶9–10: the new `Counter` is *transparently replaceable* by the old one (same type, same non-`const` storage, fully overlapping), so the old name and pointer automatically refer to the new object once its lifetime starts. `std::launder` is only needed when transparent replaceability's conditions (matching type, non-`const`, exact overlap) don't hold.

## Sources

- Primer §6.1.1 "Local Objects" (pp. 204–206): the C++11-era, pre-formalized definition of lifetime as the span of a program's execution during which an object exists, and the automatic/local-static split this note's Mechanics table tightens into `[basic.life]`'s exact wording.
- Tour §1.5 "Scope and Lifetime" (p. 10): an object is built by construction before first use and torn down at the end of its scope, with a `new`-created object's span tied to an explicit `delete` instead — the modern Tour's compressed version of the same rule.
- PPP §15.8 "The `this` pointer" (ch. 15 "Class Interfaces"): a destructor runs implicitly at the same moment a constructor ran implicitly at creation, once an object's scope ends — the pedagogical framing this note formalizes.
- cppreference, *Object lifetime*: https://en.cppreference.com/w/cpp/language/lifetime
- Draft standard `[basic.life]`: https://eel.is/c++draft/basic.life — the exact begin/end conditions, storage-reuse and transparently-replaceable rules, and the non-trivial-destructor UB case (Example 3).
- Draft standard `[class.cdtor]`: https://eel.is/c++draft/class.cdtor — virtual calls, `dynamic_cast`, and `typeid` during construction/destruction (Example 1).
- WG21 P0593R6, *Implicit creation of objects for low-level object manipulation*: https://wg21.link/p0593r6 — the C++20 change cited in Evolution.
