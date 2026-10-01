---
id: threads
title: Threads — thread and jthread
aliases:
- "std::thread"
- "std::jthread"
- thread of execution
type: concept
domain: D12
tier: 2
status: draft
standard: C++11
prereqs:
- "[[Concurrency vs Parallelism]]"
related:
- "[[Data Races and Race Conditions]]"
- "[[Mutexes and Lock Guards]]"
- "[[Cooperative Cancellation with stop_token]]"
- "[[The C++ Memory Model — happens-before]]"
- "[[Futures, Promises and async]]"
- "[[Dangling Pointers and References]]"
practice:
- 29
tags:
- type/concept
- domain/d12
- tier/2
- tension/abstraction-vs-control
- tension/safety-vs-performance
- std/c++11
- std/c++20
created: 2026-10-01
updated: 2026-10-01
---

# Threads — thread and jthread

> [!essence]
> A **thread** is an independent sequence of instructions that shares its creator's entire address space. `std::thread` (C++11) and `std::jthread` (C++20) are move-only **handles** to that sequence — constructing one launches the function immediately, and what you do with the handle before it is destroyed (`join`, `detach`, or nothing) decides whether your program waits, abandons, or crashes.

## The Problem

[[Concurrency vs Parallelism]] fixed the vocabulary: a program can be *structured* as independent tasks whether or not hardware ever runs them at the same instant. C++ still needs a concrete way to create one of those independent tasks and a name for the thing it creates. That is a narrower, more mechanical question than *concurrency vs. parallelism*, and it is where this note starts.

> [!principle] From "more cores" to a handle object
> 1. **Constraint.** A single core runs one instruction stream at a time. Pikus makes the consequence blunt: running on more than one processor at once has exactly one mechanism behind it, and that mechanism is additional threads or processes (Pikus ch. 5, "What is a thread?", p. 160).
> 2. **Consequence.** Processes are too heavyweight and too isolated for this: they don't share memory by default, so passing data between them means copying it across a process boundary. A sequential program's single call stack also has nowhere to put a second, independent stream of execution — the whole point is that it executes one call at a time.
> 3. **Requirement.** The language needs a unit that (a) is cheap enough to share memory with its creator directly, so communicating needs no serialization, and (b) is still something a program can name, wait for, and reason about the end of.
> 4. **Design.** C++11 added `std::thread` (`<thread>`): constructing one starts a callable running *now*, in a new thread of execution that shares the full address space of the thread that created it. Stroustrup's framing is precise: a *task* is the computation you want run concurrently, and a thread is simply how the system represents that task once it's running (Tour §18.2, p. 238). The object itself is only a **handle** — a small, move-only value naming that execution — so the thread of execution and the C++ object that refers to it are two different things with two different lifetimes.
> 5. **Price.** Splitting "the execution" from "the handle" means the handle can outlive your interest in waiting for it, or go out of scope while the execution is still running. C++ cannot silently decide what you meant in that case — join could hang forever, detach could corrupt memory the execution is still using — so by default it refuses to decide at all: destroying a handle that is still joinable calls `std::terminate`. `std::jthread` (C++20) is the design's second iteration: it picks a safe default (ask the execution to stop, then wait) instead of refusing to choose.

> [!tension] abstraction ⟷ control
> `std::thread` sits as close to the operating system as the Standard Library gets: you decide exactly how many threads exist, you name each one, and you decide when to wait for it. Higher layers — `std::async`, parallel algorithms, a thread pool — make that decision for you. Reaching for `std::thread` directly is a deliberate trade of convenience for control, which is why [[Map — Concurrency|this domain's own advice]] is to reach for it only when no higher layer fits.

## Mental Model

> [!model] Two cooks sharing one kitchen
> Each thread gets its **own cutting board** — a private stack for its own local variables, parameters and return addresses, the kind of storage [[Storage Duration|automatic storage duration]] already described for a single thread. But both cooks work in the **same kitchen** — the one heap, the one set of global and static objects, the one address space — and can reach the same pantry shelf (a shared object) at the same time.
> **Where it breaks:** two human cooks finish a motion — chopping one onion — before the other one reaches for the same knife. Threads are not that polite. The scheduler can interrupt one thread between *any* two machine instructions, so "finish what you're doing first" is not a guarantee the hardware gives you; it is something you have to build with [[Mutexes and Lock Guards|a lock]] or an atomic. That gap between the analogy's implied courtesy and the hardware's actual indifference is exactly what makes unsynchronized sharing a [[Data Races and Race Conditions|data race]] rather than just bad luck.

```text
                         ONE ADDRESS SPACE (one process)
 ┌─────────────────────────────────────────────────────────────────┐
 │  shared: heap objects · global/static objects · code (.text)    │
 │  ┌───────────────────────┐        ┌───────────────────────┐     │
 │  │ thread A's stack      │        │ thread B's stack      │     │
 │  │  locals, params,      │        │  locals, params,      │     │
 │  │  return addresses     │        │  return addresses     │     │
 │  │  (private)            │        │  (private)            │     │
 │  └───────────────────────┘        └───────────────────────┘     │
 └─────────────────────────────────────────────────────────────────┘
```

## Mechanics

The Standard's term is **thread of execution**; `std::thread`/`std::jthread` are handle *objects* that may or may not currently represent one. Telling the two apart resolves most of this section's rules.

| Situation | Rule | Example |
|---|---|---|
| Constructing `std::thread(f, args...)` | The thread of execution starts **immediately**, running `f` with decay-copies of `args...` | `std::thread t(work, 3);` — `work` runs now, concurrently with the rest of `main` |
| An argument the callee declares as `T&` | Must be wrapped in `std::ref`/`std::cref`, or the program is **ill-formed** — the constructor decay-copies every argument first | See *Pitfalls* below |
| Default-constructed, moved-from, joined, or detached `std::thread` | `joinable() == false`: it names no thread of execution | `std::thread t; t.joinable(); // false` |
| `t.join()` | Blocks the caller until `t`'s function returns; afterwards, `t.joinable() == false` | Required before reading anything the thread wrote |
| `t.detach()` | The thread of execution continues on its own; `t` immediately stops representing it | Rarely correct — see *Pitfalls* |
| `std::thread` destroyed while `joinable() == true` | Calls `std::terminate` — not UB, but not recoverable either | `[thread.thread.destr]` ¶1 |
| `std::jthread` destroyed while `joinable() == true` | Calls `request_stop()`, then `join()` — never `std::terminate` | C++20 |

> [!standard] A joinable thread's destructor doesn't guess
> `[thread.thread.destr]` ¶1: *"If `joinable()`, invokes `terminate()`. Otherwise, has no effects."* The Standard's own note explains why neither silent alternative was chosen: an implicit `join` "can hang," and an implicit `detach` "leaves a thread using destroyed locals" — both are worse than failing loudly. `std::jthread` only avoids this because it has something extra to try first: a stop request the running function is expected to notice.

> [!standard] "Eventually makes progress" is a guarantee, not a scheduling promise
> `[intro.progress]` ¶7 (vocabulary formalized for C++17, alongside the parallel algorithms, via WG21 P0299): general-purpose implementations *should* give the thread running `main` and every `std::thread`/`std::jthread` a **concurrent forward progress guarantee** — it will eventually execute another instruction, no matter what any other thread is doing. That rules out starvation; it says nothing about *when*, and nothing about two threads ever running at the literal same instant (that is parallelism, a hardware fact, not a language guarantee — see [[Concurrency vs Parallelism]]).

## Under the Hood

> [!machine] A thread of execution is an OS object, not a language one
> C++ does not define how a thread is implemented; it only defines the handle's interface. On a POSIX system, `std::thread`'s constructor calls into the library's `pthread_create`; on Windows, `CreateThread`. Either way, the kernel allocates a **new stack** (the size is set by the OS or the runtime, not the Standard — commonly a few megabytes by default on desktop platforms, overridable with platform-specific APIs `std::thread` does not expose) and registers a new schedulable entity. That is a system call, not a function call: creating a thread costs on the order of microseconds, where an ordinary call costs nanoseconds. This is the whole reason [[Thread Pools and Task Queues|a thread pool]] exists — to pay that cost once and reuse the threads for many small pieces of work, rather than once per piece of work.

```text
 BEFORE: one thread of execution        AFTER: std::thread t(work);
 ┌───────────────────────┐              ┌───────────────────────┐
 │ main thread            │              │ main thread            │
 │  PC ──▶ ...            │              │  PC ──▶ ...            │
 │  own stack             │              │  own stack             │
 └───────────────────────┘              │  handle `t` (small:    │
                                          │   an id + OS handle)   │
    kernel: 1 schedulable entity         └───────────────────────┘
                                          ┌───────────────────────┐
                                          │ new thread of execution│
                                          │  PC ──▶ work(...)      │
                                          │  new stack (OS-sized)  │
                                          └───────────────────────┘
                                             kernel: 2 schedulable entities
```

`t` itself — the handle in `main`'s stack — is small: an id and an OS-level handle, not a copy of the new thread's stack or registers. Moving a `std::thread` moves that small handle, which is why construction is cheap compared to the thread of execution it names.

## In Code

**1 · The handle's state is separate from whether a thread is running**

```cpp
#include <chrono>
#include <iostream>
#include <thread>

int main() {
    std::thread t;                                           // ①
    std::cout << std::boolalpha << t.joinable() << ' ';
    std::thread worker([] {
        std::this_thread::sleep_for(std::chrono::milliseconds(5));
    });
    std::cout << worker.joinable() << ' ';                   // ②
    t = std::move(worker);                                    // ③
    std::cout << worker.joinable() << ' ' << t.joinable() << ' ';
    t.join();                                                  // ④
    std::cout << t.joinable() << '\n';
}
// expect: false true false true false
```
1. Default-constructed: no thread of execution is attached, so `joinable()` is `false`.
2. `worker` names a real, running thread of execution: `joinable()` is `true` the instant the constructor returns, regardless of whether the function has finished.
3. Moving the handle transfers which object names the thread of execution; it does not touch the thread itself. `worker` now names nothing.
4. After `join()`, `t` no longer represents a thread either — the execution ended and the handle has nothing left to wait for.

**2 · ✗ Passing a reference parameter without `std::ref` doesn't compile**

```cpp
// cc: ill-formed
#include <thread>

void bump(int& n) { n += 100; }

int main() {
    int shared = 1;
    std::thread t(bump, shared);   // error: must be invocable after decay-copy
    t.join();
}
```
`std::thread`'s constructor decay-copies every argument into its own storage before calling the function — even when the function asks for a reference. GCC's static assertion names this directly: *"std::thread arguments must be invocable after conversion to rvalues."* A plain `int` copy cannot bind to `int&`, so the program is rejected at compile time, not silently miscompiled.

**3 · ✓ `std::ref` is what actually shares the object**

```cpp
#include <functional>
#include <iostream>
#include <thread>

void bump(int& n) { n += 100; }

int main() {
    int shared = 1;
    std::thread t(bump, std::ref(shared));   // ① wraps shared in reference_wrapper<int>
    t.join();
    std::cout << shared << '\n';             // ② the real object was modified
}
// expect: 101
```
1. `std::ref` itself decay-copies into a `std::reference_wrapper<int>`, which *does* convert to `int&` — satisfying the constructor's requirement while still naming the original object.
2. Because `bump` genuinely received a reference to `shared`, not a copy, the caller sees the update after `join()`.

**4 · `jthread` stops and joins itself**

```cpp
// cc: std=c++20
#include <chrono>
#include <iostream>
#include <thread>

int main() {
    int ticks = 0;
    {
        std::jthread counter([&ticks](std::stop_token st) {   // ①
            while (!st.stop_requested()) {
                ++ticks;
                std::this_thread::sleep_for(std::chrono::milliseconds(5));
            }
        });
        std::this_thread::sleep_for(std::chrono::milliseconds(25));
    }   // ②
    std::cout << std::boolalpha << (ticks > 0) << '\n';
}
// expect: true
```
1. Because the callable's first parameter is a `std::stop_token`, `jthread` passes one in automatically, drawn from a `stop_source` it owns internally. See [[Cooperative Cancellation with stop_token]].
2. At the closing brace, `~jthread()` requests a stop and joins — `counter` always exits cleanly here, unlike example 2 of the *Pitfalls* section below.

## Pitfalls

> [!trap] Destroying a joinable `std::thread` ends the program
> Any path out of a scope — an early `return`, a thrown exception, a missing `else` — that reaches a `std::thread`'s destructor while it is still `joinable()` calls `std::terminate()` (`[thread.thread.destr]` ¶1). This compiles and passes review right up until the first time that code path is actually exercised.

```cpp
// cc: norun
#include <thread>
void work() {}
int main() {
    std::thread t(work);
    // no join(), no detach(): t is still joinable() here
}   // ~thread(): joinable() is true -> std::terminate()
```
`std::jthread` removes this failure mode entirely (Example 4 above); in C++11/14/17, wrap `std::thread` in a small RAII type whose destructor calls `join()` if `joinable()`.

> [!ub] A detached thread can outlive what it captures by reference
> `detach()` severs the handle from the thread of execution, but the thread keeps running with whatever it captured. A lambda that captures a local *by reference* and is detached will go on reading and writing that local's storage after the enclosing function returns and the storage is reused — a dangling reference, exactly as in [[Dangling Pointers and References]], just reached through a second thread instead of a second pointer.

```cpp
// cc: ub norun
#include <chrono>
#include <thread>
void start_logger() {
    int counter = 0;                         // automatic storage duration
    std::thread t([&counter] {
        while (true) {
            ++counter;                       // reads/writes a local about to die
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
    });
    t.detach();                               // nobody will ever join this thread
}   // counter's storage is reused the instant start_logger() returns
```
`detach()` is almost never the right call unless everything the thread touches is static or otherwise immortal for the life of the program.

> [!trap] Reading a thread's results before `join()` is a data race, not a timing bug
> `join()` is a synchronizing operation: everything the thread wrote *happens-before* `join()` returns (see [[The C++ Memory Model — happens-before]]). Reading the same data from the owning thread *before* calling `join()`, with no other synchronization, is undefined behavior even if it "usually" produces the right answer — see [[Data Races and Race Conditions]].

## Evolution

| Standard | Change | Why |
|---|---|---|
| **C++11** | `std::thread`, `<thread>`; arguments decay-copied; `std::terminate` on destroying a joinable thread | A move-only handle to an OS thread of execution, sharing one address space (Tour §18.2, p. 238) |
| C++17 | Three-tier **forward-progress** vocabulary (`[intro.progress]`) formalized and applied to `std::thread`, alongside the new parallel algorithms (WG21 P0299) | Give "the thread will eventually run" a precise, checkable meaning, not just an intuition |
| **C++20** | `std::jthread`; `<stop_token>` (`stop_token`, `stop_source`, `stop_callback`) | Replace "terminate if you forget" with a safe default, and give threads a standard way to ask one another to stop |
| C++23 | `std::formatter` specialization for `thread::id` | Minor: lets `thread::id` be formatted with `std::format` like any other printable type |

## Connections

- **Prerequisites:** [[Concurrency vs Parallelism]] — fixes the vocabulary (task, concurrent, parallel) and the forward-progress guarantees this note's Mechanics table cites directly.
- **Enables:** [[Data Races and Race Conditions]] (what happens the moment two threads share memory with no discipline) · [[Mutexes and Lock Guards]] (the basic discipline) · [[Cooperative Cancellation with stop_token]] (the mechanism behind Example 4) · [[The C++ Memory Model — happens-before]] (what `join()` actually guarantees) · [[Futures, Promises and async]] (a higher-level layer built on the same underlying thread of execution).
- **Hazards:** [[Dangling Pointers and References]] (a detached thread's captured reference is the same hazard, reached from a second call stack).
- **Builds on:** [[Storage Duration]] (each thread's locals are automatic storage private to that thread's own stack).
- **Domain:** [[Map — Concurrency]].
- **Practice:** *Continuum #29 Producer-Consumer* — launching and joining the worker threads is the first thing this project requires.

## Check Yourself

> [!quiz]- What is the difference between a "thread of execution" and a `std::thread` object?
> A thread of execution is the OS-level running sequence of instructions; `std::thread` is a small, move-only handle that may or may not currently name one. A default-constructed, moved-from, joined, or detached `std::thread` is `joinable() == false` — it names no thread of execution, even though in the detached case the execution itself may still be running.

> [!quiz]- Why does `std::thread(bump, shared)` fail to compile when `bump` takes `int&`, while `std::thread(bump, std::ref(shared))` works?
> The constructor decay-copies every argument into its own storage before invoking the function, even when the function wants a reference — a plain `int` copy can't bind to `int&`, so it's ill-formed. `std::ref(shared)` decay-copies into a `std::reference_wrapper<int>`, which *does* convert to `int&`, so the copy that gets made still refers to the original object.
> 
> See [[References]] for why a reference must bind to something at the moment it is created, which is exactly the property `std::ref` preserves and a plain copy does not.

> [!quiz]- A function launches a `std::thread`, does some other work, and returns without calling `join()` or `detach()`. What happens, and why wasn't it made to just quietly `join()` for you?
> The thread's destructor runs while it is still `joinable()`, so the program calls `std::terminate()`. The Standard's own rationale (`[thread.thread.destr]`) is that an implicit `join` here could hang forever if the thread never finishes, and an implicit `detach` could leave it reading destroyed locals — both failure modes are worse than stopping loudly. `std::jthread` can do better only because it has a stop request to send first.

> [!quiz]- In Example 4, what two things does `~jthread()` do, and in what order, that make the loop exit cleanly?
> It calls `request_stop()` first, which makes `st.stop_requested()` return `true` so the loop's condition fails on its next check; only then does it `join()`, waiting for that now-exiting loop to actually finish. Calling `join()` alone, with no stop request, would wait forever on a loop with no way to know it should stop.

## Sources

- Tour §18.2 "Tasks and threads" (pp. 238–239): the task/thread distinction this note's Design step relies on; threads sharing a single address space; `jthread`'s destructor joining in reverse construction order.
- Pikus ch. 5 "Threads, Memory, and Concurrency", §"Understanding threads and concurrency" (pp. 160–161): the definition of a thread as an independently executable instruction sequence, and why all threads of one process share the same memory.
- cppreference, *std::thread* · *std::jthread*: https://en.cppreference.com/w/cpp/thread/thread · https://en.cppreference.com/w/cpp/thread/jthread
- Draft standard `[thread.thread.destr]` (destructor calls `terminate()` if joinable) and `[intro.progress]` ¶7 (concurrent forward progress for `main`, `thread`, `jthread`): https://eel.is/c++draft/thread.thread.destr · https://eel.is/c++draft/intro.progress
- WG21 P0299, *Forward progress guarantees for the Parallelism TS v2* (the paper that introduced the concurrent/parallel/weakly-parallel vocabulary, merged for C++17): https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2016/p0299r0.html
- C++ Core Guidelines CP.25 "Prefer `gsl::joining_thread` over `std::thread`", CP.26 "Don't `detach()` a thread": https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
