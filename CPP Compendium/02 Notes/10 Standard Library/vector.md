---
id: std-vector
title: vector
aliases:
- "std::vector"
type: concept
domain: D10
tier: 1
status: draft
standard: C++98
prereqs:
- "[[STL Architecture — Containers, Iterators, Algorithms]]"
related:
- "[[Iterators]]"
- "[[The Algorithms Library]]"
- "[[How vector Grows — Capacity and Amortized Cost]]"
- "[[Sequence Containers Compared]]"
practice:
- 7
- 12
tags:
- type/concept
- domain/d10
- tier/1
- tension/abstraction-vs-control
- tension/safety-vs-performance
- std/c++98
- std/c++11
- std/c++17
- std/c++20
created: 2026-09-26
updated: 2026-09-26
---

# vector

> [!essence]
> **`std::vector<T>`** is a growable sequence of `T` that owns one contiguous heap buffer and manages it through RAII: indexing is as fast as a hand-written array, growth is amortized O(1), and the destructor frees the buffer with no help from the caller. It is the standard library's answer to "give every program the same tested, resizable array" instead of letting each one hand-roll its own.

## The Problem

A C++ built-in array cannot grow. `int a[n]` fixes `n` at compile time (or, for `new T[n]`, at the moment of allocation); there is no operation that means "now hold one more element." Yet almost no real program knows its element count in advance — a phone book fills up as lines are read, a log grows as events occur (Tour §12.2, p. 158). Something has to sit between "the hardware only understands fixed blocks of bytes" (PPP ch. 15 §15.1, ch. 15 "Vector and Free Store") and "the program needs a sequence that grows."

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint:** Memory is a sequence of bytes with no built-in notion of "resize this block." A fixed-size array can't be extended, and the elements a program will need are usually not known until run time (PPP ch. 15 §15.1).
> 2. **Consequence:** Left to solve this alone, every program (or every team) hand-rolls its own dynamic array: a pointer, a manually tracked size, `new`/`delete` calls at every growth point. Each version is separately buggy, separately tested, and incompatible with every other team's version — the same problem [[Map — Standard Library]] names at the whole-domain level.
> 3. **Requirement:** The shared answer must (a) behave like an ordinary value — copyable, assignable, self-cleaning, no manual `delete` — (b) store elements contiguously, so indexing and iteration cost exactly what a hand-written array would, and (c) let the caller grow it one element at a time without personally managing reallocation.
> 4. **Design:** `std::vector<T>` is a class template holding a **handle** — a pointer to the first element plus a size and a capacity — that owns a single heap-allocated buffer through RAII ([[RAII]]): the destructor frees it, no `delete` required anywhere in user code. The handle exposes the buffer through `[]`, iterators and `data()`, so it slots directly into the iterator protocol ([[STL Architecture — Containers, Iterators, Algorithms]]) and into any code that expects a raw pointer.
> 5. **Price:** Because every element must stay in *one* contiguous block, growing past the current capacity means allocating a new, bigger block and relocating every element into it — and every pointer, reference and iterator into the old block is left pointing at freed memory. The zero-overhead promise (Under the Hood) is bought with this one sharp edge, examined fully in [[How vector Grows — Capacity and Amortized Cost]] and [[Iterator Invalidation]].

> [!tension] abstraction ⟷ control
> `vector` is supposed to cost nothing beyond a hand-written dynamic array — that is the standard library's whole bet (Tour §9.2, p. 121). It keeps that promise by giving you the same contiguous buffer and the same pointer arithmetic underneath, but the abstraction only holds as long as you don't outlive it: reallocation is invisible in the source but very visible the moment an old pointer is dereferenced.

> [!tension] safety ⟷ performance
> `operator[]` performs no bounds check — reading `v[i]` for `i >= size()` is undefined behavior, not an exception. `.at(i)` checks and throws `std::out_of_range` instead. `vector` deliberately offers both, because a hot inner loop and an untrusted input path have different needs, and the library refuses to pick one answer for you.

## Mental Model

> [!model] The manifest and the warehouse — and where it breaks
> A `vector<T>` object is a small **manifest**: a pointer to the goods, a count of how many are there, and a count of how much room there is. The actual goods sit in a separate **warehouse** — the heap buffer — that the manifest owns. Copying the manifest (`vector<int> b = a;`) rents a *new* warehouse and duplicates every item into it: `a` and `b` are now independent. Moving the manifest (`vector<int> c = std::move(a);`) hands over the *same* warehouse and its address: `a` is left with an empty manifest, in O(1), because nothing was actually copied.
> **Where it breaks:** an ordinary warehouse doesn't relocate itself. `vector`'s does — silently, whenever a `push_back` needs more room than the current buffer has. Any note you had stuck to a shelf (a pointer, reference or iterator into the old buffer) now refers to a warehouse that has been torn down. The manifest survives every reallocation; nothing that pointed *into* the old buffer does.

```mermaid
flowchart LR
    V["v : vector#lt;int#gt;<br/><i>fixed-size handle</i>"]:::focus
    BUF["heap buffer<br/><i>owned; may relocate</i>"]:::mech
    CP["vector#lt;int#gt; b = v;<br/><i>copy</i>"]:::concept
    BUF2["new, independent buffer"]:::good
    MV["vector#lt;int#gt; c = std::move(v);<br/><i>move</i>"]:::concept

    V -->|owns| BUF
    CP -->|allocates + copies every element| BUF2
    MV -->|steals the same buffer, O(1)| BUF

    classDef concept fill:#312e81,stroke:#818cf8,color:#eef2ff
    classDef mech    fill:#134e4a,stroke:#2dd4bf,color:#f0fdfa
    classDef focus   fill:#78350f,stroke:#fbbf24,color:#fffbeb
    classDef good    fill:#14532d,stroke:#4ade80,color:#f0fdf4
```

## Mechanics

| Situation | Rule | Example |
|---|---|---|
| Construct with a count | Parentheses request "*n* of a value" | `vector<int> v(5, 0)` → five zeros |
| Construct with a list of values | Braces request "exactly these values," and win when both readings are possible | `vector<int> v{5, 0}` → the two values `5, 0` |
| Read an element | `[]` is O(1) and unchecked (UB out of range); `.at()` is O(1) and checked (throws) | `v[i]` vs `v.at(i)` |
| Grow by one | `push_back`/`emplace_back` are amortized O(1): occasional O(n) reallocations, averaged over many calls, cost O(1) each | `v.push_back(x)` |
| Insert or erase in the middle | O(n): every element after the point must shift | `v.insert(v.begin(), x)` |
| Copy a vector | Allocates a new buffer, copies every element: O(n) | `vector<int> b = a;` |
| Move a vector | Takes the other's buffer directly: O(1) | `vector<int> b = std::move(a);` |

> [!standard] What the Standard actually promises
> `std::vector` meets the requirements of *Container*, *ReversibleContainer*, *AllocatorAwareContainer* (C++11) and *SequenceContainer*, and — for any element type other than `bool` — of a *ContiguousContainer* (C++17) (`[vector.overview]` ¶2). Complexity is specified, not merely conventional: random access is constant time; insertion or removal at the end is amortized constant time; insertion or removal elsewhere is linear in the distance to the end (`[vector.overview]` ¶1, cppreference *Complexity* summary). "Amortized" here has a precise meaning: the *total* cost of *n* `push_back` calls is O(n), even though a handful of those calls individually pay for a reallocation.

## Under the Hood

> [!machine] The handle costs exactly one extra load
> `operator[]` on a `vector<int>&` and on a raw `int*` compile to almost the same instructions; the only difference is the one load that follows the handle to find the buffer (GCC, `-O2`, x86-64):
> ```nasm
> at(int*, int):                                   ; raw pointer: raw[i]
>         movsx rsi, esi
>         mov   eax, DWORD PTR [rdi+rsi*4]
>         ret
> at(std::vector<int>&, int):                       ; vector: v[i]
>         mov   rax, QWORD PTR [rdi]                ; ① load the buffer pointer out of the handle
>         movsx rsi, esi
>         mov   eax, DWORD PTR [rax+rsi*4]           ; ② identical indexed load from there on
>         ret
> ```
> That one extra `mov` is the entire cost of "resizable" over "fixed": everything downstream of the handle is exactly the array access a programmer would write by hand.

Contiguity is also why iterating a `vector` is fast on a real machine, not just on paper: reading `v[i]` pulls a whole cache line — typically 64 bytes, or 16 `int`s — into cache, so `v[i+1]`, `v[i+2]`, … are very likely to already be there when you ask (Pikus ch. 4, p. 113, on why sequential access patterns dominate the memory hierarchy's performance). A `vector<vector<T>>` gets none of this for the outer structure: each inner `vector` is its own separately allocated buffer, scattered across the heap (Tour §12.2.1, p. 160) — one reason [[Map — Standard Library|the domain]] treats "one flat buffer vs. a buffer of buffers" as a real design decision, not a style preference.

## In Code

**1 · Contiguity is a checkable fact, not a metaphor**

```cpp
#include <cassert>
#include <cstddef>
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v{10, 20, 30, 40};
    for (std::size_t i = 0; i + 1 < v.size(); ++i) {
        const int* here = &v[i];
        const int* next = &v[i + 1];
        assert(next - here == 1);                                     // ①
        assert(reinterpret_cast<const char*>(next) -
               reinterpret_cast<const char*>(here) == sizeof(int));    // ②
    }
    std::cout << "contiguous: stride == " << sizeof(int) << " bytes\n";
}
// expect: contiguous: stride == 4 bytes
```
1. Pointer arithmetic on `int*` counts in units of `int`: adjacent elements differ by exactly `1`.
2. Recast to `char*` to measure in bytes instead: the gap is exactly `sizeof(int)`, with nothing else — no per-element header, no padding — in between. This is what "contiguous" cashes out to at run time.

**2 · Copying duplicates the buffer; the two vectors are independent afterward**

```cpp
#include <iostream>
#include <vector>

int main() {
    std::vector<int> original{1, 2, 3};
    std::vector<int> copy = original;    // ①
    copy[0] = 99;                        // ②
    std::cout << original[0] << ' ' << copy[0] << '\n';
}
// expect: 1 99
```
1. The copy constructor allocates its own buffer and copies every element into it — the "rent a new warehouse" step of the Mental Model.
2. Mutating `copy` cannot affect `original`: there is no shared state left after the copy, unlike a raw pointer that would still point at the same memory.

**3 · One algorithm, unmodified, over vectors of two unrelated element types**

```cpp
#include <algorithm>
#include <iostream>
#include <string>
#include <vector>

template <typename T>
void print_sorted(std::vector<T> v) {          // ①
    std::sort(v.begin(), v.end());              // ②
    for (const auto& x : v) std::cout << x << ' ';
    std::cout << '\n';
}

int main() {
    print_sorted(std::vector<int>{3, 1, 2});
    print_sorted(std::vector<std::string>{"pear", "fig", "date"});
}
// expect: 1 2 3
// expect: date fig pear
```
1. `print_sorted` is written once, against `vector<T>` for any `T` that is comparable.
2. `std::sort` never mentions `vector`; it only asks its argument iterators for random access. This is [[STL Architecture — Containers, Iterators, Algorithms|the iterator seam]] paying off on the concrete container everything else in the domain is checked against.

## Pitfalls

> [!ub] Reallocation invalidates every pointer, reference and iterator into the old buffer
> This is the Mental Model's "where it breaks" made concrete: `push_back`, `insert`, `reserve` or `resize` can each trigger a move to a bigger buffer, and once that happens, anything that referred *into* the old one is dangling. Using it is undefined behavior — the program will often appear to work and then fail somewhere else entirely. Full mechanics and detection in [[Iterator Invalidation]] and [[Dangling Pointers and References]].

> [!trap] `[]` trusts you; `.at()` doesn't
> `v[i]` for an out-of-range `i` is undefined behavior — no exception, sometimes no crash, just a read of whatever happens to be at that address. Reach for `.at()` at a trust boundary (user input, file data, a network message) and reserve `[]` for indices you have already validated.

> [!trap] A `vector<Base>` cannot hold a `Derived` politely
> Every element occupies the same fixed-size slot in the buffer, so a `vector<Shape>` can only ever store `Shape`-sized data — assigning a `Circle` into it copies just the `Shape` part (Tour §12.2.1, p. 160, warns against exactly this). Store `unique_ptr<Shape>` or another pointer type when polymorphic behavior is needed. See [[Object Slicing]].

## Evolution

| Standard | Change | Why |
|---|---|---|
| **C++98** | `vector` enters the library as the STL's default sequence container | Replace one hand-rolled dynamic array per program with a single, tested, contiguous one |
| C++11 | Move constructor/assignment; initializer-list construction; `emplace_back`; `data()`; `cbegin`/`cend` | Returning or passing a `vector` by value stops meaning "copy every element"; construction and in-place building get direct syntax |
| C++17 | Class template argument deduction (`vector v{1,2,3}`); `std::pmr::vector`; formally named a *ContiguousContainer* | Less boilerplate at the call site; pluggable allocators; the "elements are adjacent" guarantee becomes something code can rely on by name |
| **C++20** | `constexpr` vector (with limits); `std::erase`/`std::erase_if`; `<=>` for comparisons | Push container use into compile-time evaluation; retire the erase–remove idiom's boilerplate for the common case |
| C++23 | `vector(std::from_range, r)`, `append_range`, `insert_range`, `assign_range` | Build from and extend with any range, not only an iterator pair |

## Connections

- **Prerequisites:** [[STL Architecture — Containers, Iterators, Algorithms]] — `vector` is the concrete case every claim there is checked against.
- **Enables:** [[Iterators]] · [[The Algorithms Library]] · [[How vector Grows — Capacity and Amortized Cost]] · [[Iterator Invalidation]].
- **Siblings:** [[Sequence Containers Compared]] (when *not* to reach for `vector`).
- **Hazards:** [[Iterator Invalidation]] · [[Dangling Pointers and References]] · [[Object Slicing]].
- **Lookup layer:** [[Header — vector]] for the full member reference, task recipes and the growth/invalidation tables in detail.
- **Domain:** [[Map — Standard Library]].
- **Practice:** *Continuum #12 Build-Your-Own Dynamic Array* — implement the handle-and-buffer split yourself and watch where it agrees with the asm above. *Continuum #7 Word & Text Analyzer* — `vector` as the working storage for tokenized text.

## Check Yourself

> [!quiz]- What does a `std::vector<T>` object itself actually store, and where do its elements live?
> The `vector` object is a small, fixed-size handle (a pointer, a size and a capacity). The elements live in a separate, contiguous heap buffer that the handle owns and frees in its destructor.

> [!quiz]- Why is `push_back` called "amortized O(1)" instead of just "O(1)"?
> Most calls are O(1): there's room, so the new element is placed directly. Occasionally a call must reallocate and copy/move every existing element, costing O(n). Spread over *n* calls, the total work is still O(n), so the *average* cost per call is O(1) — but any single call can be the expensive one.

> [!quiz]- `std::vector<int> v{1,2,3}; int* p = &v[0]; v.push_back(4); v.push_back(5); /* ... */ std::cout << *p;` — is this guaranteed to print `1`?
> No. Each `push_back` may reallocate. If either call moves the buffer, `p` now points into freed memory, and dereferencing it is undefined behavior — it might print `1`, might print something else, might crash. The only way to know is to check whether `capacity()` had enough room, and even then, relying on it is the pitfall this note names.

> [!quiz]- `vector<int> v(3, 7)` and `vector<int> v{3, 7}` — what does each produce, and why do they differ?
> `v(3, 7)` uses parentheses, which is a "count and value" construction: three elements, each `7`. `v{3, 7}` uses braces, which prefer list initialization whenever the braced values could be a list of elements: two elements, `3` and `7`.

## Sources

- Primer §3.3 "Library vector Type" (p. 96) and "List Initializer or Element Count?" (p. 98): construction, template instantiation, and the braces-vs-parentheses distinction used in Mechanics.
- Tour §12.2 "vector" (pp. 158–160): the handle-plus-buffer design, `push_back`'s amortized cost, and the warning against storing polymorphic objects by value.
- PPP §15.2 "vector basics" (ch. 15 "Vector and Free Store"): building a `Vector` from a pointer, a size and free-store allocation, from first principles.
- Pikus ch. 4 "Memory Architecture and Performance" (p. 113): why contiguous, sequentially accessed data wins on real cache hierarchies.
- cppreference, *`std::vector`*: https://en.cppreference.com/w/cpp/container/vector
- Draft standard `[vector.overview]` and `[container.reqmts]`: https://eel.is/c++draft/vector.overview · https://eel.is/c++draft/container.reqmts
- C++ Core Guidelines SL.con.2, "Prefer using STL `vector` by default unless you have a reason to use a different container": https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
