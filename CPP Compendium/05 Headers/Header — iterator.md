---
id: hdr-iterator
title: Header — iterator
aliases:
- <iterator>
- iterator library
- std::back_inserter
- std::istream_iterator
- std::reverse_iterator
type: header
domain: HDR
tier: 2
status: draft
standard: C++98
prereqs:
- "[[Iterators]]"
related:
- "[[Iterators]]"
- "[[Iterator Categories and Concepts]]"
- "[[STL Architecture — Containers, Iterators, Algorithms]]"
- "[[Iterator Invalidation]]"
- "[[Ranges and Views]]"
tags:
- type/header
- domain/hdr
- tier/2
- header/iterator
- tension/abstraction-vs-control
- tension/compatibility-vs-evolution
created: 2026-09-25
updated: 2026-09-25
header: <iterator>
---

# Header — iterator

> [!essence]
> **`<iterator>`** is the toolbox for the STL's connecting piece. It gives you the **operations** that move any iterator (`advance`, `next`, `prev`, `distance`), the **adaptors** that change what an iterator does (reverse it, make it insert, make it move, make it count), the **stream iterators** that turn `cin`/`cout` into sequences, the free **`begin`/`end`/`size`** functions that work on arrays and containers alike, and the **traits and concepts** that let generic code ask "what can this iterator do?". It holds no containers and no algorithms: it is the glue between them ([[STL Architecture — Containers, Iterators, Algorithms]]).

> [!standard] Versions
> C++98 (`iterator_traits`, category tags, `advance`, `distance`, `reverse_iterator`, insert iterators, stream iterators) / C++11 (`next`, `prev`, `move_iterator`, free `begin`/`end`) / C++14 (`cbegin`/`cend`, `rbegin`/`rend`, `make_reverse_iterator`) / C++17 (`size`, `empty`, `data`; named requirement *LegacyContiguousIterator*; `advance`/`next`/`prev`/`distance` and `reverse_iterator` become `constexpr`; `std::iterator` base class **deprecated**) / C++20 (iterator **concepts**, `contiguous_iterator_tag`, sentinels, `counted_iterator`, `common_iterator`, `ranges::advance`/`next`/`prev`/`distance`, `iter_value_t` & friends, `ssize`, `constexpr` container iterators) / C++23 (`basic_const_iterator`, `make_const_iterator`, `iter_const_reference_t`) / C++26 (`projected_value_t`)

## Class Hierarchy / Family

Iterator categories form a ladder. Each rung promises everything the rung below it promises, plus more. Algorithms state the lowest rung they need; containers hand out the highest rung they can support cheaply.

```text
  CATEGORY                        OPERATIONS IT ADDS                TYPICAL SOURCE
  ┌────────────────────────────┐
  │ contiguous  (C++17 / C++20)│  elements adjacent in memory       vector, array, string, T*
  └─────────────▲──────────────┘
  ┌─────────────┴──────────────┐
  │ random access              │  it + n, it - n, it[n], <, a - b   deque
  └─────────────▲──────────────┘
  ┌─────────────┴──────────────┐
  │ bidirectional              │  --it                              list, set, map
  └─────────────▲──────────────┘
  ┌─────────────┴──────────────┐
  │ forward                    │  multi-pass, ==                    forward_list, unordered_map
  └─────────────▲──────────────┘
  ┌─────────────┴──────────────┐
  │ input                      │  read *it, single pass             istream_iterator
  └─────────────▲──────────────┘
  ┌─────────────┴──────────────┐
  │ iterator (the base)        │  *it, ++it
  └─────────────┬──────────────┘
  ┌─────────────▼──────────────┐
  │ output  (a side branch)    │  write *it = x, single pass        back_inserter, ostream_iterator
  └────────────────────────────┘
```
Arrowheads point at the more capable category, which supports everything its source does. Output is a side branch: an output iterator is written through, not read.

A half-open range `[first, last)` and what `reverse_iterator` does to it:

```text
            first                          last  (past-the-end: never dereference)
               ▼                             ▼
            ┌─────┬─────┬─────┬─────┬─────┐
            │  10 │  20 │  30 │  40 │  50 │  ·
            └─────┴─────┴─────┴─────┴─────┘
         ▲                             ▲
       rend()                       rbegin()    *rbegin() == 50
                                                rbegin().base() == last: ONE TO THE RIGHT
```

A `reverse_iterator` stores the forward iterator one position to the right of the element it refers to, so `*r` is `*std::prev(r.base())`. That offset is why `rbegin()` can be built from `end()` without a special case, and why converting back needs care (see "Search Backwards, Then Convert Back").

## Quick Reference

```cpp
// cc: fragment
// ═══════════════════════════════════════════════════════════════════════════
// OPERATIONS: move and measure any iterator (cost depends on its category)
// ═══════════════════════════════════════════════════════════════════════════
std::advance(it, n)                     // it&, count  | Move it by n in place | O(1) random access, else O(n); n<0 needs bidirectional
std::next(it)  /  std::next(it, n)      // it, count   | Copy, moved forward   | C++11; returns the new iterator
std::prev(it)  /  std::prev(it, n)      // it, count   | Copy, moved back      | C++11; needs bidirectional
std::distance(first, last)              // two iters   | Number of steps       | O(1) random access, else O(n); signed difference_type
std::ranges::next(it, bound)            // it, sentinel| Move up to a bound    | C++20; also (it, n, bound)
std::ranges::distance(r)                // range       | Size of a range       | C++20; O(1) if sized
std::iter_swap(a, b)                    // two iters   | Swap *a and *b        | C++98

// ═══════════════════════════════════════════════════════════════════════════
// RANGE ACCESS: free functions that work on containers AND built-in arrays
// ═══════════════════════════════════════════════════════════════════════════
std::begin(c)   /  std::end(c)          // c or array  | First / past-the-end | C++11
std::cbegin(c)  /  std::cend(c)         // c or array  | Const iterators       | C++14
std::rbegin(c)  /  std::rend(c)         // c or array  | Reverse iterators     | C++14 (crbegin/crend too)
std::size(c)                            // c or array  | Element count         | C++17 (unsigned)
std::ssize(c)                           // c or array  | Element count         | C++20 (signed: safe in i < n loops)
std::empty(c)   /  std::data(c)         // c or array  | Is empty / T*         | C++17

// ═══════════════════════════════════════════════════════════════════════════
// INSERT ITERATORS: `*it = x` becomes a container insertion
// ═══════════════════════════════════════════════════════════════════════════
std::back_inserter(c)                   // container   | *it = x → c.push_back(x)   | C++98; vector, deque, list, string
std::front_inserter(c)                  // container   | *it = x → c.push_front(x)  | C++98; deque, list (REVERSES order)
std::inserter(c, pos)                   // c, iterator | *it = x → c.insert(pos, x) | C++98; any container, incl. set/map

// ═══════════════════════════════════════════════════════════════════════════
// STREAM ITERATORS: a stream seen as a sequence (always single-pass)
// ═══════════════════════════════════════════════════════════════════════════
std::istream_iterator<T>(in)            // istream     | Reads T with >>       | Input iterator; default-constructed = end of stream
std::istream_iterator<T>()              // none        | End-of-stream marker  |
std::ostream_iterator<T>(out, ", ")     // ostream     | Writes T with <<      | Delimiter written AFTER every element
std::istreambuf_iterator<char>(in)      // istream     | Raw chars, no skipping| Keeps whitespace; fast whole-file reads
std::ostreambuf_iterator<char>(out)     // ostream     | Raw chars out         |

// ═══════════════════════════════════════════════════════════════════════════
// OTHER ADAPTORS
// ═══════════════════════════════════════════════════════════════════════════
std::reverse_iterator<It>               // iterator    | Walks backwards       | C++98; r.base() is one to the RIGHT of *r
std::make_reverse_iterator(it)          // iterator    | Deduces the type      | C++14
std::make_move_iterator(it)             // iterator    | *it yields T&&        | C++11; algorithms then MOVE instead of copy
std::counted_iterator(it, n)            // it, count   | Stops after n steps   | C++20; pair with std::default_sentinel
std::common_iterator<It, S>             // it/sentinel | One type for both     | C++20; feeds pre-C++20 algorithms
std::default_sentinel                   // none        | "Iterator knows end"  | C++20
std::unreachable_sentinel               // none        | Never equal: no end   | C++20; unbounded ranges
std::make_const_iterator(it)            // iterator    | Read-only view        | C++23 (basic_const_iterator)

// ═══════════════════════════════════════════════════════════════════════════
// TRAITS AND TAGS (C++98 style: ask via iterator_traits)
// ═══════════════════════════════════════════════════════════════════════════
std::iterator_traits<It>::value_type        // Element type (no const/ref)
std::iterator_traits<It>::difference_type   // Signed distance type
std::iterator_traits<It>::reference         // What *it returns
std::iterator_traits<It>::pointer           // What it-> uses
std::iterator_traits<It>::iterator_category // One of the tags below
std::input_iterator_tag  output_iterator_tag  forward_iterator_tag
std::bidirectional_iterator_tag  random_access_iterator_tag
std::contiguous_iterator_tag                // C++20
std::iterator<Cat, T>                       // Base class for the 5 typedefs: DEPRECATED C++17, write them yourself

// ═══════════════════════════════════════════════════════════════════════════
// CONCEPTS AND ASSOCIATED TYPES (C++20 style: constrain templates directly)
// ═══════════════════════════════════════════════════════════════════════════
std::input_iterator<I>   std::output_iterator<I, T>   std::forward_iterator<I>
std::bidirectional_iterator<I>   std::random_access_iterator<I>   std::contiguous_iterator<I>
std::sentinel_for<S, I>  std::sized_sentinel_for<S, I>              // What may end a range
std::indirectly_readable<I>  std::indirectly_writable<I, T>  std::weakly_incrementable<I>
std::iter_value_t<I>  std::iter_reference_t<I>  std::iter_difference_t<I>   // C++20
std::iter_rvalue_reference_t<I>  std::iter_common_reference_t<I>            // C++20
std::iter_const_reference_t<I>                                              // C++23
std::ranges::iter_move(it)  /  std::ranges::iter_swap(a, b)                 // C++20 customization points
std::sortable<I>  std::mergeable<I1, I2, O>  std::permutable<I>             // Algorithm requirements, C++20
std::indirect_unary_predicate<F, I>  std::indirect_strict_weak_order<F, I>  // Callable requirements, C++20
std::projected<I, Proj>                                                     // C++20; projected_value_t C++26
```

## Patterns

### Walk a Range with Explicit Iterators (C++11/14)
```cpp
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v{3, 8, 5, 8};
    for (auto it = v.begin(); it != v.end(); ++it)   // mutable: we may write through it
        if (*it == 8) *it = 0;
    int sum = 0;
    for (auto it = v.cbegin(); it != v.cend(); ++it) // const: reading only, the compiler enforces it
        sum += *it;
    std::cout << sum << '\n';
}
// expect: 8
```
Use `!=` against `end()`, not `<`: only random-access iterators have `<`, but every iterator has `!=`. Range-for is this exact loop written for you ([[The Range-Based for Loop]]).

### Read Numbers from a Stream
```cpp
#include <iostream>
#include <iterator>
#include <numeric>
#include <sstream>
#include <vector>

int main() {
    std::istringstream in("4 8 15 16 23 42");                // any istream: std::cin, an ifstream...
    std::vector<int> v(std::istream_iterator<int>(in),       // from the first number...
                       std::istream_iterator<int>{});        // ...to end-of-stream (or a bad read)
    std::cout << v.size() << " numbers, sum " << std::accumulate(v.begin(), v.end(), 0) << '\n';
}
// expect: 6 numbers, sum 108
```
Braces on the second argument avoid the "most vexing parse", where the whole line would be read as a function declaration. Reading stops at end-of-file **or** at the first token that isn't an `int`.

### Print a Sequence with a Separator
```cpp
#include <algorithm>
#include <iostream>
#include <iterator>
#include <vector>

int main() {
    std::vector<int> v{1, 2, 3};
    std::copy(v.begin(), v.end(), std::ostream_iterator<int>(std::cout, " "));
    std::cout << '\n';
    if (!v.empty()) {                                        // no trailing comma: print the last one separately
        std::copy(v.begin(), std::prev(v.end()), std::ostream_iterator<int>(std::cout, ", "));
        std::cout << v.back() << '\n';
    }
}
// expect: 1, 2, 3
```
`ostream_iterator` writes the delimiter after **every** element, including the last. C++20's `std::format` / C++23's `std::print` with ranges or a `join` are cleaner where available ([[Header — Modern IO]]).

### Fill an Empty Container from an Algorithm
```cpp
#include <algorithm>
#include <iostream>
#include <iterator>
#include <vector>

int main() {
    std::vector<int> in{1, 2, 3, 4, 5, 6};
    std::vector<int> evens;                                  // empty: no room to write into
    std::copy_if(in.begin(), in.end(), std::back_inserter(evens),
                 [](int x) { return x % 2 == 0; });          // each "write" becomes push_back
    std::cout << evens.size() << ':' << evens[0] << evens[1] << evens[2] << '\n';
}
// expect: 3:246
```
Passing `evens.begin()` instead would write past the end of an empty vector: undefined behavior. An algorithm cannot grow a container on its own; it only writes through the iterator you give it.

### Insert into a set, or at the Front
```cpp
#include <algorithm>
#include <deque>
#include <iostream>
#include <iterator>
#include <set>
#include <vector>

int main() {
    std::vector<int> src{3, 1, 2, 3};
    std::set<int> s;
    std::copy(src.begin(), src.end(), std::inserter(s, s.end()));   // set has no push_back
    std::deque<int> d;
    std::copy(src.begin(), src.end(), std::front_inserter(d));      // each element goes to the front
    for (int x : s) std::cout << x;
    std::cout << ' ';
    for (int x : d) std::cout << x;
    std::cout << '\n';
}
// expect: 123 3213
```
`front_inserter` reverses the order. `inserter` keeps order in sequence containers; for a `set` the position is only a hint and the set orders elements anyway.

### Search Backwards, Then Convert Back
```cpp
#include <algorithm>
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v{7, 1, 7, 2};
    auto r = std::find(v.rbegin(), v.rend(), 7);        // last 7, found by walking backwards
    auto it = std::prev(r.base());                       // base() is one to the right: step back
    std::cout << "last 7 at index " << (it - v.begin()) << '\n';
    v.erase(it);                                         // erase needs a forward iterator
    std::cout << v.size() << '\n';
}
// expect: last 7 at index 2
```
Forgetting `std::prev` erases the element **after** the one you found, and when the match is the last element, `r.base()` is `end()`, which `erase` must never receive. See the diagram under Class Hierarchy.

### Move Around a list (Bidirectional Only)
```cpp
#include <iostream>
#include <iterator>
#include <list>

int main() {
    std::list<char> l{'a', 'b', 'c', 'd', 'e'};
    auto it = std::next(l.begin(), 3);                  // it + 3 does not compile for list
    std::cout << *it << *std::prev(it) << ' ';
    std::advance(it, -2);                                // negative is fine: list is bidirectional
    std::cout << *it << ' ' << std::distance(l.begin(), l.end()) << '\n';  // O(n) walk; l.size() is O(1)
}
// expect: dc b 5
```
`next`, `prev`, `advance` and `distance` compile for every category and pick the fastest way to do the job. On a `vector` they are one addition; on a `list` they walk node by node.

### Move Elements Instead of Copying
```cpp
#include <iostream>
#include <iterator>
#include <string>
#include <vector>

int main() {
    std::vector<std::string> src{"alpha", "beta", "gamma"};
    std::vector<std::string> dst(std::make_move_iterator(src.begin()),
                                 std::make_move_iterator(src.end()));   // each *it is std::string&&
    std::cout << dst.size() << ' ' << dst[2] << ' ' << src.size() << '\n';
}
// expect: 3 gamma 3
```
`src` still holds three strings, but they are in the moved-from state: valid, with unspecified contents. Assign to them or destroy them; don't read them ([[The Moved-From State]]).

### Generic Code for Arrays and Containers Alike (C++17)
```cpp
#include <iostream>
#include <iterator>
#include <list>
#include <numeric>

template <typename C>
int total(const C& c) {
    return std::accumulate(std::begin(c), std::end(c), 0);  // works for T[N] too: arrays have no .begin()
}

int main() {
    int raw[] = {1, 2, 3};
    std::list<int> l{10, 20};
    std::cout << total(raw) << ' ' << total(l) << ' ' << std::size(raw) << '\n';  // std::size: C++17
}
// expect: 6 30 3
```
Free `std::begin`/`std::end` let one template accept built-in arrays, standard containers, and any user type with `begin()`/`end()` members.

### Choose an Algorithm by Iterator Category (C++14/17 Tag Dispatch)
```cpp
#include <iostream>
#include <iterator>
#include <list>
#include <vector>

template <typename It>
const char* jump(It& it, int n, std::random_access_iterator_tag) { it += n; return "O(1) jump"; }

template <typename It>
const char* jump(It& it, int n, std::input_iterator_tag) {           // forward & bidirectional convert to this
    while (n-- > 0) ++it;
    return "O(n) walk";
}

template <typename It>
const char* my_advance(It& it, int n) {
    return jump(it, n, typename std::iterator_traits<It>::iterator_category{});  // tag picks the overload
}

int main() {
    std::vector<int> v{1, 2, 3, 4};
    std::list<int> l{1, 2, 3, 4};
    auto vi = v.begin();
    auto li = l.begin();
    std::cout << my_advance(vi, 2) << ' ' << *vi << " | " << my_advance(li, 2) << ' ' << *li << '\n';
}
// expect: O(1) jump 3 | O(n) walk 3
```
The tags are empty structs that inherit from each other (`bidirectional_iterator_tag` derives from `forward_iterator_tag`, which derives from `input_iterator_tag`). Overload resolution therefore picks the most specific overload the iterator qualifies for. This is how `std::advance` itself is written; C++20 replaces it with concept-constrained overloads ([[Iterator Categories and Concepts]]).

### Write Your Own Forward Iterator (C++17, Checked by C++20)
```cpp
#include <cstddef>
#include <iostream>
#include <iterator>
#include <numeric>

class Countdown {                                    // the sequence n, n-1, ..., 1 with no storage
public:
    class iterator {
    public:
        using iterator_category = std::forward_iterator_tag;   // the five names the library looks for
        using value_type        = int;
        using difference_type   = std::ptrdiff_t;
        using pointer           = const int*;
        using reference         = const int&;

        iterator() = default;
        explicit iterator(int v) : v_(v) {}
        reference operator*() const { return v_; }
        iterator& operator++() { --v_; return *this; }
        iterator operator++(int) { iterator old = *this; --v_; return old; }
        friend bool operator==(iterator a, iterator b) { return a.v_ == b.v_; }
        friend bool operator!=(iterator a, iterator b) { return !(a == b); }
    private:
        int v_ = 0;
    };
    explicit Countdown(int n) : n_(n) {}
    iterator begin() const { return iterator(n_); }
    iterator end() const { return iterator(0); }
private:
    int n_;
};

#if __cplusplus >= 202002L
static_assert(std::forward_iterator<Countdown::iterator>);    // C++20: the compiler audits the promise
#endif

int main() {
    Countdown c(4);
    for (int x : c) std::cout << x;
    std::cout << ' ' << std::accumulate(c.begin(), c.end(), 0) << '\n';
}
// expect: 4321 10
```
Declare the five member types yourself; the `std::iterator` base class that used to supply them is deprecated since C++17. In C++20 a `static_assert` on the concept turns "I think this is a forward iterator" into a checked fact.

### Read a Whole Stream into a string
```cpp
#include <iostream>
#include <iterator>
#include <sstream>
#include <string>

int main() {
    std::istringstream file("line one\nline  two\n");    // an ifstream works the same way
    std::string all{std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>{}};
    std::cout << all.size() << '\n';                      // whitespace and newlines kept
}
// expect: 19
```
`istreambuf_iterator` reads raw characters from the stream buffer. `istream_iterator<char>` would skip whitespace and run slower, because each character goes through `>>` ([[Header — streambuf]]).

### Bounded and Unbounded Ranges with Sentinels (C++20)
```cpp
// cc: std=c++20
#include <algorithm>
#include <iostream>
#include <iterator>
#include <list>

int main() {
    std::list<int> l{5, 6, 7, 8, 9};
    std::counted_iterator first3(l.begin(), 3);                 // "3 elements from here"
    int sum = 0;
    for (auto it = first3; it != std::default_sentinel; ++it) sum += *it;

    int data[] = {4, 9, 2, -1, 7};                              // -1 marks the end, like '\0' in C strings
    auto stop = std::ranges::find(data, std::unreachable_sentinel, -1);   // no bounds check: -1 must exist
    std::cout << sum << ' ' << (stop - data) << '\n';
}
// expect: 18 3
```
A **sentinel** is "whatever tells you to stop", and in C++20 it no longer has to be the same type as the iterator. `counted_iterator` stops by count; `unreachable_sentinel` never stops, which removes the end check from the loop when you *know* the value exists.

## Key Concepts

### Half-Open Ranges and the Past-the-End Iterator
Every range is `[first, last)`: `first` points at the first element, `last` one position **past** the final one. An empty range is simply `first == last`, the loop condition is always `it != last`, and splitting a range at `mid` gives `[first, mid)` + `[mid, last)` with no overlap. The past-the-end iterator may be compared and (for bidirectional iterators) decremented, but **never dereferenced**.

### Valid, Dereferenceable, Singular
An iterator can be in one of three states. It can be **dereferenceable** (points at an element). It can be **past-the-end** (valid, but `*it` is undefined behavior). Or it can be **singular**, like a default-constructed iterator or one invalidated by a container change. On a singular iterator almost everything is undefined behavior; you may only assign to it or destroy it (and copy it, if it was value-initialized). See [[Iterator Invalidation]] and [[Undefined Behavior]].

### Categories Are Promises About Cost
The categories don't say what's *possible*; they say what's possible **in constant time**. You could reach element 1000 of a `list` by stepping; the list iterator refuses `it + 1000` because that would hide an O(n) walk behind syntax that looks O(1). `std::advance` and `std::distance` are the explicit way to pay that cost ([[Iterator Categories and Concepts]]).

### Two Generations: Named Requirements vs Concepts
Before C++20, categories were *named requirements* (LegacyForwardIterator, ...): documentation plus an `iterator_category` typedef, not checked by the compiler. C++20 adds real **concepts** (`std::forward_iterator`, ...) that the compiler checks, plus associated-type aliases (`iter_value_t<I>`) that replace most uses of `iterator_traits`. The two are close but not identical. For example, a C++20 `forward_iterator` may return a value (not a reference) from `*it`, which the legacy rules forbade.

### Sentinels (C++20)
C++20 relaxes "a range is two iterators of the same type" to "an iterator and a **sentinel**", where the sentinel is any type comparable with the iterator. That's how "until the null terminator", "until the stream fails" and "n elements from here" become ranges without inventing a fake end iterator. `std::ranges` algorithms accept iterator/sentinel pairs; classic `std::` algorithms still need matching types, which `common_iterator` provides.

### Insert Iterators Change the Meaning of `=`
Algorithms write with `*out++ = value`. An insert iterator makes `*` and `++` do nothing and turns `=` into `push_back`, `push_front` or `insert`. That is the whole trick that lets an algorithm "grow" a container it knows nothing about.

### Stream Iterators Are Single-Pass
Reading from an `istream_iterator` consumes the input. Copies of the iterator share the same stream, so you cannot rewind by keeping an old copy. Algorithms that need two passes (for example `std::max_element` followed by a second scan, or anything requiring forward iterators) must first copy the data into a container.

### `iter_move`, `iter_swap` and Proxy References
Some iterators don't return `T&` from `*it`. `vector<bool>` returns a proxy object, and zip-style views return tuples of references. `std::move(*it)` does the wrong thing for those, so C++20 algorithms call `std::ranges::iter_move(it)` and `iter_swap`, which types can customize ([[Header — vector]], "`vector<bool>` Is Not a Container of `bool`").

## Choosing a Tool

```text
Need                                                Best choice
─────────────────────────────────────────────────────────────────────────────────────
Algorithm output into an EMPTY container            std::back_inserter(v)       (vector/deque/list/string)
Output into a set or map                            std::inserter(s, s.end())
Read whitespace-separated values from a stream      std::istream_iterator<T>
Read a whole file verbatim                          std::istreambuf_iterator<char>
Print a range quickly                               std::ostream_iterator<T>(out, sep)  or std::format (C++20)
Iterate backwards                                   rbegin()/rend(), or std::views::reverse (C++20)
Step n positions on ANY iterator                    std::next / std::prev / std::advance
Count elements between two iterators                std::distance  (O(n) unless random access)
Transfer elements out of a container                std::make_move_iterator
Template that must accept T[N] as well as containers std::begin / std::end / std::size
Signed loop bound without warnings                  std::ssize (C++20)
Restrict a template to cheap random access          std::random_access_iterator<I> (C++20) or a tag check (C++14/17)
"The first n elements" / "until a marker"           std::counted_iterator / a sentinel (C++20)
```

## Best Practices

1. **Compare with `!=`, not `<`**, in iterator loops: every category supports `!=`
2. **Use `cbegin()`/`cend()`** (or a `const&` range-for) when you only read
3. **Give output algorithms room**: an insert iterator for an empty container, or `resize` first
4. **Use `std::next`/`std::prev`/`std::distance`** instead of `+`/`-` in generic code, so it compiles for every category
5. **Never dereference `end()`**, and never hold an iterator across a call that may invalidate it
6. **Convert a `reverse_iterator` with `std::prev(r.base())`**, never plain `r.base()`
7. **Declare the five member types yourself** when writing an iterator; don't inherit from the deprecated `std::iterator`
8. **In C++20, constrain templates with iterator concepts** and `static_assert` your own iterators against them
9. **Prefer `std::begin(c)`/`std::size(c)`** in templates that might receive a built-in array
10. **Copy single-pass input into a container** before running any algorithm that needs two passes

## Related Headers

```cpp
#include <iterator>    // this card: operations, adaptors, stream iterators, traits, concepts, begin/end/size
#include <algorithm>   // the algorithms that consume iterators: copy, find, sort, ...
#include <numeric>     // accumulate, iota, reduce: numeric algorithms over iterator ranges
#include <ranges>      // C++20: views and range algorithms built on iterators + sentinels
#include <concepts>    // C++20: core concepts the iterator concepts are built from
#include <vector>      // (and every container) also provides std::begin/end/size for its type
#include <iosfwd>      // declarations of the stream classes the stream iterators wrap
```

## Connections

- **Hub:** [[Map — Standard Headers]]
- **Concept notes (the why behind this card):** [[Iterators]] · [[Iterator Categories and Concepts]] · [[STL Architecture — Containers, Iterators, Algorithms]] · [[Iterator Invalidation]] · [[Ranges and Views]] · [[Concepts and Constraints]]
- **Hazards:** [[Undefined Behavior]] (dereferencing `end()`, singular iterators) · [[The Moved-From State]] (after `make_move_iterator`)
- **Sibling cards:** [[Header — vector]] · [[Header — algorithm]] · [[Header — ranges]] · [[Header — iostream]] · [[Header — streambuf]]
- **Practice:** *Continuum #23 STL Container & Algorithm Playground* (rewrite each hand loop with an adaptor from this card) · *#7 Word & Text Analyzer* (read words with `istream_iterator<std::string>`)

## Sources

- Primer §3.4 "Introducing Iterators" (p. 106) and §3.4.2 "Iterator Arithmetic" (p. 111): `begin`/`end`, half-open ranges, which types support arithmetic.
- Primer §10.4 "Revisiting Iterators" (p. 401): insert iterators (p. 401), `iostream` iterators (p. 403) and reverse iterators with the `base()` offset (p. 407).
- Primer §10.5.1 "The Five Iterator Categories" (p. 410): what each category guarantees and why algorithms name the weakest they need.
- Primer §13.6.2 (p. 543): move iterators and `make_move_iterator`.
- Tour §13.2 "Use of Iterators" (p. 175), §13.3 "Iterator Types" (p. 178, stream iterators p. 179): iterators as the algorithm/container glue.
- Tour §14.5.2 "Iterator Concepts" (p. 192): the C++20 iterator concepts, sentinels, and `sortable`/`mergeable`/`permutable`.
- PPP ch. 19 "Containers and Iterators", §19.2 "Sequences and iterators": the half-open sequence built up from first principles.
- cppreference / web, *Iterator library*: https://en.cppreference.com/w/cpp/iterator (the page this card was built from: categories, definitions, concepts, primitives, adaptors, operations, range access, defect reports)
- cppreference / web, *`<iterator>`*: https://en.cppreference.com/w/cpp/header/iterator
- C++ Core Guidelines ES.55 "Avoid the need for range checking" and ES.71 "Prefer a range-for-statement to a for-statement when there is a choice": https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
