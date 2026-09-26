---
id: hdr-list
title: Header — list
aliases:
- <list>
- std::list
- doubly linked list
- splice
type: header
domain: HDR
tier: 2
status: draft
standard: C++98
prereqs:
- "[[Sequence Containers Compared]]"
related:
- "[[Sequence Containers Compared]]"
- "[[Iterator Invalidation]]"
- "[[Iterators]]"
- "[[Iterator Categories and Concepts]]"
- "[[STL Architecture — Containers, Iterators, Algorithms]]"
tags:
- type/header
- domain/hdr
- tier/2
- header/list
- tension/abstraction-vs-control
- tension/safety-vs-performance
created: 2026-09-26
updated: 2026-09-26
header: <list>
---

# Header — list

> [!essence]
> **`<list>`** provides `std::list<T>`, a **doubly linked list**: every element lives in its own heap node that points to the node before and the node after. That buys one thing no other standard sequence offers: **elements never move**. Inserting, erasing, sorting or even moving elements to *another list* only rewires pointers, so every other iterator, pointer and reference stays valid. The price is no indexing, O(n) search, two pointers of overhead per element, and a cache miss on almost every step.

> [!standard] Versions
> C++98 (`list`, `splice`, `merge`, member `sort`/`unique`/`remove`/`remove_if`/`reverse`) / C++11 (move semantics, `emplace`, `emplace_front`/`emplace_back`, initializer lists, `cbegin`/`crbegin`, **`size()` guaranteed O(1)**) / C++17 (`emplace_front`/`emplace_back` return a reference, class template argument deduction, `std::pmr::list`, incomplete element types allowed) / C++20 (`remove`, `remove_if` and `unique` return the number removed; `std::erase`/`std::erase_if`; `<=>` replaces `<`, `>`, `<=`, `>=`, `!=`) / C++23 (`from_range` constructor, `assign_range`, `insert_range`, `append_range`, `prepend_range`) / C++26 (`constexpr` list)

## Memory Layout

A `std::list<int>` object holds a *sentinel* node (the permanent position of `end()`) and a size counter: 24 bytes in libstdc++. Each element is a separately allocated node holding two pointers and the value (24 bytes for an `int` in libstdc++, before the allocator's own overhead).

```text
            ┌──────────────────── circular: 30's next and S's prev link back around ──────────────┐
            ▼                                                                                     │
  ┌───────────────────┐      ┌───────────────┐      ┌───────────────┐      ┌───────────────┐      │
  │ sentinel S        │ ───▶ │  prev │ next  │ ───▶ │  prev │ next  │ ───▶ │  prev │ next  │ ─────┘
  │ (inside the list  │ ◀─── │   value: 10   │ ◀─── │   value: 20   │ ◀─── │   value: 30   │
  │ object) size = 3  │      └───────────────┘      └───────────────┘      └───────────────┘
  └───────────────────┘
  end() points at S        begin()                                       std::prev(end())
```

Compare [[Header — vector]]: one contiguous block, elements side by side. Walking a `list` means loading `next`, waiting for that memory, then loading the next `next`: every step can be a cache miss. That's why a `vector` usually beats a `list` even for inserting in the middle, unless the elements are large or you already hold the position ([[Sequence Containers Compared]]).

## Quick Reference

```cpp
// cc: fragment
// ═══════════════════════════════════════════════════════════════════════════
// CONSTRUCTION & ASSIGNMENT
// ═══════════════════════════════════════════════════════════════════════════
std::list<int> l;                       // none        | Empty (no nodes)      |
std::list<int> l(5);                    // count       | 5 value-initialized   | {0,0,0,0,0}
std::list<int> l(5, 7);                 // count, value| 5 copies of 7         | ← PARENTHESES
std::list<int> l{5, 7};                 // init list   | Exactly these values  | {5,7}  ← BRACES: different!
std::list<int> l(first, last);          // iterators   | Copy any range        |
std::list<int> l(std::move(other));     // rvalue      | Steal all nodes       | O(1); other left empty
std::list l{1, 2, 3};                   // init list   | CTAD → list<int>      | C++17
std::list<int> l(std::from_range, r);   // range       | Copy any range        | C++23
l = other;  l.assign(n, v);  l.assign(first, last);  l.assign({1, 2});
l.assign_range(r)                       // range       | Replace contents      | C++23

// ═══════════════════════════════════════════════════════════════════════════
// ELEMENT ACCESS  (no operator[], no at(): there is no index)
// ═══════════════════════════════════════════════════════════════════════════
l.front()  /  l.back()                  // none        | First / last element  | UB on an empty list
*std::next(l.begin(), k)                // it, k       | The k-th element      | O(k) walk: a smell if frequent

// ═══════════════════════════════════════════════════════════════════════════
// ITERATORS  (bidirectional: ++ and --, but no +n, no <, no [])
// ═══════════════════════════════════════════════════════════════════════════
l.begin() / l.end()  /  l.cbegin() / l.cend()          // cbegin/cend: C++11
l.rbegin() / l.rend() /  l.crbegin() / l.crend()       // crbegin/crend: C++11

// ═══════════════════════════════════════════════════════════════════════════
// SIZE  (no capacity: memory is per node)
// ═══════════════════════════════════════════════════════════════════════════
l.size()                                // none        | Element count         | O(1) since C++11 (was allowed O(n))
l.empty()                               // none        | size() == 0?          |
l.resize(n)  /  l.resize(n, v)          // count       | Grow or shrink at the back |

// ═══════════════════════════════════════════════════════════════════════════
// MODIFIERS  (all O(1) once you have the position; NO other iterator is invalidated)
// ═══════════════════════════════════════════════════════════════════════════
l.push_front(x)  /  l.push_back(x)      // T           | Add at either end     | O(1)
l.emplace_front(args...) / l.emplace_back(args...)     // Construct in place  | C++11; return T& since C++17
l.pop_front()  /  l.pop_back()          // none        | Remove at either end  | UB on an empty list
l.insert(pos, x)                        // iter, T     | Insert before pos     | O(1); returns iterator to the new element
l.insert(pos, n, x) / insert(pos, first, last) / insert(pos, {…})
l.emplace(pos, args...)                 // iter, args  | Construct before pos  | C++11
l.insert_range(pos, r) / l.append_range(r) / l.prepend_range(r)   // C++23
l.erase(pos)  /  l.erase(first, last)   // iterators   | Remove                | Returns iterator to the next element
l.clear()                               // none        | Remove all            | O(n); frees every node
l.swap(other)                           // list        | Exchange contents     | O(1); iterators follow their elements

// ═══════════════════════════════════════════════════════════════════════════
// LIST OPERATIONS  (members: they relink nodes instead of copying values)
// ═══════════════════════════════════════════════════════════════════════════
l.splice(pos, other)                    // iter, list  | Move ALL of other before pos       | O(1)
l.splice(pos, other, it)                // + iterator  | Move ONE node before pos           | O(1)
l.splice(pos, other, first, last)       // + range     | Move a range before pos            | O(1) same list, else O(range) (size count)
l.merge(other)  /  l.merge(other, cmp)  // sorted list | Merge sorted other into sorted l   | O(n+m), stable; other ends empty
l.sort()  /  l.sort(cmp)                // none        | Sort by relinking                  | O(n log n), stable
l.unique()  /  l.unique(pred)           // none        | Drop ADJACENT duplicates           | Returns count since C++20 (void before)
l.remove(v)  /  l.remove_if(pred)       // value/pred  | Erase all matches                  | Returns count since C++20 (void before)
l.reverse()                             // none        | Reverse order                      | O(n), no element copied

// ═══════════════════════════════════════════════════════════════════════════
// NON-MEMBERS
// ═══════════════════════════════════════════════════════════════════════════
std::erase(l, v)  /  std::erase_if(l, pred)            // Remove matches, return count  | C++20
a == b,  a <=> b                        // Element-wise, lexicographic          | <=> C++20
std::swap(a, b)                         // O(1)
std::pmr::list<T>                       // list with a memory_resource          | C++17
```

## Patterns

### Build and Traverse
```cpp
#include <iostream>
#include <list>
#include <string>

int main() {
    std::list<std::string> tasks{"write", "test"};
    tasks.push_front("plan");                    // O(1) at the front: vector can't do that cheaply
    tasks.emplace_back("ship");                  // constructed in place inside a new node
    for (const auto& t : tasks) std::cout << t << ' ';
    for (auto it = tasks.rbegin(); it != tasks.rend(); ++it) std::cout << (*it)[0];   // backwards
    std::cout << '\n';
}
// expect: plan write test ship stwp
```

### Iterators That Stay Valid (the Reason to Choose a list)
```cpp
#include <iostream>
#include <list>

int main() {
    std::list<int> jobs{10, 20, 30};
    auto mine = std::next(jobs.begin());         // a handle to the element 20
    for (int i = 0; i < 1000; ++i) jobs.push_front(i);   // with vector, `mine` would dangle long ago
    jobs.erase(jobs.begin());                    // erasing OTHER elements doesn't touch it either
    jobs.push_back(40);
    std::cout << *mine << ' ' << jobs.size() << '\n';
}
// expect: 20 1003
```
Only the erased element's iterators die. Everything else, including `end()`, survives inserts, erases, `sort`, `reverse` and `splice` ([[Iterator Invalidation]]).

### Insert in the Middle
```cpp
#include <algorithm>
#include <iostream>
#include <list>

int main() {
    std::list<int> l{10, 20, 40, 50};
    auto pos = std::find(l.begin(), l.end(), 40);   // O(n): finding is the expensive part
    auto it = l.insert(pos, 30);                    // O(1): link one node before pos
    l.insert(it, {25, 27});                         // several at once, before 30
    for (int x : l) std::cout << x << ' ';
    std::cout << '\n';
}
// expect: 10 20 25 27 30 40 50
```
"O(1) insertion" only pays off if you already hold the position, or the search is needed anyway.

### Erase While Looping
```cpp
#include <iostream>
#include <list>

int main() {
    std::list<int> l{1, 2, 3, 4, 5, 6};
    for (auto it = l.begin(); it != l.end(); ) {
        if (*it % 2 == 0) it = l.erase(it);          // erase returns the next position
        else ++it;
    }
    for (int x : l) std::cout << x;
    std::cout << '\n';
}
// expect: 135
```
Never `++it` after erasing `it`. For simple conditions use `remove_if` (next pattern).

### Remove by Value or Condition
```cpp
#include <iostream>
#include <list>

int main() {
    std::list<int> l{4, -1, 7, -3, 4, 9};
    l.remove(4);                                     // member: unlinks every 4, no shifting
    l.remove_if([](int x) { return x < 0; });        // C++20: returns how many were removed
    for (int x : l) std::cout << x << ' ';
    std::cout << l.size() << '\n';
}
// expect: 7 9 2
```
Use the **member** `remove`, not the algorithm `std::remove`. The algorithm shuffles values towards the front and needs a follow-up `erase`; the member just unlinks nodes. C++20's `std::erase(l, 4)` / `std::erase_if(l, pred)` do the same with a uniform syntax.

### Sort a list (Member `sort`, Stable)
```cpp
#include <iostream>
#include <list>
#include <string>
#include <utility>

int main() {
    std::list<std::pair<int, std::string>> l{{2, "b"}, {1, "x"}, {2, "a"}, {1, "y"}};
    // std::sort(l.begin(), l.end());               // ✗ does not compile: needs random access
    l.sort([](const auto& a, const auto& b) { return a.first < b.first; });
    for (const auto& p : l) std::cout << p.first << p.second << ' ';
    std::cout << '\n';
}
// expect: 1x 1y 2b 2a
```
`list::sort` is a **stable** merge sort that relinks nodes; no element is copied or moved, so iterators still point at the same values afterwards. Equal keys keep their original order (`x` before `y`, `b` before `a`).

### Remove Duplicates
```cpp
#include <iostream>
#include <list>

int main() {
    std::list<int> l{3, 1, 3, 2, 1, 3};
    l.sort();                                        // 1 1 2 3 3 3
    l.unique();                                      // removes ADJACENT equals only
    for (int x : l) std::cout << x;
    std::cout << '\n';
}
// expect: 123
```

### An LRU Cache: splice Moves a Node in O(1) (C++17)
```cpp
#include <iostream>
#include <list>
#include <string>
#include <unordered_map>

class LruCache {
public:
    explicit LruCache(std::size_t cap) : cap_(cap) {}
    void put(const std::string& key, int value) {
        if (auto f = index_.find(key); f != index_.end()) { f->second->second = value; touch(f->second); return; }
        order_.emplace_front(key, value);            // newest at the front
        index_[key] = order_.begin();                // iterator stays valid for the node's lifetime
        if (order_.size() > cap_) { index_.erase(order_.back().first); order_.pop_back(); }
    }
    int* get(const std::string& key) {
        auto f = index_.find(key);
        if (f == index_.end()) return nullptr;
        touch(f->second);
        return &f->second->second;
    }
private:
    using Order = std::list<std::pair<std::string, int>>;
    void touch(Order::iterator it) { order_.splice(order_.begin(), order_, it); }   // relink to front
    std::size_t cap_;
    Order order_;
    std::unordered_map<std::string, Order::iterator> index_;
};

int main() {
    LruCache c(2);
    c.put("a", 1); c.put("b", 2);
    c.get("a");                                      // "a" becomes most recent
    c.put("c", 3);                                   // evicts "b", the least recent
    std::cout << (c.get("b") ? "b " : "-b ") << *c.get("a") << *c.get("c") << '\n';
}
// expect: -b 13
```
This is the textbook reason `std::list` exists: the hash map stores **iterators into the list**, which would be invalidated by any `vector` growth, and `splice` moves a node to the front without allocating or copying.

### Move Elements Between Lists (splice)
```cpp
#include <iostream>
#include <iterator>
#include <list>

int main() {
    std::list<int> todo{1, 2, 3, 4, 5};
    std::list<int> done;
    auto first = todo.begin();
    auto last  = std::next(first, 3);
    auto keep  = std::next(first);                   // points at 2
    done.splice(done.end(), todo, first, last);      // relink 1 2 3 into `done`
    std::cout << todo.size() << ' ' << done.size() << ' ' << *keep << '\n';
}
// expect: 2 3 2
```
`keep` is still valid: it now refers to an element of `done`. No node was allocated, freed, copied or moved. Both lists must use equal allocators.

### Merge Two Sorted Lists
```cpp
#include <iostream>
#include <list>

int main() {
    std::list<int> a{1, 4, 9};
    std::list<int> b{2, 3, 10};
    a.merge(b);                                      // both must already be sorted
    for (int x : a) std::cout << x << ' ';
    std::cout << "| b has " << b.size() << '\n';
}
// expect: 1 2 3 4 9 10 | b has 0
```

### Walk to a Position (No Random Access)
```cpp
#include <iostream>
#include <iterator>
#include <list>

int main() {
    std::list<char> l{'a', 'b', 'c', 'd', 'e'};
    auto it = std::next(l.begin(), 2);               // l.begin() + 2 does not compile
    std::advance(it, -1);                            // bidirectional: going back is allowed
    std::cout << *it << *std::prev(l.end()) << ' '
              << std::distance(l.begin(), l.end()) << '\n';   // O(n); prefer l.size(), which is O(1)
}
// expect: be 5
```
See [[Header — iterator]] for `next`/`prev`/`advance`/`distance` and [[Iterator Categories and Concepts]] for why `+ 2` is refused.

### Store Types That Can't Move (C++17)
```cpp
#include <iostream>
#include <list>
#include <mutex>

struct Account {
    int balance = 0;
    std::mutex m;                                    // not copyable, not movable
};

int main() {
    std::list<Account> accounts;                     // vector<Account> couldn't grow: growth moves elements
    accounts.emplace_back();                         // default-constructed inside a node
    accounts.emplace_back().balance = 50;            // C++17: emplace_back returns a reference
    for (auto& a : accounts) { std::lock_guard<std::mutex> g(a.m); a.balance += 1; }
    std::cout << accounts.back().balance << '\n';
}
// expect: 51
```
Because nodes never relocate, `list` holds types a `vector` can't grow with (mutexes, atomics, objects others hold pointers to). `std::deque` can also do this if you only add at the ends.

## Key Concepts

### Node-Based: Elements Never Move
Each element is allocated once, in its own node, and stays at that address until erased. Every operation (insert, erase, `sort`, `merge`, `reverse`, `splice`, `swap`) changes only the `prev`/`next` pointers. This is the one property that justifies `std::list`.

### Iterator Invalidation
| Operation | Invalidates |
|---|---|
| `insert`, `emplace`, `push_*`, `splice`, `merge`, `sort`, `reverse` | **Nothing** |
| `erase`, `pop_*`, `remove`, `remove_if`, `unique`, `resize` (shrinking) | Only the erased elements |
| `clear` | All elements (the `end()` iterator stays valid) |
| `swap` | Nothing: iterators now refer into the *other* list |

Compare the much harsher table in [[Header — vector]].

### O(1) Insert and Erase, but O(n) to Find
The O(1) is for the *link* operation at a position you already have. Getting that position by searching is O(n), and every step of the search may be a cache miss. Benchmarks usually show `vector` + shifting beating `list` for small elements even for middle insertions, because shifting contiguous memory is fast and the search dominates ([[Sequence Containers Compared]]).

### Bidirectional Iterators Only
`++it` and `--it` work; `it + n`, `it[n]`, `it < other` and `last - first` don't, because they would hide an O(n) walk ([[Iterator Categories and Concepts]]). Algorithms needing random access (`std::sort`, `std::binary_search`'s speed guarantee, `std::nth_element`) either refuse or degrade.

### Why `list` Has Its Own `sort`, `merge`, `remove`, `unique`, `reverse`
Generic algorithms work by copying or moving *values* between positions. A list can do the same jobs by *relinking nodes*, which never copies a value and keeps every iterator valid. `std::sort` doesn't compile on a list at all. The members also do the full job in one step, e.g. `l.remove(x)` actually erases, while `std::remove` would only shuffle values. Use the members (Primer §10.6).

### `size()` Is O(1), So Cross-List `splice` of a Range Is Not
C++11 required `size()` to be constant time, so each list stores a count. Splicing a *range* from another list must count the moved nodes to update both sizes: O(length of range). Splicing a whole list, a single node, or a range within the same list is still O(1).

### Memory Cost
Per element: the value, two pointers, plus the allocator's per-allocation overhead (often 8–16 bytes). A `list<int>` can use 6–8× the memory of a `vector<int>`, and each node is a separate `new`/`delete`. `std::pmr::list` with a `monotonic_buffer_resource` or `unsynchronized_pool_resource` (C++17) makes the allocations cheap and keeps nodes closer together.

### `list` vs `forward_list`
`std::forward_list` (C++11, `<forward_list>`) is singly linked: one pointer per node, no `size()`, no backward iteration, and operations named `insert_after`/`erase_after`/`splice_after` because you can only reach the *next* node. Use it only when the memory for the second pointer matters.

## Choosing a Tool

```text
Need                                                        Best choice
──────────────────────────────────────────────────────────────────────────────────────────────
Default sequence; iterate, index, append                    std::vector              (<vector>)
Fast push/pop at BOTH ends, indexing still needed           std::deque               (<deque>)
Iterators/pointers to elements must survive any insert/erase std::list
Move elements or sub-ranges between sequences in O(1)       std::list  (splice)
LRU cache, ordered "recently used" set                      std::list + unordered_map<key, list::iterator>
Elements that can't be moved or copied (mutex, atomic)      std::list  (or std::deque at the ends)
Same, but memory is tight and forward traversal suffices    std::forward_list        (<forward_list>)
Sorted, with lookup by key                                  std::set / std::map      (<set>, <map>)
Frequent middle insertion of SMALL elements                 std::vector (measure: it usually wins)
```

## Best Practices

1. **Default to `std::vector`**; choose `list` for a specific reason: stable iterators, splicing, or non-movable elements
2. **Store `list::iterator`s as handles** when other structures must point at elements (the LRU pattern)
3. **Use the member operations** (`sort`, `remove`, `remove_if`, `unique`, `merge`, `reverse`); `std::sort` won't compile
4. **Erase in loops with `it = l.erase(it)`**, never `++` an erased iterator
5. **Use `splice` to move elements**, not erase + insert: no allocation, no copy, iterators stay valid
6. **Sort before `unique`**: it only removes adjacent duplicates
7. **Prefer `l.size()` to `std::distance`**: O(1) versus a full walk
8. **Don't index with `std::next(begin, k)` in a loop**: that's O(n²); keep an iterator instead
9. **Consider `std::pmr::list` or a pool** when you create and destroy many nodes
10. **Measure before replacing a `vector` with a `list` for "fast insertion"**: cache effects usually decide

## Related Headers

```cpp
#include <list>            // std::list, std::pmr::list (C++17), erase/erase_if (C++20)
#include <forward_list>    // std::forward_list: singly linked, one pointer per node
#include <vector>          // std::vector: the default sequence
#include <deque>           // std::deque: fast at both ends, random access
#include <unordered_map>   // pairs with list for LRU caches (map key → list::iterator)
#include <iterator>        // next, prev, advance, distance for bidirectional iterators
#include <algorithm>       // find, count, copy... (but use list's own sort/remove/unique)
#include <memory_resource> // C++17: pool allocators for node-heavy containers
```

## Connections

- **Hub:** [[Map — Standard Headers]]
- **Concept notes (the why behind this card):** [[Sequence Containers Compared]] · [[Iterator Invalidation]] · [[Iterators]] · [[Iterator Categories and Concepts]] · [[STL Architecture — Containers, Iterators, Algorithms]] · [[Erase-Remove and erase_if]]
- **Hazards:** [[Dangling Pointers and References]] (an erased node's iterators) · [[Undefined Behavior]] (`front()`/`pop_back()` on an empty list, splicing with unequal allocators)
- **Sibling cards:** [[Header — vector]] · [[Header — iterator]] · [[Header — algorithm]]
- **Practice:** *Continuum #23 STL Container & Algorithm Playground* (time `vector` vs `list` for middle insertion, with and without the search) · *#12 Build-Your-Own Dynamic Array* (then build the linked version and compare the layouts)

## Sources

- Primer §9.1 "Overview of the Sequential Containers" (p. 326): when to choose `list` over `vector`, `deque` and `forward_list`.
- Primer §9.3 "Sequential Container Operations" (p. 341; invalidation rules p. 353) and §10.6 "Container-Specific Algorithms" (p. 415): the member `sort`/`merge`/`remove`/`unique`/`reverse`/`splice` and why they exist.
- Tour §12.3 "list" (p. 162) and §12.4 "forward_list" (p. 164): the designer's advice to prefer `vector` unless there's a reason.
- PPP ch. 19, §19.3 "Linked lists" and §19.6 "vector, list, and string": building a linked list from first principles.
- Pikus ch. 4 "Memory Architecture and Performance" (p. 113; random memory access p. 124): why pointer-chasing structures pay for every cache miss.
- cppreference / web, *`std::list`*: https://en.cppreference.com/w/cpp/container/list (every member, complexity and invalidation note on this card)
- cppreference / web, *`<list>`*: https://en.cppreference.com/w/cpp/header/list
- C++ Core Guidelines SL.con.2 "Prefer using STL `vector` by default unless you have a reason to use a different container": https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
