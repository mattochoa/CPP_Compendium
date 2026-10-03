---
id: iterators
title: Iterators
aliases:
- iterator
- begin and end
- past-the-end
- half-open range
type: concept
domain: D10
tier: 1
status: reviewed
standard: C++98
prereqs:
- "[[STL Architecture — Containers, Iterators, Algorithms]]"
related:
- "[[Iterator Categories and Concepts]]"
- "[[Iterator Invalidation]]"
- "[[Header — iterator]]"
- "[[The Range-Based for Loop]]"
- "[[Pointer Arithmetic and Arrays]]"
practice:
- 23
tags:
- type/concept
- domain/d10
- tier/1
- tension/abstraction-vs-control
- tension/safety-vs-performance
- std/c++98
- std/c++20
created: 2026-09-25
updated: 2026-09-25
reviewed: 2026-10-03
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

# Iterators

> [!essence]
> An iterator is a **position in a sequence, packaged as an object**: it can name an element (`*it`), step to the next position (`++it`), and be compared with another position (`it != last`). It is the pointer idea with the memory layout taken out, so the same loop works whether the elements sit in one array, in a chain of nodes, or come off a stream.

## The Problem

A program constantly needs to say "this element, then the next one, until we're done". The difficulty is that every container stores its elements differently, and the obvious ways of naming a place each assume a particular layout.

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint:** Containers lay out their elements in incompatible ways. A `vector` keeps them adjacent in one heap block; a `list` scatters them across nodes linked by pointers; a `map` hangs them off a balanced tree; an input stream doesn't store them at all.
> 2. **Consequence:** An **index** (`v[i]`) names a place only where jumping to element *i* is cheap, and a list would have to walk *i* nodes. A **raw pointer** names a place only in contiguous storage: `++p` on a list node's address lands on unrelated memory. A **node pointer** would work for a list, but it exposes the container's internals to every caller.
> 3. **Requirement:** One way of naming "a place in a sequence" that every container can support, that costs nothing extra where the layout is simple, and that hides the layout from the code using it.
> 4. **Design:** Each container defines a small class type, its *iterator*, that overloads the pointer operators: `*` reads the element, `++` moves to the next one, `==`/`!=` compare positions. For a `vector` that type is a thin wrapper around a pointer; for a `list` it wraps a node pointer and `++` follows the link. Code written against the operators never learns which (`[iterator.requirements.general]`: iterators are "a generalization of pointers").
> 5. **Price:** An iterator is a borrowed position, not an owner. The container can move or destroy the element underneath it (*invalidation*), nothing checks that `it` is still in range, and misuse is [[Undefined Behavior]] rather than an error. Code must also keep two objects, the current position and the end, consistent with each other.

> [!tension] abstraction ⟷ control
> The iterator hides layout (abstraction) but must compile to exactly the pointer loop you would write by hand (control); see Under the Hood. The same trade creates safety ⟷ performance pressure: every `*it` is unchecked because a check on every access would defeat the point.

## Mental Model

> [!model] A cursor that sits *on* an element, plus a marker one step past the last
> Think of a text cursor that highlights one character at a time. `*it` is the highlighted character, `++it` moves the highlight right, and `last` is the empty slot after the final character: you may move the cursor there to mean "done", but there is nothing there to read. **Where the analogy breaks:** an editor's cursor survives edits, but an iterator may not. Insert into a `vector` that has to reallocate and every iterator into it is left pointing at freed memory ([[Iterator Invalidation]]).

```text
  RANGE [first, last)                       HOW ++it IS IMPLEMENTED

  first                   last              vector<int>::iterator     list<int>::iterator
    ▼                       ▼               ┌──────────────┐          ┌──────────────┐
  ┌────┬────┬────┬────┐                     │ int* p       │          │ node* n      │
  │ 10 │ 20 │ 30 │ 40 │  ·                  └──────────────┘          └──────────────┘
  └────┴────┴────┴────┘                     ++it  →  p += 1           ++it  →  n = n->next
                                            (adjacent memory)          (follow a pointer)
  empty range:  first == last
  element count: 4 = last - first  (random access only; otherwise std::distance)
```

Why "one past the last" rather than "the last"? A half-open range makes the empty range expressible (`first == last`) with no special case. It makes "not found" a natural result (`find` returns `last`). And it lets a range split at any `mid` into `[first, mid)` and `[mid, last)` with no overlap and no gap (Tour §13.1, p. 173).

## Mechanics

Every iterator supports `*it` and `++it`. What else it supports depends on its **category** (details in [[Iterator Categories and Concepts]]):

| Situation | Rule | Example |
|---|---|---|
| Read or write the element | `*it` gives the element; `it->m` reaches a member | `*it = 0;` · `it->size()` |
| Move forward | `++it` (prefer pre-increment; `it++` returns a copy of the old position) | `for (; it != last; ++it)` |
| Test for the end | Compare with `!=`/`==` against `end()`; never `<` in generic code | `it != v.end()` |
| Move backward | `--it`; only bidirectional or better (`list`, `map`, `vector`...) | `--it` on a `forward_list` does not compile |
| Jump / measure | `it + n`, `it[n]`, `b - a`, `<`: random access only | `v.begin() + 3`; for a `list`, `std::next(it, 3)` |
| Get the range | Members `c.begin()`/`c.end()`, or free `std::begin(c)` (C++11), which also works on built-in arrays | `std::begin(arr)` |
| Read-only access | `c.cbegin()`/`c.cend()` (C++11) give a `const_iterator`: `*it` is `const` | `*v.cbegin() = 1;` does not compile |
| Range-based `for` | Rewritten by the compiler into a `begin()`/`end()`/`!=`/`++` loop | `for (int x : v)` |

**`const_iterator` vs `const iterator`.** A `const_iterator` is a movable cursor over read-only elements (like `const T*`). A `const iterator` is a cursor that can't move but can still write the element (like `T* const`). You almost always want the first.

**The states of an iterator.** The standard distinguishes four:

| State | Meaning | What you may do |
|---|---|---|
| Dereferenceable | Refers to an element | Everything its category allows |
| Past-the-end | Valid position after the last element | Compare, copy, decrement (bidirectional); **not** `*it` |
| Singular | Not associated with any sequence (e.g. `std::vector<int>::iterator it;`) | Assign to it or destroy it; copy it only if it was value-initialized |
| Invalidated | Was valid until the container changed | Treat as singular |

> [!standard] `[iterator.requirements.general]`
> Values of an iterator `i` for which `*i` is defined are *dereferenceable*. The library never assumes past-the-end values are dereferenceable. Results of most expressions on singular values are undefined; the exceptions are destroying the iterator, assigning a non-singular value to it, and (for value-initialized iterators) copying it. C++20 generalizes the pair `[i, j)` to an iterator plus a **sentinel** `[i, s)`, and adds *counted ranges* `i + [0, n)`.

## Under the Hood

> [!machine] A vector iterator is a pointer; a list iterator is a pointer chase
> The same source loop, `for (auto it = c.begin(); it != c.end(); ++it) s += *it;`, compiled with GCC 13.3, `-std=c++17 -O2 -fno-tree-vectorize` (vectorizing turned off so the loops stay readable), x86-64:
> ```nasm
> sum_vec(std::vector<int> const&):          ; it wraps an int*
> .L3:    add  edx, DWORD PTR [rax]          ;   s += *it
>         add  rax, 4                        ;   ++it  → pointer + sizeof(int)
>         cmp  rcx, rax                      ;   it != end
>         jne  .L3
>
> sum_list(std::list<int> const&):           ; it wraps a node*
> .L9:    add  edx, DWORD PTR 16[rax]        ;   s += *it  (value sits 16 bytes into the node)
>         mov  rax, QWORD PTR [rax]          ;   ++it  → load node->next from memory
>         cmp  rax, rdi                      ;   it != end (end is the list's sentinel node)
>         jne  .L9
> ```
> The iterator class is gone entirely: no calls, no object. What remains is the container's real cost. `add rax, 4` is predictable arithmetic that a CPU prefetcher streams through. `mov rax, [rax]` makes each step wait for a memory load whose address isn't known until the previous load finishes, which is why iterating a `list` is often several times slower than a `vector` of the same length ([[Sequence Containers Compared]]).

`sizeof(std::vector<int>::iterator) == sizeof(int*)` on every mainstream library, and `std::list<int>::iterator` is one node pointer. Iterators are meant to be passed and returned **by value**.

## In Code

**1 · What a range-based `for` really is**

```cpp
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v{1, 2, 3};
    for (int& x : v) x *= 10;                            // ① what you write
    for (auto it = v.begin(), last = v.end(); it != last; ++it)   // ② roughly what the compiler writes
        std::cout << *it << ' ';
    std::cout << '\n';
}
// expect: 10 20 30
```
1. The range-for declares a reference `x` bound to `*it` on each step, so `x *= 10` writes into the vector.
2. `end()` is evaluated **once**, before the loop. That is one reason adding elements inside a range-for is a bug: the saved `last` can be invalidated ([[The Range-Based for Loop]]).

**2 · An iterator is an answer to "where?"**

```cpp
#include <algorithm>
#include <iostream>
#include <string>
#include <vector>

int main() {
    std::vector<std::string> names{"ada", "linus", "grace"};
    auto it = std::find(names.begin(), names.end(), "linus");      // ①
    if (it != names.end()) {                                        // ②
        std::cout << "found at " << (it - names.begin()) << '\n';   // ③
        names.insert(it, "bjarne");                                 // ④
    }
    std::cout << names[1] << ' ' << names.size() << '\n';
}
// expect: found at 1
// expect: bjarne 4
```
1. `find` returns a **position**, not a copy of the element and not a `bool`.
2. "Not found" is reported as `last`, the one value that can never be a real element's position.
3. `it - begin()` converts a position to an index, which is O(1) for random-access iterators.
4. The position is what `insert` and `erase` take. After this call `it` is invalid: `insert` may reallocate. Use the iterator that `insert` returns if you need the position again.

**3 · Dereferencing `end()` is undefined behavior**

```cpp
// cc: ub
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v{1, 2, 3};
    auto it = v.end();
    std::cout << *it << '\n';        // reads one int past the buffer: ASan reports a heap-buffer-overflow
}
```
`end()` is a position, not an element. Here the vector's buffer holds exactly three `int`s, so `*end()` reads memory the vector does not own. Whether that crashes, prints garbage, or appears to work depends on what happens to sit there, which is the definition of undefined behavior.

## Pitfalls

> [!ub] Using an iterator after the container changed
> `push_back`, `insert`, `erase`, `resize`, `clear` and assignment can invalidate iterators. Which ones they invalidate differs per container (all of them after a `vector` reallocation; only the erased element's for a `list`). A stale iterator is not detected; using it is UB. See [[Iterator Invalidation]] and the table in [[Header — vector]].

> [!ub] Mixing iterators from different containers
> `std::find(a.begin(), b.end(), x)` compiles, since the types match, but `b.end()` is not reachable from `a.begin()`, so the loop runs off into memory it doesn't own. The same happens with two calls to a function that returns a container **by value**: `get().begin()` and `get().end()` belong to two different temporary copies.

> [!trap] Iterators into a temporary dangle
> `auto it = make_vector().begin();` leaves `it` pointing into a vector that was destroyed at the end of the statement. Store the container first, then take iterators from the named object ([[Dangling Pointers and References]]).

> [!trap] Using pointer arithmetic that the category doesn't have
> `list.begin() + 2` and `it < last` on a `list` don't compile. That's the design telling you the operation isn't O(1). Use `std::next(it, 2)` and `!=`, which work for every category ([[Header — iterator]]).

## Evolution

| Standard | Change | Why |
|---|---|---|
| **C++98** | Iterators, half-open ranges, `iterator_traits`, five categories | Stepanov's STL design: algorithms written once against a pointer-like protocol |
| C++11 | `auto`, range-based `for`, `cbegin`/`cend` members, free `std::begin`/`std::end`, `std::next`/`std::prev` | Stop spelling `std::vector<int>::const_iterator`; make read-only iteration easy; treat arrays like containers |
| C++14 | Free `std::cbegin`/`std::rbegin`...; value-initialized forward iterators compare equal ("null iterators") | Generic code can ask for read-only or reverse ranges; an "empty" iterator has a usable value |
| C++17 | Range-for allows `begin()` and `end()` to have different types; `std::size`/`std::data`/`std::empty` | Preparation for sentinels; uniform size queries for arrays and containers |
| **C++20** | Iterator **concepts**; iterator + **sentinel** ranges; `std::ranges`; `contiguous_iterator`; `std::ssize`; standard container iterators usable in `constexpr` code | The compiler checks iterator requirements; a range may end at "a condition" rather than at a second iterator |
| C++23 | `basic_const_iterator`, `std::ranges::cbegin` always yields a read-only iterator | Fix `const` iteration for views, where `cbegin` could previously still allow writes |

## Connections

- **Prerequisites:** [[STL Architecture — Containers, Iterators, Algorithms]] (why the iterator seam exists) · [[Pointer Arithmetic and Arrays]] (the model iterators generalize).
- **Enables:** [[Iterator Categories and Concepts]] (which operations each iterator guarantees) · [[The Algorithms Library]] · [[Ranges and Views]] · [[The Range-Based for Loop]].
- **Hazards:** [[Iterator Invalidation]] · [[Dangling Pointers and References]] · [[Undefined Behavior]].
- **Reference card:** [[Header — iterator]] (every operation, adaptor and stream iterator, with compiled patterns).
- **Domain:** [[Map — Standard Library]].
- **Practice:** *Continuum #23 STL Container & Algorithm Playground*: write the same search once with indices and once with iterators, then switch the container from `vector` to `list` and see which version still compiles.

## Check Yourself

> [!quiz]- Why is `end()` one position *past* the last element instead of the last element itself?
> Because it makes an empty range simply `begin() == end()`, gives "not found" a natural value, and lets any range split into two halves that neither overlap nor leave a gap. With an inclusive end, an empty container would need a special case.

> [!quiz]- `for (auto it = l.begin(); it < l.end(); ++it)` fails to compile for a `std::list`. Why, and what's the fix?
> `<` is only defined for random-access iterators, because ordering two positions in a linked list would mean walking from one to the other. Every iterator supports `!=`, so write `it != l.end()`.

> [!quiz]- Spot the bug: `auto it = std::find(v.begin(), v.end(), 3); v.push_back(4); std::cout << *it;`
> `push_back` may reallocate the vector's buffer, which invalidates every iterator into it. `*it` may then read freed memory: undefined behavior. Either finish using `it` before modifying `v`, or keep the index `it - v.begin()` and rebuild the iterator afterwards.

## Sources

- Primer §3.4 "Introducing Iterators" (p. 106), §3.4.2 "Iterator Arithmetic" (p. 111): `begin`/`end`, `const_iterator`, and which iterators support arithmetic.
- Primer §10.5 "Structure of Generic Algorithms" (p. 410): the categories an algorithm can require.
- Tour §13.1 "Introduction" (p. 173), §13.2 "Use of Iterators" (p. 175), §13.3 "Iterator Types" (p. 178): half-open sequences, algorithms returning positions, and what iterator types look like inside different containers.
- PPP ch. 19 "Containers and Iterators", §19.2 "Sequences and iterators": the sequence/iterator idea derived from first principles.
- cppreference / web, *Iterator library* (definitions of dereferenceable, past-the-end, singular, valid ranges, counted ranges): https://en.cppreference.com/w/cpp/iterator
- Draft standard `[iterator.requirements.general]`: https://eel.is/c++draft/iterator.requirements.general
- C++ Core Guidelines ES.71 "Prefer a range-for-statement to a for-statement when there is a choice": https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
