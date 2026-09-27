---
id: process-memory-layout
title: Process Memory Layout — Stack, Heap, Static
type: mechanism
domain: D04
tier: 1
status: draft
standard: C++98
prereqs: []
related:
- "[[Storage Duration]]"
- "[[Object Lifetime]]"
- "[[Dangling Pointers and References]]"
- "[[Dynamic Memory — new and delete]]"
practice:
- 11
tags:
- type/mechanism
- domain/d04
- tier/1
- tension/abstraction-vs-control
created: 2026-09-27
updated: 2026-09-27
---

# Process Memory Layout — Stack, Heap, Static

> [!essence]
> An object needs somewhere to live for exactly as long as it's needed — no longer, because that costs time and space, and no less, because then it dangles. C++ answers with four **storage durations**, and every mainstream implementation honors them with the same real-machine convention: a fixed static region, a LIFO stack of call frames, and a general-purpose heap. The Standard names the first; hardware and the ABI supply the second.

## The Problem

Three functions in the same program need memory for very different lengths of time: a global logger that must exist for the whole run, a loop counter that dies the moment its block ends, and a buffer whose size and lifetime aren't known until a file is opened at run time.

> [!principle] Constraint → Consequence → Design
> 1. **Constraint.** A process gets one address space — a flat range of bytes — from the operating system. Nothing about that range distinguishes "this byte belongs to an object that outlives the program" from "this byte belongs to an object that dies at the next `}`."
> 2. **Consequence.** If every object were allocated the same way — say, by asking a general-purpose allocator for a block and remembering to free it — then a loop counter used once and discarded would pay for the same bookkeeping (free lists, locks, metadata) as a long-lived buffer, and every one of the millions of function calls a program makes would need matching, explicit deallocation code.
> 3. **Requirement.** The language needs storage disciplines that match how each object's lifetime is actually decided: near-zero-cost, automatic reclamation for objects whose scope nests in the same order it opened (call this one, then that one, then unwind); a single fixed slot, prepared once, for objects that live as long as the program or a thread; and a general-purpose allocator, addressed explicitly by the programmer, for objects whose lifetime only run-time logic can determine.
> 4. **Design.** The Standard defines exactly four **storage durations** — static, thread, automatic, and dynamic (`[basic.stc.general]`) — as a property of *when the storage is obtained and released*, independent of how long any particular implementation happens to keep it. It says nothing about *where* that storage lives. But GCC, Clang and MSVC alike answer with the same convention: a **stack**, one per thread, holding automatic-duration activation records in last-in-first-out order; a **heap** (the *free store*), a general-purpose allocator serving dynamic-duration requests; and **static storage**, fixed regions sized and largely populated before `main` runs. [[Object Lifetime|Lifetime]] is the abstract machine's promise; *the stack* and *the heap* are the folk names for how every real compiler keeps it.
> 5. **Price.** Because the mapping is convention, not mandate, none of it is something a conforming program may rely on: no address ordering, no growth direction, no guarantee that "automatic" means "on a stack" at all. Relying on it anyway — assuming two locals are adjacent, or that a freed stack slot stays garbage instead of being reused — is exactly how a programmer talks a real machine into optimizing their bug away or reusing memory out from under them ([[Dangling Pointers and References]]).

> [!tension] abstraction ⟷ control
> `[basic.stc.general]` gives you a vocabulary — static, thread, automatic, dynamic — with zero mention of stacks, heaps, or addresses; that is the abstraction. Every one of those four categories is nonetheless implemented as a specific, inspectable real-machine mechanism with its own performance profile, which is why the sections below switch lenses deliberately: "the Standard says" versus "on Linux/x86-64, GCC does."

## Mental Model

> [!model] A concert hall built before the audience arrives
> **Static storage** is the reserved seating chart: printed and fixed before the doors open (before `main`), unaffected by who shows up. **The stack** is the coat-check line: one attendant handles claims in strict last-in-first-out order — the last coat checked in is the first handed back — so no ticket-matching search is ever needed. **The heap** is the general cloakroom down the hall: any coat, any time, any order of return, but you must remember your own ticket number, and the attendant has to search for your coat.
> **Where it breaks:** the coat-check line only ever grows or shrinks from one end (the top); a real call stack does too, but unlike a physical line, its "attendant" is just a single register (the stack pointer) — there is no search, not even a fast one, and reclaiming a frame is one subtraction, not a hand-off.

```text
STATIC (fixed before main)      STACK (LIFO, per thread)      HEAP (free store)
┌───────────────────────┐       ┌──────────────────────┐      ┌──────────────────────┐
│ int global_total;     │       │ main()'s frame        │      │ [ 42 ]  ← int         │
│ static int last;      │       │  ┌─────────────────┐  │      │  owned by a           │
│  (one slot, ever)     │       │  │ recurse(0)      │  │      │  unique_ptr<int>      │
└───────────────────────┘       │  │  frame_marker=0 │  │      └──────────────────────┘
                                 │  │ ┌─────────────┐ │  │       any lifetime, any
                                 │  │ │ recurse(1)  │ │  │       order of release —
                                 │  │ │ frame_marker│ │  │       you name the moment
                                 │  │ │   = 1       │ │  │       with new / delete
                                 │  │ └─────────────┘ │  │
                                 │  └─────────────────┘  │
                                 └──────────────────────┘
```

## Step by Step

```mermaid
sequenceDiagram
    autonumber
    participant OS as Loader (before main)
    participant ST as Static storage
    participant SK as Stack (this thread)
    participant HP as Heap (free store)
    OS->>ST: map text + fix layout; place constant-initialized globals
    OS->>ST: run dynamic initializers (unspecified order across TUs)
    OS->>SK: enter main() — push its activation record
    SK->>SK: call f() — push f's record atop main's
    SK->>HP: new T(...) — request dynamic storage
    HP-->>SK: pointer to a block outside the stack
    SK->>SK: f() returns — pop f's record (LIFO)
    SK->>HP: delete p — destructor runs, block returned to the allocator
    SK->>ST: main() returns — pop main's record
    ST->>ST: run destructors for static-duration objects, reverse order
```

1. **Before `main` (static storage prepared).** The loader maps the program's code and lays out its static-duration objects. Those with a *constant* initializer (a literal, a `constexpr` expression) get their bits written directly into the program image — no code runs. Those needing a computed initializer run in an order the Standard leaves largely unspecified *across* translation units, which is precisely the [[Static Initialization Order Fiasco|static-initialization-order]] hazard.
2. **Each function call (a frame is pushed).** The compiler emits code that reserves space — for parameters, local variables, the return address, and saved registers — and makes that the new top of the stack. `push`, in effect, is "move a single pointer." [PPP calls this an *activation record*, and shows the same growing stack of them one call at a time (§7.4).]
3. **Each `new`-expression (dynamic storage is requested).** Unlike the other three, dynamic storage doesn't ride on scope at all: the program calls an allocation function explicitly, which finds or carves out a suitably sized, suitably aligned block from the heap — a data structure the runtime itself manages, entirely separate from the stack.
4. **Each function return (the frame is popped).** Local objects' destructors run, then the frame is discarded by moving the same pointer back — no search, no bookkeeping, because LIFO order means the *last* thing pushed is always, unconditionally, the *next* thing popped.
5. **Each `delete`-expression (dynamic storage is released).** The pointed-to object's destructor runs, then the block returns to the allocator, which must remember which blocks are free and may have to merge or search — real bookkeeping a stack pop never needs.
6. **Program exit (static storage torn down).** Static-duration objects whose construction completed are destroyed in the reverse of that completion order. Storage that was never freed by a matching `delete` (or a thread's stack that no one unwinds because the process just exits) is simply reclaimed by the OS when the process ends — the bits go away, but no destructor for it ever ran.

## Under the Hood

> [!machine] A typical process image, low to high addresses (Linux/x86-64 convention — nothing here is guaranteed by the Standard)
> ```text
>  low addr                                                      high addr
>  ┌─────────┬───────────────┬───────────────┬───────►    ◄───────┬─────────┐
>  │  text   │ data (init'd) │ bss (zeroed)  │  heap  │    │ stack │ args/env│
>  │ (code,  │ static objs   │ static objs   │ grows  │gap │ grows │  argv,  │
>  │ read-   │ with non-zero │ zero-initial- │  up →  │    │← down │  envp   │
>  │  only)  │ initializers  │ ized/no init  │        │    │       │         │
>  └─────────┴───────────────┴───────────────┴────────┴────┴───────┴─────────┘
> ```
> `text`, `data` and `bss` together *are* static storage; the sizes of all three are fixed at link time. Each thread gets its own stack region, reserved (not necessarily all committed) at thread-creation time — typically a few MiB by default on Linux, which is exactly why unbounded recursion overflows it while the far larger heap usually doesn't. The heap is not one contiguous thing either: small requests are typically served from a region the allocator extends with `brk`/`sbrk`, while large requests often go straight to `mmap` — detail the allocator hides behind `new` and `delete` entirely.

Popping a frame is one instruction changing one register; the compiler doesn't call a function to do it. Asking the heap for memory is a real function call into an allocator that must consult (and update) shared bookkeeping — which is why avoiding needless allocation is one of the cheapest performance wins available, and why frequent small `new`/`delete` calls in a hot loop show up on a profiler when an equivalent stack-allocated `std::array` would not.

## In Code

**1 · Static storage: one slot, prepared once, shared by every call**

```cpp
#include <cstdio>

int global_total = 0;                 // ① static storage duration: fixed before main runs

int next_ticket() {
    static int last = 100;            // ② static storage duration, but block scope
    ++last;
    return last;
}

int main() {
    printf("%d\n", next_ticket());
    printf("%d\n", next_ticket());
    printf("%d\n", next_ticket());
    printf("global @ %p\n", (void*)&global_total);
}
// expect: 101
// expect: 102
// expect: 103
```
1. `global_total` gets its storage — and, since it has a constant initializer, its value — before `main` ever runs.
2. `last` is declared inside a function, but `static` moves its storage duration out of the stack: it is initialized exactly once, the first time control reaches it, and keeps its value across every later call ([[Storage Duration]]).

**2 · Automatic storage is scope-bound; dynamic storage isn't**

```cpp
#include <cstdio>
#include <memory>

std::unique_ptr<int> make_dynamic() {
    auto p = std::make_unique<int>(42);   // ① dynamic storage duration
    return p;                             // ② moved out: the int outlives this call
}

int main() {
    const void* first_addr;
    {
        int a = 1;                        // ③ automatic storage duration
        first_addr = &a;
    }                                      // ④ a's lifetime ends here; its storage is released
    int b = 2;                            // ⑤ a new object, same scope depth
    printf("%s\n", first_addr == (void*)&b ? "reused" : "not reused (no promise either way)");

    auto owned = make_dynamic();
    printf("%d\n", *owned);                // ⑥ still valid: nothing has reused this storage
}
// expect: 42
```
1. `make_unique<int>` obtains dynamic storage: its lifetime is tied to explicit release (here, via the smart pointer), not to any scope.
2. Returning `p` moves ownership out; the `int` is still alive in `main` — dynamic storage was never scope-bound to begin with.
3. `a` is an ordinary local: automatic storage duration.
4. The closing brace ends `a`'s lifetime and releases its storage — deterministically, unlike dynamic storage's programmer-chosen release.
5. `b` is a *different* object that may or may not occupy the same bytes `a` used; the Standard makes no promise either way, which is exactly the point.
6. The heap object, in contrast, is untouched by any of the stack activity around it.

**3 · Recursion makes the stack's LIFO discipline visible**

```cpp
// cc: flags=-O0
#include <cstdio>

void recurse(int depth) {
    int frame_marker = depth;              // ① a fresh automatic object per call
    printf("depth %d: frame @ %p\n", depth, (void*)&frame_marker);
    if (depth < 3) recurse(depth + 1);     // ② push another activation record
}                                          // ③ this one is popped on return

int main() {
    recurse(0);
}
```
1. Every call gets its *own* `frame_marker`; the name is reused, the storage is not.
2. Each recursive call pushes a new frame directly on top of its caller's — the mechanism [[Anatomy of a Function|function calls]] rely on for recursion to work at all.
3. `-O0` keeps every call from being inlined away, so the growing stack of frames stays visible; on this build the printed addresses fall a fixed distance apart and count *down*, matching the box diagram above. Neither the direction nor the distance is something the Standard promises — it's this platform's calling convention, not C++'s.

## Consequences

| Observed rule or failure | Explained by |
|---|---|
| A pointer or reference to a local is garbage (or crashes) right after the function returns | Automatic storage is released — and its bytes are free to be reused by the very next call's frame: [[Dangling Pointers and References]] |
| A `static` local remembers its value between calls, but an ordinary local doesn't | Only the `static` one has *static* storage duration; it isn't part of any stack frame to begin with: [[Storage Duration]] |
| Deep, unbounded recursion crashes with a stack overflow, but the heap "runs out" far more gracefully (or not at all) | Each thread's stack is a small, fixed-size reservation set up once; the heap can keep growing (via the allocator asking the OS for more) until physical limits are hit |
| `new`/`delete` in a hot loop shows up on a profiler; the equivalent stack array doesn't | Popping a frame is a register update; releasing heap storage calls into an allocator that does real bookkeeping |
| Two objects declared one after another sometimes share an address across separate runs of a program, and sometimes don't | Storage reuse for automatic-duration objects is real but unspecified — nothing about it is part of the contract ([[Undefined Behavior|Implementation-Defined, Unspecified and Undefined Behavior]]) |
| A global's constructor can crash before `main` even starts, depending on link order | Dynamic initializers for static-duration objects across translation units run in largely unspecified order: [[Static Initialization Order Fiasco]] |

## Connections

- **Domain:** [[Map — Objects, Memory & Lifetime]] — the real-machine picture the rest of the domain's abstract rules attach to.
- **Enables:** [[Storage Duration]] (the Standard's four-way vocabulary this note gives a machine to run on) · [[Object Lifetime]] (lifetime vs. storage: lifetime ends when a destructor starts running; the underlying *storage* may be released later still, at scope exit, at `delete`, or at program end — `[basic.life]` ¶2 versus `[basic.stc.general]` ¶1).
- **Explains:** [[Dangling Pointers and References]] (stack-slot and heap-block reuse) · [[Dynamic Memory — new and delete]] (the free store this note treats from the outside).
- **Deeper:** [[The Call Stack and Stack Frames]] (per-call layout: return address, saved registers, argument passing) · [[Static Initialization Order Fiasco]] (the unspecified cross-TU ordering named in Step 1).
- **Siblings:** [[Pointers vs References]] (both can point into any of these three regions).
- **Practice:** *Continuum #11 Pointer & Array Internals Lab* — print the addresses of a static, a stack, and a heap object side by side and account for the ordering you see.

## Check Yourself

> [!quiz]- Why does the Standard define *storage duration* instead of just saying "the stack" and "the heap"?
> Because "stack" and "heap" are implementation conventions, not language guarantees. `[basic.stc.general]` needs to bind every conforming compiler to the same rule regardless of whether it happens to use a downward-growing stack, an upward-growing one, or (on an unusual target) something else entirely. Storage duration describes *when* storage is obtained and released; it says nothing about *where*.

> [!quiz]- A function returns a `unique_ptr<int>` built inside it, and the caller dereferences it successfully. Another function returns a raw `int*` to a local `int`, and dereferencing that is undefined behavior. Both objects were created inside a function that returned. What's actually different?
> Storage duration, not "being inside a function." The `unique_ptr`'s `int` has *dynamic* storage duration: nothing ties its release to the function's scope, so it is simply still there. The raw local has *automatic* storage duration: its storage is released when the block ends, before the caller ever gets to use the pointer — the address is real, but nothing behind it is guaranteed to be.

> [!quiz]- Predict: in the recursion example, if you compiled at `-O2` instead of `-O0`, would you expect to see four distinct addresses printed?
> Not reliably. At higher optimization levels the compiler is free — under the as-if rule — to keep `frame_marker` in a register instead of giving it stack storage at all, or to inline shallow recursion outright, in which case there may be far fewer distinct addresses, or the variable may have no address to take without forcing a spill. The activation-record picture is what a *conforming, unoptimized* mental model predicts; what actually happens is up to the optimizer.

> [!quiz]- Two automatic objects, `a` in one block and `b` declared right after that block ends, sometimes end up at the same address and sometimes don't. Is either outcome a bug?
> No — neither is promised, so neither is a violation. What *would* be a bug is code that depends on one outcome or the other: assuming `b` always reuses `a`'s address (or never does) is relying on an implementation convention the Standard never signed up to keep.

## Sources

- Primer §12.1 "Dynamic Memory and Smart Pointers" (p. 450): the three-way split — static memory, stack memory, and the free store (heap) — stated together, with cross-references to where each is introduced.
- Primer §6.1.1 "Function Basics" (pp. 205–206): automatic objects created and destroyed with their block; local `static` objects initialized once and destroyed only at program termination.
- PPP §7.4 "Function call implementation": the function activation record, built and stacked one call at a time, with the direction of stack growth drawn explicitly for a small recursive example.
- PPP §15.4 "Free store and pointers": free-store allocation and deallocation through `new` and `delete`, independent of any enclosing scope.
- Tour §15.3.1 "array" (p. 203): the stack-vs-free-store trade-off in practice — direct, fast access to a bounded, limited resource versus flexible, indirect access to a much larger one, and the cost of getting it wrong (stack overflow; free-store fragmentation and exhaustion).
- Pikus, §"Unnecessary memory allocations" (p. 336): frequent heap allocation as a measured performance cost, and the advice to minimize round-trips to the allocator.
- cppreference, *Storage class specifiers*: https://en.cppreference.com/w/cpp/language/storage_duration — the four storage durations and their exact conditions.
- Draft standard `[basic.stc.general]`: storage duration as "the minimum potential lifetime of the storage containing the object," and its four categories: https://eel.is/c++draft/basic.stc.general
- Draft standard `[basic.life]` ¶2: an object's *lifetime* ends when its destructor starts (class type) or its storage is released or reused — not necessarily the same moment: https://eel.is/c++draft/basic.life
- Real-machine process layout (text/data/bss/heap/stack, Linux x86-64 convention): Gustavo Duarte, "Anatomy of a Program in Memory," https://manybutfinite.com/post/anatomy-of-a-program-in-memory/
- See [[Map — Objects, Memory & Lifetime]] for how this note's picture connects to storage duration, lifetime, and the access-path notes ([[Pointers]], [[References]]) that reach into all three regions.
