---
id: hdr-vector
title: Header — vector
aliases:
- <vector>
- std::vector
- dynamic array
type: header
domain: HDR
tier: 1
status: draft
standard: C++98
prereqs:
- "[[vector]]"
related:
- "[[vector]]"
- "[[How vector Grows — Capacity and Amortized Cost]]"
- "[[Iterator Invalidation]]"
- "[[Sequence Containers Compared]]"
- "[[Erase-Remove and erase_if]]"
- "[[span]]"
tags:
- type/header
- domain/hdr
- tier/1
- header/vector
- tension/abstraction-vs-control
- tension/safety-vs-performance
created: 2026-09-24
updated: 2026-09-24
header: <vector>
---

# Header — vector

> [!essence]
> **`<vector>`** provides `std::vector<T>`, a **resizable array that owns one contiguous heap buffer**. It gives you O(1) indexing, amortized O(1) `push_back`, cache-friendly iteration and a raw pointer (`data()`) that C APIs accept, with the memory managed for you ([[RAII]]). It is the default container: reach for something else only when you can say why.

> [!standard] Versions
> C++98 (`vector`, `vector<bool>`) / C++11 (`emplace`, `emplace_back`, `data`, `shrink_to_fit`, `cbegin`/`cend`, initializer lists, move semantics) / C++17 (`emplace_back` returns a reference, class template argument deduction, `std::pmr::vector`, incomplete element types allowed) / C++20 (`constexpr` vector, `std::erase`/`std::erase_if`, `<=>` replaces `<`, `>`, `<=`, `>=`, `!=`) / C++23 (`from_range` constructor, `append_range`, `insert_range`, `assign_range`)

## Memory Layout

A `vector` object is three pointers (24 bytes on typical 64-bit libraries). The elements live in a separate heap block that the vector owns.

```text
  STACK (automatic)                           HEAP (dynamic, owned by v)
 ┌──────────────────────────┐          ┌─────┬─────┬─────┬─────┬ ─ ─ ─ ┬ ─ ─ ─ ┐
 │ std::vector<int> v       │          │  10 │  20 │  30 │  40 │ spare │ spare │
 │  begin ●─────────────────┼────────▶ └─────┴─────┴─────┴─────┴ ─ ─ ─ ┴ ─ ─ ─ ┘
 │  end   ●─────────────────┼──────────────────────────────────▲
 │  cap   ●─────────────────┼──────────────────────────────────────────────────▲
 └──────────────────────────┘          ◀───── size() = 4 ─────▶◀─── spare 2 ───▶
                                       ◀──────────── capacity() = 6 ───────────▶
```

When `size()` reaches `capacity()`, the next insertion allocates a bigger block (typically 1.5× or 2×), moves the elements across, and frees the old block. **Every pointer, reference and iterator into the old block now dangles.**

## Quick Reference

```cpp
// cc: fragment
// ═══════════════════════════════════════════════════════════════════════════
// CONSTRUCTION & ASSIGNMENT
// ═══════════════════════════════════════════════════════════════════════════
std::vector<int> v;                     // none        | Empty, no allocation  |
std::vector<int> v(5);                  // count       | 5 value-initialized   | {0,0,0,0,0}
std::vector<int> v(5, 7);               // count, value| 5 copies of 7         | {7,7,7,7,7}   ← PARENTHESES
std::vector<int> v{5, 7};               // init list   | Exactly these values  | {5,7}         ← BRACES: different!
std::vector<int> v = {1, 2, 3};         // init list   | List initialization   | C++11
std::vector<int> v(first, last);        // iterators   | Copy a range          | Any input iterators
std::vector<int> v(other);              // vector      | Deep copy             | Allocates, copies every element
std::vector<int> v(std::move(other));   // rvalue      | Steal the buffer      | O(1); other left empty (valid)
std::vector v{1, 2, 3};                 // init list   | CTAD → vector<int>    | C++17
std::vector<int> v(std::from_range, r); // range       | Copy any range        | C++23
v = other;  v = std::move(other);  v = {1, 2};         // Copy / move / list assignment
v.assign(n, value);  v.assign(first, last);  v.assign({1, 2});   // Replace all contents
v.assign_range(r)                       // range       | Replace from range    | C++23

// ═══════════════════════════════════════════════════════════════════════════
// ELEMENT ACCESS
// ═══════════════════════════════════════════════════════════════════════════
v[i]                                    // index       | Element i             | NO bounds check: out of range = UB
v.at(i)                                 // index       | Element i             | Throws std::out_of_range
v.front()  /  v.back()                  // none        | First / last element  | UB on an empty vector
v.data()                                // none        | T* to first element   | C++11; for C APIs; may be null if empty

// ═══════════════════════════════════════════════════════════════════════════
// ITERATORS  (random access, contiguous)
// ═══════════════════════════════════════════════════════════════════════════
v.begin() / v.end()                     // Mutable (const on a const vector)
v.cbegin() / v.cend()                   // Always const                        | C++11
v.rbegin() / v.rend() / v.crbegin() / v.crend()        // Reverse traversal

// ═══════════════════════════════════════════════════════════════════════════
// SIZE & CAPACITY
// ═══════════════════════════════════════════════════════════════════════════
v.size()                                // none        | Element count         | size_type (unsigned!)
v.empty()                               // none        | size() == 0?          | Prefer over size() == 0
v.capacity()                            // none        | Allocated slots       | >= size()
v.reserve(n)                            // count       | Capacity >= n         | Never shrinks; no new elements
v.resize(n)  /  v.resize(n, value)      // count       | Grow (value-init/copies) or shrink (destroy) |
v.shrink_to_fit()                       // none        | Request capacity == size | C++11, non-binding
v.max_size()                            // none        | Theoretical limit     |

// ═══════════════════════════════════════════════════════════════════════════
// MODIFIERS
// ═══════════════════════════════════════════════════════════════════════════
v.push_back(x)                          // T           | Copy/move x to the end| Amortized O(1)
v.emplace_back(args...)                 // ctor args   | Construct at the end  | C++11; returns T& since C++17
v.pop_back()                            // none        | Destroy last element  | UB on an empty vector; returns void
v.insert(pos, x)                        // iter, T     | Insert before pos     | O(n): shifts the tail; returns iterator
v.insert(pos, n, x) / insert(pos, first, last) / insert(pos, {…})
v.emplace(pos, args...)                 // iter, args  | Construct before pos  | C++11
v.insert_range(pos, r)  /  v.append_range(r)           // C++23
v.erase(pos)                            // iterator    | Remove one            | O(n); returns iterator to next
v.erase(first, last)                    // range       | Remove a range        | Returns iterator after it
v.clear()                               // none        | Remove all            | size → 0, capacity UNCHANGED
v.swap(other)  /  std::swap(a, b)       // vector      | Exchange buffers      | O(1)

// ═══════════════════════════════════════════════════════════════════════════
// NON-MEMBERS
// ═══════════════════════════════════════════════════════════════════════════
std::erase(v, value)                    // Remove all == value, return count    | C++20
std::erase_if(v, pred)                  // Remove all matching, return count    | C++20
a == b,  a <=> b                        // Element-wise, lexicographic          | <=> C++20 (< > <= >= != before)
std::pmr::vector<T>                     // Vector using a memory_resource       | C++17
std::vector<bool>                       // Bit-packed specialization: NOT a real container of bool
```

## Patterns

### Build a Vector Efficiently
```cpp
#include <iostream>
#include <string>
#include <vector>

struct Reading { std::string sensor; double value; };

int main() {
    std::vector<Reading> log;
    log.reserve(3);                                  // one allocation up front when the count is known
    log.push_back({"temp", 21.5});                   // builds a temporary, then moves it in
    log.emplace_back(Reading{"humidity", 40.0});
    Reading& last = log.emplace_back(Reading{"co2", 412.0});   // C++17: returns a reference
    std::cout << log.size() << ' ' << last.sensor << '\n';
}
// expect: 3 co2
```

### Iterate: Read, Modify, or Need the Index
```cpp
#include <iostream>
#include <vector>

int main() {
    std::vector<int> scores{70, 85, 92};
    for (int& s : scores) s += 5;                              // modify: reference
    int total = 0;
    for (const int& s : scores) total += s;                    // read: const reference (cheap for big T)
    for (std::size_t i = 0; i < scores.size(); ++i)            // need the index: size_t, not int
        std::cout << i << ':' << scores[i] << ' ';
    std::cout << "total=" << total << '\n';
}
// expect: 0:75 1:90 2:97 total=262
```

### Bounds-Checked Access
```cpp
#include <iostream>
#include <stdexcept>
#include <vector>

int main() {
    const std::vector<int> v{1, 2, 3};
    try {
        std::cout << v.at(10) << '\n';                        // checked: throws
    } catch (const std::out_of_range& e) {
        std::cout << "out of range\n";
    }
    // v[10] would be undefined behavior: no check, no exception.
}
// expect: out of range
```

### Remove Elements That Match a Condition (C++11/14/17: erase-remove)
```cpp
#include <algorithm>
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v{1, 2, 3, 4, 5, 6};
    v.erase(std::remove_if(v.begin(), v.end(), [](int x) { return x % 2 == 0; }),   // ① compact keepers
            v.end());                                                               // ② chop the tail
    for (int x : v) std::cout << x << ' ';
    std::cout << '\n';
}
// expect: 1 3 5
// remove_if alone does NOT shrink the vector. It returns the new logical end, and erase does the removal.
```

### Remove Elements That Match a Condition (C++20)
```cpp
// cc: std=c++20
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v{1, 2, 3, 4, 5, 6};
    const auto removed = std::erase_if(v, [](int x) { return x % 2 == 0; });   // one call, returns count
    std::cout << removed << " removed, " << v.size() << " left\n";
}
// expect: 3 removed, 3 left
```

### Erase While Looping
```cpp
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v{5, -1, 7, -3, 9};
    for (auto it = v.begin(); it != v.end(); ) {
        if (*it < 0) it = v.erase(it);   // erase returns the next valid iterator
        else ++it;                       // advance only when nothing was erased
    }
    std::cout << v.size() << '\n';
}
// expect: 3
```

### Keep a Vector Sorted on Insert
```cpp
#include <algorithm>
#include <iostream>
#include <vector>

void insert_sorted(std::vector<int>& v, int x) {
    v.insert(std::upper_bound(v.begin(), v.end(), x), x);   // O(log n) search + O(n) shift
}

int main() {
    std::vector<int> v{10, 20, 40};
    insert_sorted(v, 30);
    insert_sorted(v, 5);
    for (int x : v) std::cout << x << ' ';
    std::cout << '\n';
}
// expect: 5 10 20 30 40
```

### Remove Duplicates
```cpp
#include <algorithm>
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v{3, 1, 3, 2, 1, 3};
    std::sort(v.begin(), v.end());                       // unique only removes ADJACENT duplicates
    v.erase(std::unique(v.begin(), v.end()), v.end());
    for (int x : v) std::cout << x << ' ';
    std::cout << '\n';
}
// expect: 1 2 3
```

### Fast Unordered Removal (swap and pop)
```cpp
#include <iostream>
#include <utility>
#include <vector>

template <class T>
void remove_at_unordered(std::vector<T>& v, std::size_t i) {
    std::swap(v[i], v.back());           // O(1) instead of shifting the tail
    v.pop_back();
}

int main() {
    std::vector<char> v{'a', 'b', 'c', 'd'};
    remove_at_unordered(v, 1);
    for (char c : v) std::cout << c;
    std::cout << '\n';
}
// expect: adc
// Use it when element order doesn't matter (particles, entities, work queues).
```

### A 2D Grid in One Contiguous Buffer
```cpp
#include <iostream>
#include <vector>

class Grid {
    std::size_t rows_, cols_;
    std::vector<int> cells_;                             // one allocation, cache-friendly
public:
    Grid(std::size_t r, std::size_t c) : rows_(r), cols_(c), cells_(r * c, 0) {}
    int& at(std::size_t r, std::size_t c) { return cells_[r * cols_ + c]; }   // row-major
    std::size_t rows() const { return rows_; }
};

int main() {
    Grid g(3, 4);
    g.at(2, 3) = 7;
    std::cout << g.at(2, 3) << ' ' << g.rows() << '\n';
}
// expect: 7 3
// vector<vector<int>> works too, but makes one allocation per row and scatters rows in memory.
```

### Hand the Buffer to a C API
```cpp
#include <cstring>
#include <iostream>
#include <vector>

extern "C" void fill_bytes(unsigned char* dst, std::size_t n) { std::memset(dst, 0xAB, n); }  // stand-in C API

int main() {
    std::vector<unsigned char> buffer(16);               // size first: the C function writes into it
    fill_bytes(buffer.data(), buffer.size());            // contiguous: data() is a plain array
    std::cout << std::hex << static_cast<int>(buffer[15]) << '\n';
}
// expect: ab
```

### Return and Transfer Without Copying
```cpp
#include <iostream>
#include <utility>
#include <vector>

std::vector<int> make_range(int n) {
    std::vector<int> out;
    out.reserve(n);
    for (int i = 0; i < n; ++i) out.push_back(i);
    return out;                                          // no copy: NRVO or an implicit move
}

int main() {
    std::vector<int> a = make_range(1000);
    std::vector<int> b = std::move(a);                   // O(1): b takes a's buffer
    std::cout << b.size() << ' ' << a.empty() << '\n';   // a is valid; for vector it's empty in practice
}
// expect: 1000 1
```

### Watching Capacity Grow
```cpp
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v;
    std::size_t last_cap = v.capacity(), reallocations = 0;
    for (int i = 0; i < 1000; ++i) {
        v.push_back(i);
        if (v.capacity() != last_cap) { ++reallocations; last_cap = v.capacity(); }
    }
    std::cout << "1000 push_backs, " << (reallocations < 20 ? "few" : "many") << " reallocations\n";
}
// expect: 1000 push_backs, few reallocations
// Geometric growth: about 11 reallocations with doubling (libstdc++, libc++), about 18 with 1.5x (MSVC).
```

## Key Concepts

### `size()` vs `capacity()`
`size()` counts live elements. `capacity()` counts allocated slots. `reserve(n)` changes only capacity (no elements are created). `resize(n)` changes size, constructing or destroying elements. Writing `v[i]` for `i >= size()` is undefined behavior even when `i < capacity()`.

### Growth Is Geometric, So `push_back` Is Amortized O(1)
On reallocation the capacity is multiplied (2× in libstdc++ and libc++, 1.5× in MSVC), not increased by a constant. The total copying over n pushes is therefore O(n). If you know the final size, `reserve` it and pay for one allocation instead of about log n. See [[How vector Grows — Capacity and Amortized Cost]].

### Iterator Invalidation
| Operation | Invalidates |
|---|---|
| Read-only calls (`[]`, `at`, `size`, iteration) | Nothing |
| `push_back`, `emplace_back`, `insert`, `emplace`, `reserve`, `resize` **that reallocate** | **Everything**: all iterators, pointers and references |
| Same operations without reallocation | `end()`, plus (for `insert`/`emplace`) everything at and after the insertion point |
| `erase` | The erased elements and everything after them, including `end()` |
| `pop_back` | The last element and `end()` |
| `clear`, `assign`, `operator=` | Everything |
| `shrink_to_fit` | Everything, if it reallocates |

Holding a reference across a `push_back` is the classic bug. See [[Iterator Invalidation]] and [[Dangling Pointers and References]].

### Braces vs Parentheses
`std::vector<int> v(3, 7)` is `{7, 7, 7}`, while `std::vector<int> v{3, 7}` is `{3, 7}`. Braces always prefer the `initializer_list` constructor. Use parentheses for "count and value" and braces for "these elements". See [[Narrowing Conversions and Brace Initialization]].

### `noexcept` Moves Make Growth Fast
When `vector` reallocates, it *moves* elements only if their move constructor is `noexcept` (or they can't be copied). Otherwise it *copies* them, to keep the strong exception guarantee. A user type with a non-`noexcept` move constructor silently makes every growth a full copy. See [[noexcept and Why Move Must Not Throw]].

### `push_back` vs `emplace_back`
`emplace_back(args...)` constructs the element in place from constructor arguments. `push_back(x)` copies or moves an existing object. For an already-built object the two cost the same. `emplace_back` wins when you would otherwise build a temporary, and it can call `explicit` constructors, which is a correctness trap as well as a feature.

### `vector<bool>` Is Not a Container of `bool`
The specialization packs bits, so `operator[]` returns a proxy object, not a `bool&`. `&v[0]` is not a `bool*`, `auto x = v[0]` holds a proxy, and concurrent writes to different elements can race. Use `std::vector<char>`, `std::deque<bool>` or `std::bitset` when you need real `bool` objects.

### Unsigned Sizes
`size()` returns an unsigned `size_type`. `v.size() - 1` on an empty vector wraps to a huge number, and `for (int i = 0; i < v.size(); ++i)` mixes signed and unsigned. Use range-for, `std::size_t` indices, or C++20's `std::ssize(v)`. See [[Mixing Signed and Unsigned]].

### `clear()` Keeps the Memory
`clear()` destroys the elements but keeps the capacity, which is good for reuse in loops. To actually release memory, call `shrink_to_fit()` (a request) or swap with an empty vector: `std::vector<T>().swap(v);`.

## Choosing a Tool

```text
Need                                              Best choice
────────────────────────────────────────────────────────────────────────────
Default sequence, unknown size                    std::vector
Fixed size known at compile time                  std::array            (<array>)
Fast push/pop at BOTH ends                        std::deque            (<deque>)
Stable references while inserting/erasing         std::list / std::deque (ends only)
A non-owning view of someone else's elements      std::span             (<span>, C++20)
Sorted, unique keys, frequent lookup              std::set / std::map, or sorted vector + binary search
Small sizes that usually fit on the stack         a small-vector library (not in std)
Bits                                              std::bitset / vector<bool> (with care)
```

## Best Practices

1. **Default to `std::vector`**; measure before switching to `list` or `deque`
2. **`reserve` when the final size is known** or can be estimated
3. **Never hold references or iterators across a growing call**; hold indices instead
4. **Use `at()` at trust boundaries** (user input, file data) and `[]` in hot inner loops you have validated
5. **Parentheses for count/value, braces for element lists**
6. **Mark move constructors `noexcept`** on types you store in vectors
7. **Use `std::erase_if` (C++20)** or the erase-remove idiom; never erase inside a range-for
8. **Pass vectors by `const&`** (read), `&` (modify) or value (sink), and return them by value
9. **Prefer one flat vector** over `vector<vector<T>>` for fixed-shape grids
10. **Avoid `vector<bool>`** unless you want bit packing and accept its proxy semantics

## Related Headers

```cpp
#include <vector>      // std::vector, std::vector<bool>, std::pmr::vector (C++17), erase/erase_if (C++20)
#include <array>       // std::array: fixed size, no heap
#include <deque>       // std::deque: fast at both ends
#include <list>        // std::list: stable iterators, O(1) splice
#include <span>        // C++20: non-owning view over contiguous elements
#include <algorithm>   // sort, remove_if, unique, lower_bound, find
#include <numeric>     // accumulate, iota
#include <memory_resource>  // C++17: pmr allocators
#include <ranges>      // C++20: views over vectors
```

## Connections

- **Hub:** [[Map — Standard Headers]]
- **Concept notes (the why behind this card):** [[vector]] · [[How vector Grows — Capacity and Amortized Cost]] · [[Iterator Invalidation]] · [[Sequence Containers Compared]] · [[Erase-Remove and erase_if]] · [[Move Semantics]] · [[span]]
- **Hazards:** [[Dangling Pointers and References]] (the reallocation example) · [[Mixing Signed and Unsigned]]
- **Sibling cards:** [[Header — string]] · [[Header — algorithm]]
- **Practice:** *Continuum #12 Build-Your-Own Dynamic Array* (reimplement this card's layout diagram) · *#7 Word & Text Analyzer* · *#23 STL Container & Algorithm Playground*

## Sources

- Primer §3.3 "Library vector Type" (p. 96): construction, `push_back`, subscripting rules.
- Primer §9.3.6 "Container Operations May Invalidate Iterators" (p. 353) and §9.4 "How a vector Grows" (p. 355): invalidation and capacity management.
- Tour §12.2 "vector" (p. 158): the designer's view of `vector` as the default container.
- PPP ch. 15 "Vector and Free Store" (§15.2 "vector basics"): `vector` built from scratch, from first principles.
- Pikus ch. 4 "Memory Architecture and Performance" (p. 113): why contiguous storage wins on real caches.
- cppreference / web, *`std::vector`*: https://en.cppreference.com/w/cpp/container/vector
- cppreference / web, *`<vector>`*: https://en.cppreference.com/w/cpp/header/vector
- C++ Core Guidelines SL.con.2 "Prefer using STL `vector` by default unless you have a reason to use a different container": https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
