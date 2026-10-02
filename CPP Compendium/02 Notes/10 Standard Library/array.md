---
id: std-array
title: array
aliases:
- "std::array"
type: concept
domain: D10
tier: 1
status: draft
standard: C++11
prereqs:
- "[[Built-in Arrays and Array-to-Pointer Decay]]"
- "[[STL Architecture — Containers, Iterators, Algorithms]]"
related:
- "[[vector]]"
- "[[Header — array]]"
- "[[span]]"
practice:
- 4
tags:
- type/concept
- domain/d10
- tier/1
- tension/compile-time-vs-run-time
- tension/abstraction-vs-control
- std/c++11
- std/c++17
- std/c++20
created: 2026-10-01
updated: 2026-10-01
---

# array

> [!essence]
> **`std::array<T,N>`** is a fixed-size sequence of `N` elements of type `T` that directly *contains* its elements — no heap buffer, no handle, no decay to a pointer — so it is exactly as fast and exactly as large as the built-in array it replaces, while behaving like an ordinary, copyable, container-interface-bearing value.

## The Problem

A built-in array `T arr[N]` has no member that stores "the address of element 0": that address is simply where `arr` itself lives. This is efficient but costly in a different way — almost every operation C++ defines (arithmetic, comparison, passing to a function) works on a single address, not on a 20-byte aggregate, so the compiler silently decays `arr` to `T*` wherever one is needed ([[Built-in Arrays and Array-to-Pointer Decay]]). That conversion discards `N`, and a raw array has no copy assignment at all: `int a[3]; int b[3]; a = b;` does not compile (PPP §16.1, ch. 16, calls this "the major problem with pointers to arrays" — once decayed, nothing downstream can recover how many elements were meant).

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint.** A fixed-size, compile-time-sized sequence needs to be exactly as cheap as a raw array — no extra indirection, no dynamic allocation — because that is the entire reason to choose it over [[vector]] in the first place (Tour §15.3.1, p. 202: "no overhead — time or space — involved in using an array compared to using a built-in array").
> 2. **Consequence.** But a raw array can't be assigned, can't report its own size to an algorithm, and silently decays — losing `N` — the moment it's passed to most functions (Primer §9.2.4, p. 336, "Library arrays Have Fixed Size").
> 3. **Requirement.** Something must behave like the raw array in storage and cost, yet like an ordinary library container in interface: copyable with `=`, queryable with `.size()`, walkable with `begin()`/`end()` so every [[The Algorithms Library|STL algorithm]] already works on it.
> 4. **Design.** `std::array<T,N>` is an **aggregate** whose only non-static data member is, in effect, a raw `T[N]` (cppreference: "the same semantics as a struct holding a C-style array `T[N]` as its only non-static data member"). It layers the [[STL Architecture — Containers, Iterators, Algorithms|Container interface]] — `size()`, `at()`, `begin()`/`end()`, `operator==` — directly onto that storage, with no separate buffer to own or free. Because it is a distinct class type rather than a bare array, it gets real assignment and real copy construction for free (Primer §9.2.4, p. 338: "Unlike built-in arrays, the library `array` type does allow assignment").
> 5. **Price.** Nothing is bought for free. `N` moves from "a run-time fact a raw array also forgets" to "part of the type itself" — `array<int,3>` and `array<int,4>` are unrelated types, so a function that must work for any size needs a template, not a single signature. And because there is no separate buffer to swap *pointers* to, `array::swap` is linear in `N`, the one place the "it's just the raw array, dressed up" design shows through as a real cost difference from [[vector]]'s O(1) handle swap (cppreference: array satisfies *Container* and *ReversibleContainer* "except that... the complexity of swapping is linear").

> [!tension] compile-time ⟷ run-time
> `array<T,N>` resolves the tension in `vector`'s favor of the other side: `vector` carries its size as *data*, discoverable and changeable at run time; `array` carries its size as a *template argument*, fixed the moment the type is named and baked into every address computation the compiler ever does for it. You trade "can grow" for "the compiler knows exactly how big this is, always."

> [!tension] abstraction ⟷ control
> The whole point of `array` is that the abstraction (a container with `size()`, iterators, assignment) costs nothing over the raw storage it wraps (Under the Hood). The library keeps that promise only because `array` never allocates — the moment any operation needed heap storage, the zero-overhead claim would be gone, which is exactly why `array` offers no `push_back`.

## Mental Model

> [!model] The struct that *is* its array — and where the analogy still holds
> Picture writing this struct yourself:
> ```cpp
> template <class T, std::size_t N>
> struct RawWrapper { T elems[N]; };
> ```
> That is not a simplification — per cppreference, `std::array<T,N>` has exactly those semantics: one member, the raw array itself, with nothing else in the object. Indexing it, copying it, and taking its address all behave exactly as they would for `RawWrapper::elems`, because there is no handle sitting in between.
> **Where it holds up (unlike most analogies here):** there is no hidden warehouse the way there is for [[vector]]. `array<T,N>` really does live wherever it's declared — the stack frame, a class, static storage — exactly as `T[N]` would.

```text
 STACK (automatic storage)
┌──────────────────────────────┐
│ int raw[4]                    │   16 bytes, inline
│ [ 10 | 20 | 30 | 40 ]         │
├──────────────────────────────┤
│ std::array<int,4> a           │   16 bytes, inline — identical layout to raw[4]
│ [ 10 | 20 | 30 | 40 ]         │
├──────────────────────────────┤                           HEAP (dynamic)
│ std::vector<int> v            │   24-byte handle        ┌────────────────────┐
│  data ●───────────────────────┼────────────────────────▶│ [10|20|30|40]      │
│  size = 4, cap = 4            │                          └────────────────────┘
└──────────────────────────────┘
```

## Mechanics

| Situation | Rule | Example |
|---|---|---|
| Construct | Aggregate-initialize with up to `N` values; fewer initializers value-initialize the rest | `array<int,5> a{1,2}` → `{1,2,0,0,0}` |
| Default-construct, no braces | Elements are default-initialized — indeterminate for a built-in `T`, exactly like a raw array | `array<int,5> a;` → unspecified values |
| Default-construct, empty braces | `{}` forces value-initialization of every element | `array<int,5> a{};` → all zero |
| Read an element | `[]` is unchecked (UB out of range); `.at()` is checked, throws `std::out_of_range` | `a[i]` vs `a.at(i)` |
| Copy / assign | Works like any value type — unlike a raw array — but only between the *same* `array<T,N>` type | `array<int,3> b = a;` |
| Swap | Exchanges elements one by one: **O(N)**, not O(1) | `a.swap(b)` |
| Deduce the type (C++17) | `N` and `T` can both be deduced from the initializer | `array a{1,2,3};` → `array<int,3>` |
| Wrap a raw array (C++20) | `to_array` copies a `T[N]` into a new `array<T,N>`, deducing both | `auto a = std::to_array({1,2,3});` |

> [!standard] What the Standard actually says
> `array<T,N>` stores `N` elements of `T` such that `size() == N` is an invariant, and it is an aggregate list-initializable with up to `N` elements (`[array.overview]` ¶1–2). It meets the requirements of *Container* and *ReversibleContainer*, and — since C++17 — of *ContiguousContainer*, **except** that a default-constructed `array` is not empty when `N > 0`, and that swap is linear rather than constant (`[array.overview]` ¶3, cppreference). It only *partially* meets *SequenceContainer*: there is no `push_back`, `insert` or `erase`, because every one of those would require changing the number of elements the type itself fixes.

## Under the Hood

> [!machine] Indexing an `array` and a raw array compile to the identical instruction (GCC 11.4, `-O2`, x86-64 Linux)
> ```nasm
> at_raw(int*, int):                          ; raw[i]
>         movsx rsi, esi
>         mov   eax, DWORD PTR [rdi+rsi*4]
>         ret
> at_array(std::array<int, 8ul>&, int):       ; a[i]
>         movsx rsi, esi
>         mov   eax, DWORD PTR [rdi+rsi*4]
>         ret
> ```
> No extra load, no indirection: `a[i]` and `raw[i]` are the same memory access, because `array<int,8>` *is* the eight `int`s, passed by reference exactly as `int*` is. Contrast [[vector|vector's `operator[]`]], which must first load the buffer pointer out of its handle — the one extra instruction that is the entire cost of "resizable."

The linear `swap` is the same fact from the other side: because the object's storage and its contents are one and the same, swapping two `array`s has no handle to exchange — only `N` element-wise swaps, each one moving real data rather than reassigning a pointer.

## In Code

**1 · Same size, same layout, and no decay**

```cpp
#include <array>
#include <iostream>

int main() {
    std::array<int, 4> a{10, 20, 30, 40};
    int raw[4]{10, 20, 30, 40};

    static_assert(sizeof(a) == sizeof(raw));           // ①
    static_assert(sizeof(a) == 4 * sizeof(int));        // ②

    std::cout << "sizeof(a) == " << sizeof(a) << " bytes\n";
}
// expect: sizeof(a) == 16 bytes
```
1. `std::array<int,4>` and `int[4]` occupy identical storage — no handle, no padding, nothing extra.
2. Spelled out: exactly four `int`s, nothing else.

**✗ Unlike a raw array, `array` does not decay to a pointer:**
```cpp
// cc: ill-formed
#include <array>
int main() {
    std::array<int, 4> a{1, 2, 3, 4};
    int* p = a;   // error: no array-to-pointer decay for std::array
}
```
Where a raw array would silently convert, `array` refuses: it is a class type, not an array type, so [[Built-in Arrays and Array-to-Pointer Decay|the decay rule]] simply does not apply to it (PPP §16.5 makes the identical point: "`std::array<int,8> arr {...}; int* p = arr; // error (and that's good)`"). Reach `a.data()` for the raw pointer explicitly when a C-style interface needs one.

**2 · Copy assignment works — the one thing a raw array could never do**

```cpp
#include <array>
#include <iostream>

int main() {
    std::array<int, 3> original{1, 2, 3};
    std::array<int, 3> copy = original;    // ①
    copy[0] = 99;                           // ②
    std::cout << original[0] << ' ' << copy[0] << '\n';
}
// expect: 1 99
```
1. `array`'s copy constructor (compiler-generated, since it's an aggregate) copies every element into an independent object.
2. Mutating `copy` cannot affect `original` — the same independence [[vector|`vector`'s copy]] gives you, now without a heap allocation.

**3 · `array` plugs straight into algorithms and structured bindings**

```cpp
#include <algorithm>
#include <array>
#include <iostream>

int main() {
    std::array coords{3.0, 1.0, 4.0};              // ①
    std::sort(coords.begin(), coords.end());         // ②

    auto [x, y, z] = coords;                          // ③
    std::cout << x << ' ' << y << ' ' << z << '\n';
}
// expect: 1 3 4
```
1. Class template argument deduction (C++17): the braced initializer fixes both `T = double` and `N = 3` — no `<double, 3>` needed.
2. `std::sort` never mentions `array`; it only needs the random-access iterators every [[STL Architecture — Containers, Iterators, Algorithms|container in the domain]] provides.
3. Structured bindings decompose `coords` through its `tuple_size`/`tuple_element`/`get<I>` specializations (C++11) — the same tuple-like protocol that lets `pair` and `tuple` be destructured.

## Pitfalls

> [!trap] The size is part of the type — a generic function needs two template parameters, not one
> `array<int,3>` and `array<int,4>` are unrelated types with no common base. A function written as `void f(std::array<int,3>&)` rejects every other size outright; writing it generically needs `template <std::size_t N> void f(std::array<int,N>&)`. This is the direct cost of the compile-time ⟷ run-time trade the Mental Model names.

> [!trap] A bare `array<int,5> a;` is not zeroed
> Default construction default-initializes the elements — for a built-in `T`, that means indeterminate values, exactly as a raw array would leave them. Write `array<int,5> a{};` (empty braces) whenever you need every element value-initialized to `0`.

> [!ub] `front()`, `back()` and out-of-range `operator[]` are undefined behavior on an empty or overrun access
> For the special case `N == 0`, `begin() == end()` and calling `front()` or `back()` is undefined behavior (cppreference). `operator[]` performs no bounds check at any `N`; use `.at()` at a trust boundary. See [[Dangling Pointers and References]] and [[Buffer Overruns and Out-of-Bounds Access]] for the general shape of this hazard.

## Evolution

| Standard | Change | Why |
|---|---|---|
| **C++11** | `array<T,N>` introduced in `<array>`, with `tuple_size`/`tuple_element`/`get<I>` specializations | Give the raw array a container interface and a tuple-like protocol at zero cost, without changing its layout |
| C++14 | Core defect resolution (retroactive) removes the need for double braces (`{{1,2,3}}`) in most aggregate-initializations of `array` | The double-brace requirement was an artifact of treating `array` as "a struct containing an array," not an ergonomic choice |
| C++17 | Class template argument deduction; most member functions become `constexpr`; formally a *ContiguousContainer*; structured bindings (language feature) can decompose an `array` | Less boilerplate at the declaration site; compile-time use catches up to run-time use; the "contiguous" guarantee becomes something generic code can name |
| **C++20** | `to_array()`; iterators meet the full constexpr-iterator requirements; `<=>` replaces the six relational operators | Build an `array` from a raw array without hand-writing the size; push more `array` use into compile-time evaluation |

## Connections

- **Prerequisites:** [[Built-in Arrays and Array-to-Pointer Decay]] — the exact problem `array` is built to not have; [[STL Architecture — Containers, Iterators, Algorithms]] — the interface `array` adopts.
- **Enables:** [[Header — array]] for the full member reference and task recipes.
- **Siblings:** [[vector]] — the run-time-sized sibling; read the two side by side to see the compile-time ⟷ run-time tension resolved in opposite directions. [[span]] — a non-owning view that can wrap either one.
- **Hazards:** [[Buffer Overruns and Out-of-Bounds Access]] · [[Dangling Pointers and References]].
- **Domain:** [[Map — Standard Library]].
- **Practice:** *Continuum #4* — a fixed-size buffer is the natural first container to reach for before a resizable one is justified; use this note to decide when `array` is still the right call instead of reaching straight for `vector`.

## Check Yourself

> [!quiz]- What does a `std::array<T,N>` object itself store, and how does that differ from what a `std::vector<T>` object stores?
> `array<T,N>` stores the `N` elements directly, inline, wherever the object lives — there is no separate buffer. `vector<T>` stores a small handle (pointer, size, capacity) pointing at a separately allocated heap buffer. That is why `array` never allocates and `vector` almost always does.

> [!quiz]- Why is `array<T,N>::swap` linear in `N` while `vector<T>::swap` is O(1)?
> `vector::swap` only needs to exchange the three words of the handle — the buffers themselves never move. `array` has no handle to exchange: its "buffer" is the object itself, so swapping two `array`s means swapping every element, one at a time, which costs O(N).

> [!quiz]- `std::array<int,3> a{1,2,3}; std::array<int,4> b{1,2,3,4}; a = b;` — does this compile?
> No. `N` is part of the type, so `array<int,3>` and `array<int,4>` are different, unrelated types. Assignment requires the same type on both sides (Primer §9.2.4, p. 338); there is no conversion between arrays of different lengths.

> [!quiz]- `std::array<int,4> a{1,2,3,4}; int* p = a;` — why doesn't this compile, when the equivalent line for a raw `int[4]` would?
> `array<T,N>` is a class type, not an array type, so [[Built-in Arrays and Array-to-Pointer Decay|array-to-pointer decay]] — a rule defined only for expressions of array type — never applies to it. Use `a.data()` to get the pointer explicitly.

## Sources

- Tour §15.3.1 "array" (pp. 202–203): the "no overhead over a built-in array" claim, construction rules, and why you'd choose `array` over both a raw array and `vector`.
- PPP §16.5 "An example: palindromes" (ch. 16 "Pointers and Arrays"): `array` not decaying to a pointer, "and that's good."
- Primer §9.2.4 "Library arrays Have Fixed Size" (pp. 336–338): construction, the fixed size as part of the type, and assignment where a raw array has none.
- cppreference, *`std::array`*: https://en.cppreference.com/w/cpp/container/array
- Draft standard `[array.overview]`: https://eel.is/c++draft/array.overview
