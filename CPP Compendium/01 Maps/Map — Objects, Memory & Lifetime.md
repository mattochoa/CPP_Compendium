---
id: map-d04
title: Map — Objects, Memory & Lifetime
type: map
domain: D04
tier: 1
status: reviewed
standard: C++98
prereqs:
- "[[Map — What C++ Is]]"
related:
- "[[Map — Ownership & Move Semantics]]"
- "[[Map — Types & Values]]"
- "[[Map — Functions]]"
- "[[Map — Performance & the Machine]]"
practice:
- 11
- 12
- 13
tags:
- type/map
- domain/d04
- tier/1
- tension/safety-vs-performance
- tension/value-vs-identity
created: 2026-09-23
updated: 2026-09-25
reviewed: 2026-09-23
score: 19
rubric:
  accuracy: 3
  first_principles: 3
  clarity: 3
  depth: 2
  visual: 3
  code: 3
  integration: 2
---

# Map — Objects, Memory & Lifetime

> [!essence]
> *Where does an object live, how long does it live, and who can reach it?* Every C++ program answers these three questions for every object. It answers some of them explicitly and the rest by accident. This domain makes the answers explicit, and nearly every serious C++ bug is a wrong answer to one of them.

## Why This Domain Exists

[[Map — What C++ Is|The previous domain]] established that C++'s contract binds only *observable behavior*, leaving everything else — including where things live and how long they last — for the implementation to decide within rules the Standard still pins down. A program computes with **objects**: regions of storage that hold values of a [[What a Type Is|type]] ([[The C++ Object Model — What an Object Is]]). Take away a language's conveniences, and three facts remain that any language must handle:

> [!principle] The three questions, from first principles
> 1. **Where?** An object needs *storage*: bytes somewhere. Storage comes from different places with different costs. The stack is almost free to allocate from but limited to a scope. The heap is flexible but needs an allocator call. Static storage lasts forever but exists only once. So C++ exposes the choice as [[Storage Duration]].
> 2. **How long?** Storage alone is not an object. An object's [[Object Lifetime|lifetime]] begins when its initialization completes and ends when its destructor starts (or its storage is released). Between those moments its value is meaningful; outside them it isn't, even if the bytes are still there.
> 3. **Who can reach it?** Code reaches objects through **names** (bound at compile time), **references** (aliases) and **pointers** (addresses held in other objects) ([[Pointers vs References]]). Each is a claim that *this object is alive right now*, and the language does not check that claim.
>
> Most languages hide the first two answers behind a garbage collector and make the third always safe. C++ exposes all three because hiding them costs time, memory and predictability. The domain's content is the set of rules, tools and idioms that let you give correct answers at zero overhead.

## The Core Tension

> [!tension] safety ⟷ performance
> C++ doesn't track who points at what, doesn't check bounds, and doesn't collect garbage. Every object costs exactly its bytes, and every access is a machine address. The price: **lifetime errors are undefined behavior**, not exceptions ([[Undefined Behavior]]). The domain's answer is to make safety *structural* rather than *checked*. Scope-bound lifetimes and [[RAII]] ensure release; clear ownership ([[Ownership — Who Releases What]]) and non-owning observers of shorter lifetime ensure access stays valid. Sanitizers catch what escapes.

> [!tension] value ⟷ identity
> An object is both a *value* (its contents, which can be copied or moved) and an *identity* (its address, which others may hold). Copying preserves the value and creates a new identity. References share the identity. [[Value Categories]] tell the compiler, expression by expression, whether identity still matters or the value may be pilfered.

## Concept Map

Arrows read "is needed to understand".

```mermaid
flowchart LR
    OM["Object Model"]:::concept --> SD["Storage Duration"]:::concept
    PML["Process Memory Layout"]:::mech --> SD
    SD --> LT["Object Lifetime"]:::focus
    LT --> INIT["Forms of Initialization"]:::concept
    LT --> VC["Value Categories"]:::concept
    LT --> TMP["Temporaries &<br/>Lifetime Extension"]:::mech
    OM --> REF["References"]:::concept
    OM --> PTR["Pointers"]:::concept
    PTR --> ARR["Arrays & Decay"]:::mech
    PTR --> DYN["new and delete"]:::mech
    REF --> DANG["Dangling Pointers<br/>and References"]:::danger
    PTR --> DANG
    LT --> DANG
    DYN --> LEAK["Memory Leaks"]:::danger
    DYN --> RAII["RAII (D07)"]:::good
    VC --> MOVE["Move Semantics (D07)"]:::good
    classDef concept fill:#312e81,stroke:#818cf8,color:#eef2ff
    classDef mech fill:#134e4a,stroke:#2dd4bf,color:#f0fdfa
    classDef focus fill:#78350f,stroke:#fbbf24,color:#fffbeb
    classDef danger fill:#7f1d1d,stroke:#f87171,color:#fef2f2
    classDef good fill:#14532d,stroke:#4ade80,color:#f0fdf4
```

**Lifetime** is the hub. Storage feeds into it; initialization, value categories and temporaries elaborate it; the hazards are violations of it; and the next domain ([[Map — Ownership & Move Semantics]]) automates it.

## Learning Route

1. [[The C++ Object Model — What an Object Is]]: fixes the vocabulary (object, storage, type, value). Everything after depends on it.
2. [[Process Memory Layout — Stack, Heap, Static]]: the *real-machine* picture, so the abstract rules have something concrete to attach to.
3. [[Storage Duration]]: the Standard's four answers to *where* (automatic, static, thread, dynamic).
4. [[Object Lifetime]]: *how long*, the hub of the domain.
5. [[References]] → [[Pointers]] → [[Pointers vs References]]: *who can reach it*, and the contract each access path makes.
6. [[Dynamic Memory — new and delete]]: manual lifetime, and the reason [[RAII]] exists.
7. [[Dangling Pointers and References]] and [[Memory Leaks]]: the two ways the answers go wrong: an observer too long, an owner never ending.
8. [[Value Categories]] → [[Temporaries and Lifetime Extension]]: the expression-level view of lifetime that powers move semantics.
9. [[The Forms of Initialization]]: exactly when and how a lifetime begins.
10. Advanced layer: [[Object Representation, Padding and Layout]] (including hidden members such as the [[Virtual Dispatch — vptr and vtable|vptr]]) → [[Strict Aliasing and Type Punning]] → [[Placement new and Manual Lifetime]] → [[Allocators and pmr Memory Resources]]. What that layout costs on real hardware — cache lines, false sharing, allocation overhead — is [[Map — Performance & the Machine|a later domain's]] question, not this one's.

## Key Ideas

1. **An object's lifetime and its storage are governed by two different clocks.** [[Object Lifetime|An object's lifetime]] begins once storage of the right size and alignment exists *and* initialization completes, and ends when a class type's destructor call starts or a non-class object is destroyed (`[basic.life]`); its *storage* is reclaimed only later — at scope exit, at `delete`, or at program end (`[basic.stc.general]`) — so a stale pointer can still address allocated-but-dead bytes for a while after its target's lifetime is already over.
2. **Storage duration picks the *where*; scope or ownership picks the *when*.** [[Storage Duration]] names exactly four categories — automatic, static, thread and dynamic (`[basic.stc]`) — and it is the automatic/dynamic pair that competes in most designs: automatic objects are destroyed, in reverse construction order, at the end of their block, while a dynamic object dies at whatever moment the owning code chooses to call `delete`.
3. **Every pointer or reference is an unchecked claim that its target is alive.** Dereferencing one after its referent's lifetime has ended is undefined behavior the instant it happens, independent of whether the underlying *storage* has actually been reused yet ([[Dangling Pointers and References]]); the language performs no liveness check at all, so the claim is kept honest only by the programmer nesting the observer's scope inside the observed object's.
4. **Ownership must be singular and visible.** Exactly one party may call `delete` on — or let a destructor run over — a given resource; [[unique_ptr]] turns that party into a compile-time-checked type instead of a comment, which is why code that merely *looks* at an object should take a raw observer ([[Owning vs Observing Pointers]]) rather than a smart pointer that implies it might delete.
5. **Lifetime errors are undefined behavior, not a checked failure.** Once code dereferences past a lifetime's end, the abstract machine imposes zero requirements on the rest of the execution ([[Undefined Behavior]] — the same contract [[Map — What C++ Is|the previous domain]] derives); the bug typically doesn't fail at the point of the mistake, which is why sanitizers (ASan's `heap-use-after-free`, `stack-use-after-scope`) catch far more than reading the code ever will, and why this domain prefers designing the error out structurally over catching it at run time.
6. **Categories are about expressions; lifetimes are about objects.** [[Value Categories]] classify an *expression*, at compile time, as a glvalue, prvalue or xvalue — a statement about whether the object it denotes may safely be moved from — and that classification is fixed by the expression's grammatical form alone, never revised by anything that happens to the denoted object's lifetime while the program runs.
7. **Most memory management should be invisible.** A `std::vector`, a [[unique_ptr]] or a [[shared_ptr and Reference Counting|shared_ptr]] each wrap exactly one `new`/`delete` pair (or allocator call) inside their own constructor and destructor, so code that composes these types calls neither directly — [[RAII]] applied specifically to memory, and this domain's general safety-versus-performance answer made concrete.

| Idea | Developed in |
|---|---|
| Objects vs storage | [[The C++ Object Model — What an Object Is]] · [[Object Lifetime]] |
| Where objects live | [[Storage Duration]] · [[Process Memory Layout — Stack, Heap, Static]] |
| Access paths and their contracts | [[Pointers vs References]] · [[nullptr and Null Pointers]] |
| Failure modes | [[Dangling Pointers and References]] · [[Memory Leaks]] · [[Double Free and Mismatched new-delete]] · [[Reading Uninitialized Variables]] |
| Expression-level lifetime | [[Value Categories]] · [[Temporaries and Lifetime Extension]] |
| Structural safety | [[RAII]] · [[Memory Safety in C++ — Threats and Defenses]] |

## Index

<!-- cc:auto:domain-index:D04 -->
**Tier 1 · Foundational**
- ◐ [[The C++ Object Model — What an Object Is]] · *concept*
- ● [[Process Memory Layout — Stack, Heap, Static]] · *mechanism*
- ◐ [[Storage Duration]] · *concept*
- ◐ [[Object Lifetime]] · *concept*
- ◐ [[References]] · *concept*
- ◐ [[Pointers]] · *concept*
- ◐ [[Dynamic Memory — new and delete]] · *mechanism*
- ○ [[Reading Uninitialized Variables]] · *pitfall*
- ○ [[Pointer Arithmetic and Arrays]] · *mechanism*
- ● [[Pointers vs References]] · *comparison*
- ○ [[nullptr and Null Pointers]] · *concept*
- ○ [[Built-in Arrays and Array-to-Pointer Decay]] · *mechanism*
- ○ [[Memory Leaks]] · *pitfall*
- ● [[Dangling Pointers and References]] · *pitfall*

**Tier 2 · Proficient**
- ● [[Value Categories]] · *concept*
- ○ [[The Forms of Initialization]] · *comparison*
- ○ [[Double Free and Mismatched new-delete]] · *pitfall*
- ○ [[Temporaries and Lifetime Extension]] · *mechanism*
- ○ [[C-Style Strings]] · *concept*
- ○ [[Object Representation, Padding and Layout]] · *mechanism*
- ○ [[Memory Safety in C++ — Threats and Defenses]] · *concept*
- ○ [[Empty Base Optimization]] · *mechanism*

**Tier 3 · Advanced**
- ○ [[Strict Aliasing and Type Punning]] · *pitfall*
- ○ [[Trivial, Standard-Layout and Aggregate Types]] · *concept*
- ○ [[Placement new and Manual Lifetime]] · *mechanism*

**Tier 4 · Expert**
- ○ [[Allocators and pmr Memory Resources]] · *concept*

`████░░░░░░` 11/27 written · legend ○ planned ◐ draft ● reviewed ★ evergreen ⟲ revise
<!-- cc:end -->

## Sources

- Primer ch. 2 "Variables and Basic Types" (p. 31) and ch. 12 "Dynamic Memory" (p. 449): the rules, in C++11 terms.
- Tour ch. 1 "The Basics" §1.5 "Scope and Lifetime" (p. 9) and ch. 15 "Pointers and Containers" (p. 195): the modern discipline.
- PPP ch. 15 "Vector and Free Store" and ch. 16 "Arrays, Pointers, and References": memory built up from first principles.
- Pikus ch. 4 "Memory Architecture and Performance" (p. 113): what the storage choice costs on real hardware.
- cppreference, *Object* · *Lifetime* · *Storage duration*: https://en.cppreference.com/w/cpp/language/object · https://en.cppreference.com/w/cpp/language/lifetime · https://en.cppreference.com/w/cpp/language/storage_duration
- Draft standard `[intro.object]`, `[basic.life]`, `[basic.stc]`: https://eel.is/c++draft/basic.life
- See [[Guide — C++ Primer (5th ed)]] for how this domain's Primer citations (ch. 2 and ch. 12) sit in the book, and which of its C++11-era claims about lifetime and dynamic memory need a modern-standard check first.
