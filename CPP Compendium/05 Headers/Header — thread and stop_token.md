---
id: hdr-thread
title: Header — thread and stop_token
aliases:
- <thread>
- <stop_token>
- std::thread
- std::jthread
- this_thread
- stop_token
type: header
domain: HDR
tier: 2
status: draft
standard: C++11
prereqs:
- "[[Threads — thread and jthread]]"
related:
- "[[Threads — thread and jthread]]"
- "[[Cooperative Cancellation with stop_token]]"
- "[[Data Races and Race Conditions]]"
- "[[Mutexes and Lock Guards]]"
- "[[RAII]]"
tags:
- type/header
- domain/hdr
- tier/2
- header/thread
- header/stop_token
- tension/abstraction-vs-control
- tension/safety-vs-performance
created: 2026-09-23
updated: 2026-09-23
header: <thread>, <stop_token>
---

# Header — thread and stop_token

> [!essence]
> **`<thread>`** starts functions running concurrently (`std::thread`, and C++20's self-joining `std::jthread`) and lets the current thread sleep, yield or identify itself (`std::this_thread`). **`<stop_token>`** (C++20) adds cooperative cancellation: the owner *asks* a thread to stop, and the thread checks and exits cleanly. The key rule of the pre-C++20 API is that every `std::thread` must be joined or detached before it is destroyed, or the program calls `std::terminate`.

> [!standard] Versions
> C++11 (`<thread>`: `std::thread`, `thread::id`, `this_thread::get_id/yield/sleep_for/sleep_until`, `hardware_concurrency`) / C++20 (`std::jthread`; `<stop_token>`: `stop_token`, `stop_source`, `stop_callback`, `nostopstate`; `thread::id` gets `<=>`) / C++23 (`std::formatter` for `thread::id`) / C++26 (`inplace_stop_token`/`inplace_stop_source`/`inplace_stop_callback`, `never_stop_token`, `stoppable_token` concepts)

## Life of a Thread Object

```text
 std::thread t;           std::thread t(f, args...)
┌──────────────┐  move   ┌─────────────────────────┐   join()   ┌──────────────┐
│ not joinable │ ◀────── │ JOINABLE                │ ─────────▶ │ not joinable │ ──▶ ~thread() ✓
└──────────────┘  from   │ f running, or finished  │  detach()  └──────────────┘
                         │ but not yet joined      │
                         └────────────┬────────────┘
                                      │ destroyed, or move-assigned over, while JOINABLE
                                      ▼
                  std::thread  (C++11) → std::terminate()
                  std::jthread (C++20) → request_stop(), then join()
```

## Quick Reference

```cpp
// cc: fragment
// ═══════════════════════════════════════════════════════════════════════════
// std::thread  (C++11): move-only handle to one thread of execution
// ═══════════════════════════════════════════════════════════════════════════
std::thread t;                          // none         | Empty, not joinable     |
std::thread t(f, a, b);                 // callable+args| Start f(a, b) NOW       | Args are COPIED (decayed); use std::ref for references
std::thread t([&]{ ... });              // lambda       | Start the lambda        | Captured references must outlive the thread
std::thread t2 = std::move(t);          // rvalue       | Transfer ownership      | t becomes not joinable
t = std::move(t2);                      // rvalue       | Move-assign             | std::terminate if t was still joinable!
t.joinable()                            // none         | Owns a live thread?     | true until join/detach/move-from
t.join()                                // none         | Wait for f to finish    | Throws system_error if not joinable
t.detach()                              // none         | Let it run unowned      | Rarely correct: nobody can wait for it
t.get_id()                              // none         | thread::id              | Default id if not joinable
t.native_handle()                       // none         | pthread_t / HANDLE      | Platform APIs (priority, affinity)
std::thread::hardware_concurrency()     // static       | Hardware threads        | A hint; may return 0
t.swap(t2)  /  std::swap(t, t2)         // thread&      | Exchange handles        |
~thread()                               //              | Destroy                 | std::terminate if joinable

// ═══════════════════════════════════════════════════════════════════════════
// std::jthread  (C++20): same interface, plus automatic stop + join
// ═══════════════════════════════════════════════════════════════════════════
std::jthread j(f, a);                   // callable     | Start f(a)              | If f takes std::stop_token FIRST, it is passed in
std::jthread j([](std::stop_token st){ while (!st.stop_requested()) { ... } });
j.request_stop()                        // none         | Ask the thread to stop  | Returns true if this call made the request
j.get_stop_token()                      // none         | Token for this thread   |
j.get_stop_source()                     // none         | Source (can request too)|
~jthread()                              //              | request_stop() + join() | Never std::terminate
j.join() / detach() / joinable() / get_id() / native_handle() / hardware_concurrency()   // as std::thread

// ═══════════════════════════════════════════════════════════════════════════
// std::this_thread  (C++11): the calling thread
// ═══════════════════════════════════════════════════════════════════════════
std::this_thread::get_id()              // none         | Current thread's id     |
std::this_thread::sleep_for(100ms)      // duration     | Sleep at least that long| <chrono> durations
std::this_thread::sleep_until(tp)       // time_point   | Sleep until a moment    | Drift-free periodic loops
std::this_thread::yield()               // none         | Hint: let others run    | Mostly for spin-waits

// ═══════════════════════════════════════════════════════════════════════════
// std::thread::id  (C++11)
// ═══════════════════════════════════════════════════════════════════════════
id1 == id2,  id1 < id2                  // Comparable (<=> since C++20): usable as a map key
std::hash<std::thread::id>              // Usable in unordered containers
std::cout << id                         // Printable (implementation-specific text)
std::format("{}", id)                   // C++23 formatter

// ═══════════════════════════════════════════════════════════════════════════
// <stop_token>  (C++20): cooperative cancellation
// ═══════════════════════════════════════════════════════════════════════════
std::stop_source src;                   // none         | New stop state          |
std::stop_source src{std::nostopstate}; // tag          | No stop state           | stop_possible() == false
src.get_token()                         // none         | → std::stop_token       | Cheap to copy
src.request_stop()                      // none         | Request a stop          | Runs registered callbacks; true if first
src.stop_requested() / stop_possible()  // none         | Query                   |
std::stop_token tok;                    // none         | Default: can never stop |
tok.stop_requested()                    // none         | Stop asked for?         | Poll this in the worker loop
tok.stop_possible()                     // none         | Could a stop ever come? |
std::stop_callback cb(tok, fn);         // token+fn     | Run fn on request_stop  | Runs immediately if already stopped
std::condition_variable_any::wait(lock, tok, pred)   // Wait that also wakes on a stop request  (<condition_variable>)
```

## Patterns

### Start a Thread and Wait for It (C++11)
```cpp
#include <functional>
#include <iostream>
#include <thread>

void count_to(int n, int& result) {
    for (int i = 1; i <= n; ++i) result += i;
}

int main() {
    int total = 0;
    std::thread worker(count_to, 100, std::ref(total));   // std::ref: pass by reference
    // ... main thread does other work here ...
    worker.join();                                        // wait; afterwards `total` is safe to read
    std::cout << total << '\n';
}
// expect: 5050
```

### Main Keeps Working While a Background Loop Runs (C++11/14/17)
```cpp
#include <atomic>
#include <chrono>
#include <iostream>
#include <thread>

int main() {
    std::atomic<bool> stop{false};
    std::atomic<int> heartbeats{0};
    std::thread background([&] {
        while (!stop) {
            ++heartbeats;
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    });

    for (int task = 0; task < 3; ++task)                  // the main thread's own work
        std::this_thread::sleep_for(std::chrono::milliseconds(20));

    stop = true;                                          // ask the loop to finish
    background.join();                                    // then wait for it: REQUIRED
    std::cout << (heartbeats > 0 ? "background ran alongside main" : "?") << '\n';
}
// expect: background ran alongside main
```

### A Joining Wrapper so an Exception Can't Leak a Thread (C++11/14/17)
```cpp
#include <chrono>
#include <iostream>
#include <stdexcept>
#include <thread>
#include <utility>

class JoiningThread {                                     // RAII: join in the destructor
    std::thread t_;
public:
    template <class... Args>
    explicit JoiningThread(Args&&... args) : t_(std::forward<Args>(args)...) {}
    JoiningThread(JoiningThread&&) = default;
    ~JoiningThread() { if (t_.joinable()) t_.join(); }
};

int main() {
    try {
        JoiningThread worker([] { std::this_thread::sleep_for(std::chrono::milliseconds(5)); });
        throw std::runtime_error("early exit");           // with a bare std::thread: std::terminate
    } catch (const std::exception& e) {
        std::cout << "handled: " << e.what() << '\n';     // the worker was joined during unwinding
    }
}
// expect: handled: early exit
// Full version with stop support: [[Kit — Background Worker (C++14-17)]]. In C++20, use std::jthread.
```

### std::jthread with a stop_token (C++20)
```cpp
// cc: std=c++20
#include <chrono>
#include <iostream>
#include <thread>

int main() {
    int polls = 0;
    {
        std::jthread poller([&polls](std::stop_token st) {   // token passed automatically
            while (!st.stop_requested()) {
                ++polls;
                std::this_thread::sleep_for(std::chrono::milliseconds(5));
            }
        });
        std::this_thread::sleep_for(std::chrono::milliseconds(30));
    }   // ~jthread: request_stop(), then join()
    std::cout << (polls > 0 ? "poller stopped cleanly" : "?") << '\n';
}
// expect: poller stopped cleanly
```

### Waking a Sleeping Worker Immediately on Stop (C++20)
```cpp
// cc: std=c++20
#include <condition_variable>
#include <iostream>
#include <mutex>
#include <thread>

int main() {
    std::mutex m;
    std::condition_variable_any cv;
    bool work_ready = false;
    std::jthread worker([&](std::stop_token st) {
        std::unique_lock lock(m);
        cv.wait(lock, st, [&] { return work_ready; });   // returns on work OR on a stop request
        std::cout << (st.stop_requested() ? "stopped while idle" : "got work") << '\n';
    });
    worker.request_stop();                                // no notify needed: the wait watches st
}
// expect: stopped while idle
```

### Run a Callback When a Stop Is Requested (C++20)
```cpp
// cc: std=c++20
#include <iostream>
#include <stop_token>

int main() {
    std::stop_source source;
    std::stop_callback on_stop(source.get_token(), [] {
        std::cout << "closing socket\n";                  // e.g. unblock a blocking read
    });
    source.request_stop();                                // runs the callback on this thread
}
// expect: closing socket
```

### One Worker per Hardware Thread
```cpp
#include <algorithm>
#include <iostream>
#include <thread>
#include <vector>

int main() {
    const unsigned n = std::max(1u, std::thread::hardware_concurrency());   // 0 means "unknown"
    std::vector<long> partial(n, 0);
    std::vector<std::thread> pool;
    for (unsigned w = 0; w < n; ++w)
        pool.emplace_back([&partial, w, n] {
            for (long i = w; i < 1000; i += n) partial[w] += i;  // each thread owns one slot: no race
        });
    for (auto& t : pool) t.join();
    long sum = 0;
    for (long p : partial) sum += p;
    std::cout << sum << '\n';
}
// expect: 499500
```

### Getting an Exception Out of a Thread
```cpp
#include <exception>
#include <iostream>
#include <stdexcept>
#include <thread>

int main() {
    std::exception_ptr error;                             // escaping the thread = std::terminate
    std::thread worker([&error] {
        try {
            throw std::runtime_error("disk full");
        } catch (...) {
            error = std::current_exception();             // park it for the owner
        }
    });
    worker.join();                                        // join first: then reading `error` is safe
    try {
        if (error) std::rethrow_exception(error);
    } catch (const std::exception& e) {
        std::cout << "worker failed: " << e.what() << '\n';
    }
}
// expect: worker failed: disk full
// std::async / std::future (<future>) do this transport for you.
```

### Naming Threads in Logs by id
```cpp
#include <iostream>
#include <map>
#include <mutex>
#include <string>
#include <thread>

std::mutex log_mutex;
std::map<std::thread::id, std::string> names;             // thread::id is a valid map key

void name_this_thread(const std::string& name) {
    std::lock_guard<std::mutex> lock(log_mutex);
    names[std::this_thread::get_id()] = name;
}

void log(const std::string& msg) {
    std::lock_guard<std::mutex> lock(log_mutex);          // cout is not synchronized between threads
    std::cout << '[' << names[std::this_thread::get_id()] << "] " << msg << '\n';
}

int main() {
    name_this_thread("main");
    std::thread t([] { name_this_thread("worker"); log("hello from worker"); });
    t.join();
    log("done");
}
// expect: [worker] hello from worker
// expect: [main] done
```

## Key Concepts

### Joinable at Destruction → `std::terminate`
A `std::thread` that still represents a thread when it is destroyed (or move-assigned over) calls `std::terminate`. The committee chose this because both silent alternatives are dangerous: an implicit `join` can hang, and an implicit `detach` leaves a thread using destroyed locals. `std::jthread` (C++20) resolves it by requesting a stop, then joining. See [[Threads — thread and jthread]].

### Arguments Are Copied, Even References
`std::thread t(f, x)` copies `x` into the new thread's storage (decay-copy) *even if `f` takes `T&`*. Code that expects a reference either fails to compile or modifies a copy. Wrap the argument in `std::ref(x)` / `std::cref(x)`, and make sure `x` outlives the thread.

### Exceptions Don't Cross Threads by Themselves
An exception escaping the thread's function calls `std::terminate`. Catch it inside, store it in a `std::exception_ptr`, and rethrow it on the owning thread after `join()`, or use `std::async` / `std::promise` (`<future>`), which do this for you.

### `detach()` Is Almost Never the Answer
A detached thread can outlive `main`'s locals and even static objects, and nothing can wait for it or collect its errors. If a task must outlive its creator, give it an owner with a longer lifetime (a thread pool, a service object) instead.

### Cancellation Is Cooperative
Neither `std::thread` nor `std::jthread` can kill a thread. A stop request only sets a flag the thread must check (`stop_requested()`), or wakes waits that watch the token (`condition_variable_any::wait` with a `stop_token`, and `stop_callback`). Long blocking calls need their own way to be interrupted. See [[Cooperative Cancellation with stop_token]].

### `join()` Is a Synchronization Point
Everything the thread wrote *happens-before* `join()` returns, so after `join()` the owner may read the thread's results without atomics or locks. Reading them *before* `join()` without synchronization is a data race. See [[The C++ Memory Model — happens-before]].

### `hardware_concurrency()` Is a Hint
It reports how many threads the hardware can run at once, and may return 0 when that is unknown. It says nothing about how many cores are free, so treat it as an upper bound for CPU-bound work.

### `sleep_for` Is a Minimum
The thread sleeps *at least* the requested time; the scheduler decides when it runs again. For periodic work, use `sleep_until` with a precomputed time point. See [[Header — chrono]].

## Best Practices

1. **Use `std::jthread`** in C++20; in C++11/14/17 wrap `std::thread` in a joining RAII type
2. **Join before reading results**, and treat `join()` as the moment data becomes safe to use
3. **Never `detach()`** unless the thread touches only static, immortal state
4. **Pass `std::ref`** when a thread function must modify the caller's object, and guarantee that object's lifetime
5. **Catch everything inside the thread function**; transport errors with `exception_ptr` or `std::future`
6. **Make stop requests cooperative**: a checked flag or `stop_token`, plus interruptible waits
7. **Prefer tasks (`std::async`, a thread pool) over raw threads** when you just need a result computed elsewhere
8. **Give each thread its own data** where possible (per-thread slots, then combine); share as little as possible
9. **Synchronize `std::cout`** (a mutex, or C++20 `std::osyncstream`) to avoid interleaved output
10. **Test with ThreadSanitizer** (`-fsanitize=thread`) on every multithreaded code path

## Related Headers

```cpp
#include <thread>              // std::thread, std::jthread (C++20), std::this_thread
#include <stop_token>          // C++20: stop_token, stop_source, stop_callback
#include <mutex>               // mutex, lock_guard, unique_lock, scoped_lock (C++17), call_once
#include <condition_variable>  // condition_variable, condition_variable_any (stop_token waits, C++20)
#include <atomic>              // atomic flags and counters shared between threads
#include <future>              // async, future, promise, packaged_task: results + exceptions
#include <chrono>              // durations for sleep_for, time points for sleep_until
#include <syncstream>          // C++20: osyncstream for non-interleaved output
#include <latch>               // C++20: wait for N events
#include <semaphore>           // C++20: counting_semaphore
```

## Connections

- **Hub:** [[Map — Standard Headers]]
- **Concept notes (the why behind this card):** [[Threads — thread and jthread]] · [[Cooperative Cancellation with stop_token]] · [[Data Races and Race Conditions]] · [[Mutexes and Lock Guards]] · [[Condition Variables]] · [[Futures, Promises and async]] · [[RAII]]
- **Sibling cards:** [[Header — atomic]] · [[Header — chrono]] · [[Header — mutex and shared_mutex]] · [[Header — condition_variable]] · [[Header — future]]
- **Practice:** [[Kit — Background Worker (C++14-17)]] (a C++14/17 `jthread`/`stop_token` stand-in) · *Continuum #29 Producer-Consumer* · *#35 Multithreaded Server Platform*

## Sources

- Tour §18.2 "Tasks and threads" (p. 238): launching and joining threads; §18.3 "Sharing Data" (p. 241).
- Pikus ch. 8 "Concurrency in C++" (p. 293): the standard threading facilities and their costs.
- cppreference / web, *`<thread>`* · *`<stop_token>`*: https://en.cppreference.com/w/cpp/header/thread · https://en.cppreference.com/w/cpp/header/stop_token
- cppreference / web, *`std::thread`* · *`std::jthread`*: https://en.cppreference.com/w/cpp/thread/thread · https://en.cppreference.com/w/cpp/thread/jthread
- C++ Core Guidelines CP.25 "Prefer `gsl::joining_thread` over `std::thread`", CP.26 "Don't `detach()` a thread", CP.31 "Pass small amounts of data between threads by value": https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
