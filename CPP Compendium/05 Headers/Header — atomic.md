---
id: hdr-atomic
title: Header — atomic
aliases:
- <atomic>
- std::atomic
- atomic_flag
- memory_order
type: header
domain: HDR
tier: 3
status: draft
standard: C++11
prereqs:
- "[[Atomics]]"
related:
- "[[Atomics]]"
- "[[The C++ Memory Model — happens-before]]"
- "[[Memory Orderings]]"
- "[[Data Races and Race Conditions]]"
- "[[Lock-Free Programming Basics]]"
tags:
- type/header
- domain/hdr
- tier/3
- header/atomic
- tension/safety-vs-performance
- tension/abstraction-vs-control
created: 2026-09-23
updated: 2026-09-23
header: <atomic>
---

# Header — atomic

> [!essence]
> **`<atomic>`** provides `std::atomic<T>`, a variable that several threads may read and write at the same time **without a data race**. Every operation on it is indivisible, and each operation takes a `memory_order` that says how it orders the surrounding ordinary reads and writes. It is the tool for flags, counters and single-value hand-offs. Anything that must keep several values consistent needs a mutex instead.

> [!standard] Versions
> C++11 (header, `atomic<T>`, `atomic_flag`, `memory_order`, fences) / C++17 (`is_always_lock_free`) / C++20 (`wait`/`notify_*`, `atomic_ref`, `atomic_flag::test`, floating-point `fetch_add`/`fetch_sub`, default constructor value-initializes, `memory_order::relaxed` spelling, `atomic<shared_ptr<T>>` in `<memory>`) / C++26 (`fetch_max`/`fetch_min`)

## Class Family

```text
std::atomic<T>                    primary template: T trivially copyable
├── atomic<bool>                  load/store/exchange/CAS only (no arithmetic)
├── atomic<integral>              + fetch_add/sub/and/or/xor, ++ -- += -= &= |= ^=
├── atomic<T*>                    + fetch_add/sub, ++ -- += -=   (pointer arithmetic)
├── atomic<floating-point>        + fetch_add/sub, += -=          (C++20)
└── atomic<shared_ptr<T>>/weak_ptr   in <memory>                  (C++20)
std::atomic_ref<T>                atomic operations on an ordinary object (C++20)
std::atomic_flag                  the only type GUARANTEED lock-free
std::memory_order                 relaxed · consume · acquire · release · acq_rel · seq_cst
```

## Quick Reference

```cpp
// cc: fragment
// ═══════════════════════════════════════════════════════════════════════════
// CONSTRUCTION  (not copyable, not movable)
// ═══════════════════════════════════════════════════════════════════════════
std::atomic<int> a{0};                  // value       | Initialize            | ALWAYS initialize in C++11/14/17
std::atomic<int> a;                     // none        | Default construct     | Value UNINITIALIZED before C++20; value-initialized (0) since C++20
std::atomic<bool> flag{false};          // bool        | Atomic flag           | load/store/exchange/CAS only
std::atomic<Node*> head{nullptr};       // pointer     | Atomic pointer        | Supports ++, --, +=, -=
std::atomic<int> b = a;                 // ✗ ERROR     | Copy is deleted       | Use: std::atomic<int> b{a.load()};
std::atomic_flag f = ATOMIC_FLAG_INIT;  // macro       | Clear flag            | Before C++20 the only portable init
std::atomic_flag f;                     // none        | Clear flag            | Guaranteed clear since C++20

// ═══════════════════════════════════════════════════════════════════════════
// LOAD / STORE / EXCHANGE  (all types)
// ═══════════════════════════════════════════════════════════════════════════
a.load()                                // [order]     | Read                  | Default order: seq_cst
a.load(std::memory_order_acquire)       // order       | Read, acquire         |
a.store(v)                              // T [,order]  | Write                 | Returns void
a = v                                   // T           | Write (seq_cst)       | Returns v, NOT a reference
int x = a;                              // implicit    | Read (seq_cst)        | operator T()
a.exchange(v)                           // T [,order]  | Write, return old     | "Take and replace"
a.is_lock_free()                        // none        | Lock-free at runtime? | bool
std::atomic<T>::is_always_lock_free     // constexpr   | Lock-free always?     | C++17, usable in static_assert

// ═══════════════════════════════════════════════════════════════════════════
// COMPARE-AND-SWAP  (all types)
// ═══════════════════════════════════════════════════════════════════════════
a.compare_exchange_strong(expected, desired)   // if a == expected: a = desired, true
                                               // else: expected = a (UPDATED!), false
a.compare_exchange_weak(expected, desired)     // Same, but may fail spuriously: use in a loop
a.compare_exchange_weak(exp, des, success_order, failure_order)

// ═══════════════════════════════════════════════════════════════════════════
// READ-MODIFY-WRITE  (integral & pointer; float/double since C++20)
// ═══════════════════════════════════════════════════════════════════════════
a.fetch_add(n)  /  a.fetch_sub(n)       // T [,order]  | Add / subtract        | Return the OLD value
a.fetch_and(m)  /  a.fetch_or(m)  /  a.fetch_xor(m)    // integral only         | Return the OLD value
a.fetch_max(n)  /  a.fetch_min(n)       // T [,order]  | Atomic max / min      | C++26
++a  a++  --a  a--                      // none        | Increment / decrement | seq_cst; pre-forms return NEW value
a += n  a -= n  a &= m  a |= m  a ^= m  // T           | Compound assignment   | Return the NEW value

// ═══════════════════════════════════════════════════════════════════════════
// WAIT / NOTIFY  (C++20): block until the value changes, no busy-wait
// ═══════════════════════════════════════════════════════════════════════════
a.wait(old)                             // T [,order]  | Sleep while a == old  | May wake spuriously; re-checks
a.notify_one()  /  a.notify_all()       // none        | Wake waiters          | Call after changing the value

// ═══════════════════════════════════════════════════════════════════════════
// ATOMIC_FLAG
// ═══════════════════════════════════════════════════════════════════════════
f.test_and_set([order])                 // Set to true, return OLD value   | C++11
f.clear([order])                        // Set to false                    | C++11
f.test([order])                         // Read without setting            | C++20
f.wait(old) / f.notify_one() / f.notify_all()                              // C++20

// ═══════════════════════════════════════════════════════════════════════════
// MEMORY ORDERS & FENCES
// ═══════════════════════════════════════════════════════════════════════════
std::memory_order_relaxed               // Atomicity only; no ordering of other memory
std::memory_order_acquire               // Loads: later reads/writes can't move before it
std::memory_order_release               // Stores: earlier reads/writes can't move after it
std::memory_order_acq_rel               // RMW ops: both of the above
std::memory_order_seq_cst               // Default: one global order of all seq_cst ops
std::memory_order_consume               // Discouraged: compilers treat it as acquire
std::memory_order::relaxed              // C++20 spelling (enum class + inline constants)
std::atomic_thread_fence(order)         // Standalone fence between threads
std::atomic_signal_fence(order)         // Fence between a thread and its signal handler

// ═══════════════════════════════════════════════════════════════════════════
// C-STYLE FREE FUNCTIONS & MACROS  (mainly for C interop)
// ═══════════════════════════════════════════════════════════════════════════
std::atomic_load(&a) / std::atomic_store(&a, v) / std::atomic_fetch_add(&a, n) ...  // + _explicit forms
std::atomic_ref<int> r(plain_int);      // Atomic view of a non-atomic object     | C++20
ATOMIC_INT_LOCK_FREE                    // 0 never · 1 sometimes · 2 always lock-free
std::atomic_int / atomic_size_t / ...   // Aliases for atomic<int>, atomic<size_t>, ...
```

## Patterns

### A Stop Flag Shared with a Worker Thread
```cpp
#include <atomic>
#include <chrono>
#include <iostream>
#include <thread>

int main() {
    std::atomic<bool> stop{false};
    std::atomic<int> beats{0};
    std::thread worker([&] {
        while (!stop.load()) {                        // no data race: atomic read
            ++beats;
            std::this_thread::sleep_for(std::chrono::milliseconds(5));
        }
    });
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    stop = true;                                      // atomic write, seen by the worker
    worker.join();
    std::cout << (beats > 0 ? "worker ran and stopped" : "never ran") << '\n';
}
// expect: worker ran and stopped
```

### A Counter Incremented from Many Threads
```cpp
#include <atomic>
#include <iostream>
#include <thread>
#include <vector>

int main() {
    std::atomic<long> hits{0};
    std::vector<std::thread> pool;
    for (int t = 0; t < 4; ++t)
        pool.emplace_back([&] {
            for (int i = 0; i < 100000; ++i)
                hits.fetch_add(1, std::memory_order_relaxed);   // only the count matters
        });
    for (auto& th : pool) th.join();                   // join() makes all increments visible
    std::cout << hits.load() << '\n';
}
// expect: 400000
```

### Publishing Data with Release / Acquire
```cpp
#include <atomic>
#include <iostream>
#include <string>
#include <thread>

int main() {
    std::string payload;                               // ordinary, non-atomic data
    std::atomic<bool> ready{false};

    std::thread producer([&] {
        payload = "sensor calibrated";                 // 1. write the data
        ready.store(true, std::memory_order_release);  // 2. publish: data write can't sink below
    });
    std::thread consumer([&] {
        while (!ready.load(std::memory_order_acquire)) {}   // 3. acquire pairs with release
        std::cout << payload << '\n';                  // 4. guaranteed to see step 1
    });
    producer.join();
    consumer.join();
}
// expect: sensor calibrated
```

### Atomic Maximum with a Compare-Exchange Loop (before C++26)
```cpp
#include <atomic>

void update_max(std::atomic<int>& best, int candidate) {
    int current = best.load(std::memory_order_relaxed);
    while (candidate > current &&
           !best.compare_exchange_weak(current, candidate, std::memory_order_relaxed)) {
        // on failure `current` now holds the latest value: the loop re-tests it
    }
}
// C++26: best.fetch_max(candidate);
```

### First Caller Wins (one-time action)
```cpp
#include <atomic>
#include <iostream>
#include <thread>
#include <vector>

std::atomic<bool> announced{false};
std::atomic<int> winners{0};

void try_announce() {
    if (!announced.exchange(true))                     // only one thread sees `false`
        ++winners;
}

int main() {
    std::vector<std::thread> pool;
    for (int i = 0; i < 8; ++i) pool.emplace_back(try_announce);
    for (auto& t : pool) t.join();
    std::cout << "winners: " << winners << '\n';
}
// expect: winners: 1
// For "run this initializer exactly once", std::call_once (<mutex>) or a
// function-local static is simpler.
```

### A Minimal Spinlock from atomic_flag
```cpp
#include <atomic>
#include <iostream>
#include <thread>

class Spinlock {
    std::atomic_flag locked_ = ATOMIC_FLAG_INIT;       // portable clear-init in C++11/14/17
public:
    void lock()   { while (locked_.test_and_set(std::memory_order_acquire)) {} }
    void unlock() { locked_.clear(std::memory_order_release); }
};

int main() {
    Spinlock lock;
    long total = 0;
    auto work = [&] { for (int i = 0; i < 50000; ++i) { lock.lock(); ++total; lock.unlock(); } };
    std::thread a(work), b(work);
    a.join(); b.join();
    std::cout << total << '\n';
}
// expect: 100000
// Teaching tool only: a std::mutex is usually as fast and never burns a core while waiting.
```

### Checking Lock-Freedom at Compile Time (C++17)
```cpp
#include <atomic>
#include <cstdint>
#include <iostream>

struct Pair { std::int32_t a, b; };                   // 8 bytes, trivially copyable

int main() {
    static_assert(std::atomic<int>::is_always_lock_free, "int atomics need a lock here");
    std::cout << std::boolalpha
              << std::atomic<Pair>::is_always_lock_free << '\n';   // true on x86-64
}
// A non-lock-free atomic silently uses a hidden lock: fine for correctness, not for
// signal handlers or lock-free algorithms. GCC may need -latomic for large T.
```

### Blocking Until a Value Changes (C++20 wait/notify)
```cpp
// cc: std=c++20
#include <atomic>
#include <iostream>
#include <thread>

int main() {
    std::atomic<int> stage{0};
    std::thread worker([&] {
        stage.wait(0);                                 // sleeps (no spinning) while stage == 0
        std::cout << "worker saw stage " << stage.load() << '\n';
    });
    stage.store(1);
    stage.notify_one();                                // wake the waiter
    worker.join();
}
// expect: worker saw stage 1
```

### Reference Count for a Shared Object
```cpp
#include <atomic>

struct Shared {
    std::atomic<int> refs{1};
    // ... payload ...
};

void retain(Shared* s)  { s->refs.fetch_add(1, std::memory_order_relaxed); }
void release(Shared* s) {
    if (s->refs.fetch_sub(1, std::memory_order_acq_rel) == 1)   // we were the last owner
        delete s;                                    // acq_rel: see every other owner's writes
}
// This is what std::shared_ptr does internally. Use shared_ptr rather than hand-rolling it.
```

## Key Concepts

### Atomic Means "No Data Race", Not "Thread-Safe Design"
Each single operation is indivisible. A *sequence* of operations is not: `if (a.load() > 0) a--;` can still go negative when two threads interleave. Combine the test and the update in one operation (`compare_exchange`, `fetch_sub`), or use a mutex. See [[Data Races and Race Conditions]].

### Default Construction Changed in C++20
Before C++20, `std::atomic<int> a;` leaves the value **indeterminate**, exactly like `int a;`. Reading it before a store is undefined behavior. Since C++20 the default constructor value-initializes it to 0. In C++14/17 code, always write `std::atomic<int> a{0};`.

### The Default Order Is `seq_cst`
Every operation without an explicit order uses `memory_order_seq_cst`: the strongest and simplest to reason about. Weaker orders are a performance tool. Use `relaxed` for pure counters, `release`/`acquire` pairs for publishing data, and write the reasoning in a comment. See [[Memory Orderings]].

### `compare_exchange` Rewrites `expected`
On failure, the current value is written back into `expected`. That is what makes the retry loop work. It also means a stale local variable is silently updated. `weak` may fail even when the values are equal (spuriously), so only use it inside a loop. Use `strong` for a single attempt.

### Assignment Returns a Value, Not a Reference
`a = 5` returns `5` (a `T`), unlike ordinary assignment, which returns `a&`. That prevents a hidden second, non-atomic read. `++a` likewise returns the new *value*.

### Atomics Are Not Copyable
Copying would need two atomic operations (read one, write the other) that aren't atomic together, so the copy constructor and copy assignment are deleted. Copy the value instead: `std::atomic<int> b{a.load()};`.

### Lock-Free Is Not Guaranteed
Only `std::atomic_flag` is required to be lock-free. For other types, especially large structs, the implementation may use a hidden lock. Check with `is_lock_free()` or, since C++17, `is_always_lock_free`. With GCC, large atomics can require linking `-latomic`.

### `volatile` Is Not `atomic`
`volatile` stops the compiler from removing or merging accesses (it is meant for memory-mapped hardware). It provides no atomicity and no inter-thread ordering. Concurrent `volatile` access is still a data race. See [[volatile — What It Does Not Mean]].

### False Sharing
Two atomics on the same cache line, written by different threads, force that line to ping-pong between cores. Correct, but slow. Pad or align hot atomics to 64 bytes (`alignas(64)`, or `std::hardware_destructive_interference_size`, C++17). See [[False Sharing]].

## Best Practices

1. **Always initialize** atomics in C++11/14/17: `std::atomic<T> x{value};`
2. **Use a mutex** when more than one value must change together. Atomics protect one variable
3. **Leave the default `seq_cst`** unless profiling shows the cost, and comment every weaker order
4. **Pair `release` stores with `acquire` loads** when an atomic flag publishes ordinary data
5. **Use `relaxed` only for counters and statistics** whose value is read after a `join()` or a stronger sync
6. **Loop around `compare_exchange_weak`**; use `strong` for single attempts
7. **Never busy-wait in production**: C++20 `wait`/`notify`, or a `condition_variable`, sleeps instead
8. **`static_assert(is_always_lock_free)`** when code relies on lock-freedom (signal handlers, lock-free structures)
9. **Prefer library types** (`shared_ptr`, `call_once`, `latch`, `counting_semaphore`) over hand-rolled atomic protocols
10. **Run ThreadSanitizer** (`-fsanitize=thread`) on every test that touches shared state

## Related Headers

```cpp
// cc: std=c++23
#include <atomic>              // std::atomic, atomic_flag, memory_order, fences
#include <mutex>               // std::mutex, lock_guard, call_once: multi-value consistency
#include <condition_variable>  // waiting for a condition (pre-C++20 alternative to wait/notify)
#include <thread>              // std::thread, this_thread::yield
#include <memory>              // atomic<shared_ptr<T>> (C++20); free atomic_load for shared_ptr (C++11)
#include <new>                 // hardware_destructive_interference_size (C++17)
#include <latch>               // C++20: one-shot countdown
#include <barrier>             // C++20: reusable phase synchronization
#include <semaphore>           // C++20: counting_semaphore, binary_semaphore
#include <stdatomic.h>         // C++23: C-compatible _Atomic interop
```

## Connections

- **Hub:** [[Map — Standard Headers]]
- **Concept notes (the why behind this card):** [[Atomics]] · [[The C++ Memory Model — happens-before]] · [[Memory Orderings]] · [[Data Races and Race Conditions]] · [[Lock-Free Programming Basics]] · [[False Sharing]]
- **Sibling cards:** [[Header — thread and stop_token]] · [[Header — mutex and shared_mutex]] · [[Header — condition_variable]] · [[Header — chrono]]
- **Practice:** [[Kit — Background Worker (C++14-17)]] (atomic stop state and counters in use) · *Continuum #29 Producer-Consumer*

## Sources

- Tour §18.3 "Sharing Data" (p. 241): atomics as the lightweight alternative to locks.
- Pikus ch. 5 "Threads, Memory, and Concurrency", § Memory model (p. 193): what the orders guarantee on real hardware.
- Pikus ch. 6 "Concurrency and Performance", § Counters and accumulators (p. 224): cost of atomic increments and contention.
- cppreference / web, *`<atomic>`*: https://en.cppreference.com/w/cpp/header/atomic
- cppreference / web, *`std::atomic`* · *`std::memory_order`*: https://en.cppreference.com/w/cpp/atomic/atomic · https://en.cppreference.com/w/cpp/atomic/memory_order
- C++ Core Guidelines CP.100 "Don't use lock-free programming unless you absolutely have to", CP.200 "Use `volatile` only to talk to non-C++ memory": https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
