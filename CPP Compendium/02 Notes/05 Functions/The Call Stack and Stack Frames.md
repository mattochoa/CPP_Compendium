---
id: call-stack
title: The Call Stack and Stack Frames
type: mechanism
domain: D05
tier: 1
status: draft
standard: C++98
prereqs:
- "[[Process Memory Layout — Stack, Heap, Static]]"
related:
- "[[Anatomy of a Function]]"
- "[[Recursion]]"
- "[[Exceptions]]"
- "[[Stack Unwinding]]"
- "[[Inlining — Compiler Reality vs the Keyword]]"
practice:
- 9
tags:
- type/mechanism
- domain/d05
- tier/1
- tension/abstraction-vs-control
created: 2026-09-28
updated: 2026-09-28
---

# The Call Stack and Stack Frames

> [!essence]
> A function call is real-machine work: the callee needs its own private storage for parameters, locals and the address to resume at, and that storage must nest exactly as deeply as the calls themselves do. Every mainstream implementation answers with a **call stack** — one **stack frame** (activation record) pushed per call, in strict last-in-first-out order, and popped the instant that call returns. Pushing and popping both collapse to moving a single pointer: the cheapest possible way to give every call the isolation it needs.

## The Problem

[[Anatomy of a Function|A function's declaration]] is a compile-time promise: fixed parameter types, a fixed return type. Keeping that promise at run time is a different problem — one call can be nested inside another, directly or through [[Recursion|recursion]], and each nested call needs its own copy of "the arguments" and "the locals" without disturbing the call that is waiting for it to finish.

> [!principle] Constraint → Consequence → Design
> 1. **Constraint.** A function's body can call other functions — including itself — before it returns. The caller is *suspended*, not abandoned: the Standard guarantees that a local object of automatic storage duration "exists and retains its last-stored value... while the block is suspended... by a call of a function" (`[intro.execution]` ¶1). That suspension can nest to any depth the program's logic demands.
> 2. **Consequence.** Every one of those suspended calls needs its own, simultaneously-alive storage for its parameters and locals. Recursion is the sharpest case: many copies of the *same* function's locals, under the *same* names, alive at once, and none may be confused with any other.
> 3. **Requirement.** The language needs a way to hand out and reclaim per-call storage that (a) matches the calls' naturally *nested* lifetime — the most recently entered call is always the first to finish — and (b) is cheap enough to pay on every single call, not only the expensive ones.
> 4. **Design.** Give each call its own **stack frame**: a block of storage holding its parameters, its locals, the address to resume the caller at, and whatever registers the callee must hand back unchanged. Push one frame per call onto a per-thread **call stack**; pop it the moment that call returns. Because calls genuinely nest — the callee of a callee always finishes before the caller does — a stack (last in, first out) is exactly the right shape, and both push and pop collapse to moving one register.
> 5. **Price.** The stack is one contiguous region of fixed, usually modest size, reserved per thread. A frame's size is fixed at compile time — locals don't grow at run time — so the only way to run out is depth: recursion (or an ordinary call chain) deep enough, or a single frame greedy enough, exhausts the region.

> [!tension] abstraction ⟷ control
> Calling `f(x)` reads like one step. [[Anatomy of a Function|What the declaration promises]] is checked entirely at compile time, from text alone — that is the abstraction. Keeping the promise at run time is not free: an activation record must be built, filled and torn down for every call, on a resource whose size is fixed and finite. This note is the "below the line" real-machine picture that [[Anatomy of a Function|Anatomy of a Function]] only gestures at.

## Mental Model

> [!model] A pad of index cards, one per open call
> Each time a function is called, write a fresh index card: the arguments it was given, its own local variables, and — pinned to the back — exactly which line to return to. Drop it on top of the pad. Work only ever happens on the *top* card. Calling another function means writing one more card and dropping it on top; finishing a call means reading the return line off the top card, discarding the card, and resuming work on the one now exposed underneath.
> **Where it breaks:** a real pad is searched by hand. The call stack's "pad" is never searched — there is never more than one card anyone needs, and it is always the one on top, so finding it costs nothing.

```text
   A single stack frame, expanded (stack grows toward lower addresses)
  ┌───────────────────────────────┐   ← still the CALLER's frame
  │ argument 6, 7, ...  (spilled)  │     args beyond the register budget
  ├───────────────────────────────┤
  │ return address                 │     where the caller resumes
  ├───────────────────────────────┤
  │ saved caller frame-base        │     restored when this frame is popped
  ├───────────────────────────────┤   ← THIS frame's base
  │ parameters (a, b, c, ...)      │     copied in from registers/stack
  │ local variables                │     this call's own objects
  └───────────────────────────────┘   ← top of stack (grows downward from here)
```

## Step by Step

```mermaid
sequenceDiagram
    autonumber
    participant M as main()
    participant F as countdown(2)
    participant G as countdown(1)
    participant H as countdown(0)
    M->>F: call: push frame #1
    F->>G: call: push frame #2
    G->>H: call: push frame #3 (base case)
    H-->>G: return; pop frame #3
    G-->>F: return; pop frame #2
    F-->>M: return; pop frame #1
```

1. **Caller prepares (before the call).** Arguments are placed where the calling convention expects them — in registers for the first few, on the stack for the rest. [[Parameter Passing — Value, Reference, Pointer|Argument passing]] is ordinary initialization applied at exactly this boundary.
2. **The call instruction fires.** The processor pushes the *return address* — the instruction right after the call — and jumps to the callee. This one step is what makes "resume exactly where you were" automatic instead of something the program has to track by hand.
3. **Callee's prologue builds the frame.** The callee reserves space for its own locals and, if it needs one, saves the caller's frame-base pointer so it can be restored later. From here on, the callee's parameters and locals live at fixed offsets from its own frame's base.
4. **The body runs.** If the callee calls anything else — including itself — stages 1 through 3 repeat, pushing a new frame *on top* of this one. Nothing about the frame underneath changes; it simply waits.
5. **Callee's epilogue tears the frame down.** Locals go out of scope — their destructors, if any, run first (see [[Object Lifetime]]) — the frame-base is restored, and the stack pointer moves back to where it was before the call.
6. **`ret` pops the return address and jumps to it.** Control resumes in the caller at exactly the instruction after the call, with the caller's own frame untouched and still valid underneath.

## Under the Hood

> [!machine] A recursive call, annotated (GCC 14.2, x86-64 Linux, Compiler Explorer, `-O0 -std=c++20`)
> ```nasm
> factorial(int):
>         push  rbp                    ; ① save caller's frame-base
>         mov   rbp, rsp                ; ② this frame's base = current top
>         sub   rsp, 16                 ; ③ reserve 16 bytes for locals/spill
>         cmp   DWORD PTR [rbp-4], 1
>         jg    .L2
>         mov   eax, 1
>         jmp   .L3
> .L2:
>         mov   eax, DWORD PTR [rbp-4]
>         sub   eax, 1
>         mov   edi, eax
>         call  factorial(int)          ; ④ push return address, jump — a new frame
>         imul  eax, DWORD PTR [rbp-4]
> .L3:
>         leave                         ; ⑤ restore rsp and rbp together
>         ret                           ; ⑥ pop return address, jump back
> ```
> For `int factorial(int n) { return n <= 1 ? 1 : n * factorial(n - 1); }`.

1–3. The prologue *is* the frame's construction: eight bytes for the saved `rbp`, sixteen more reserved by `sub rsp, 16`.
4. `call` is the entire push-and-jump from Step 2 above, compressed into one instruction.
5–6. `leave` restores `rsp` and `rbp` in one step; `ret` is the pop-and-jump from Step 6.

**A call that makes no further calls needs no frame at all.** `int add5(int a,int b,int c,int d,int e){ return a+b+c+d+e; }` compiled at `-O2` is five instructions — no `push rbp`, no `sub rsp` — because the function never calls anything that could disturb its registers, so it has nothing to protect. [[Anatomy of a Function|The abstraction]] is free to use; the frame is a cost paid only by calls that actually need one.

**Not every call that looks recursive grows the stack.** `long sum_to(long n, long acc){ return n==0 ? acc : sum_to(n-1, acc+n); }` at `-O0` compiles to a real `call sum_to(long, long)` — one frame per level, exactly as above. At `-O2` (GCC 14.2, same target), the `call` disappears entirely: the compiler proves the recursive call is the *last* thing the function does (a **tail call**) and rewrites it as a jump back to the top of the same frame — a loop, not a growing stack. This is a compiler courtesy, not a language guarantee: nothing in the Standard promises tail-call elimination, and a debug build (`-O0`) still pays for every level exactly as drawn above.

> [!standard] What the Standard actually promises here
> `[intro.execution]` guarantees an automatic object's storage survives while its block is *suspended* by a nested call — that is the constraint this whole mechanism answers. It says nothing about a "stack," a frame, or a size limit for ordinary recursion. Annex B (`[implimits]`, informative) suggests a minimum of only **512** nested invocations for *`constexpr`* recursion evaluated at compile time; it gives no corresponding number for ordinary run-time recursion at all. How deep an ordinary call can nest before the underlying storage runs out is purely an implementation-and-OS question — see Consequences.

> [!machine] Two incompatible real-machine conventions for "the same" call
> The listing above uses the **System V AMD64 ABI** (Linux, macOS): the first six integer/pointer arguments travel in `rdi, rsi, rdx, rcx, r8, r9`. A build targeting 64-bit Windows follows the **Microsoft x64 calling convention** instead: only the first *four* go in registers, `rcx, rdx, r8, r9`, and the caller must additionally reserve 32 bytes of "shadow space" on the stack for the callee to spill them into if it needs to. Neither the register choice nor the frame layout drawn above is something a conforming C++ program may assume — `factorial`'s frame looks different, byte for byte, compiled for the other target.

## In Code

**1 · Each call's locals survive the calls nested inside it**

```cpp
#include <cstdio>

void countdown(int n) {
    std::printf("down %d\n", n);       // ①
    if (n > 0) countdown(n - 1);       // ②
    std::printf("up %d\n", n);         // ③
}

int main() {
    countdown(2);
}
// expect: down 2
// expect: down 1
// expect: down 0
// expect: up 0
// expect: up 1
// expect: up 2
```
1. Each call gets its *own* `n` — same name, different frame.
2. Pushes another frame on top; this one's `n` is untouched by what happens above it.
3. The "up" prints, read in reverse call order, prove it: `n` in the outermost call is still `2`, not clobbered by the two deeper calls that ran and returned in between.

**2 · Nested calls to *different* functions don't share storage either**

```cpp
#include <cstdio>

void inner() {
    int shared_looking = 99;                             // ① inner's own frame
    std::printf("inner sees %d\n", shared_looking);
}

void outer() {
    int shared_looking = 7;                              // ② a different object
    inner();
    std::printf("outer still sees %d\n", shared_looking); // ③
}

int main() {
    outer();
}
// expect: inner sees 99
// expect: outer still sees 7
```
1. `inner`'s `shared_looking` lives in `inner`'s frame.
2. Same name, but `outer`'s `shared_looking` is a different object in a different frame — they merely share a spelling.
3. Calling `inner()` cannot touch `outer`'s local: separate frames, separate storage, even though both sit on the same one stack.

**3 · A "recursive" function that never actually grows the stack (at `-O2`)**

```cpp
// cc: flags=-O2
#include <cstdio>

long sum_to(long n, long acc) {
    if (n == 0) return acc;
    return sum_to(n - 1, acc + n);     // ① tail position: nothing left to do after it
}

int main() {
    std::printf("%ld\n", sum_to(1'000'000, 0));
}
// expect: 500000500000
```
1. The recursive call is the very last action in the function — a **tail call**. At `-O2`, GCC turns this into the loop shown in *Under the Hood*; the same source built at `-O0` instead pushes a million real frames — at roughly 32 bytes of prologue overhead each, comfortably enough to exceed a typical few-mebibyte thread stack.

## Consequences

| Observed rule or failure | Explained by |
|---|---|
| Deep or unbounded [[Recursion|recursion]] crashes with "stack overflow" | Each frame is real storage in a fixed, finite region; enough nested calls exhaust it — see [[Process Memory Layout — Stack, Heap, Static]] |
| A single function with one huge local array can crash without any recursion at all | A frame's size is fixed by its own locals; one call can be greedy enough on its own |
| A pointer or reference to a local is garbage the instant its function returns | That local's frame is popped — its storage is gone, free to be reused by the very next call: [[Dangling Pointers and References]] |
| Popping a frame is effectively free; heap allocation isn't | Return is one register restore; the free store needs a real allocator call — see [[Process Memory Layout — Stack, Heap, Static]] |
| Some functions that "look recursive" never grow the stack at all | Tail-call elimination rewrites a self-call in tail position into a jump, at the optimizer's discretion — not a promise of the language |
| An exception can unwind through many suspended calls at once | Throwing walks the call stack outward, destroying each exited frame's automatic objects in turn, until a matching `catch` is found: [[Exceptions]], [[Stack Unwinding]] |
| A heavily optimized call sometimes shows no separate frame at all | The frame is an implementation convenience the compiler is free to elide when a call is cheap enough to inline: [[Inlining — Compiler Reality vs the Keyword]] |

## Connections

- **Prerequisites:** [[Process Memory Layout — Stack, Heap, Static]] — this note is the per-call detail of the region that map only draws in outline.
- **Enables:** [[Recursion]] (the stack turned into a control-flow tool, and the reason it has a depth limit) · [[Function Pointers]] and [[Callables and std-function]] (every callable still pays this same call/return cost).
- **Explains:** [[Dangling Pointers and References]] (a returned frame's storage) · [[Exceptions]] and [[Stack Unwinding]] (propagation *is* frame-by-frame unwinding) · [[Inlining — Compiler Reality vs the Keyword]] (the cost this mechanism prices, and what erases it).
- **Siblings:** [[Anatomy of a Function]] (the compile-time promise this note keeps at run time) · [[Parameter Passing — Value, Reference, Pointer]] (what actually gets copied into the new frame).
- **Domain:** [[Map — Functions]].
- **Practice:** *Continuum #9 Recursion Lab* — call a function recursively, print each frame's own address and local, and account for the order they unwind in.

## Check Yourself

> [!quiz]- Why does a stack — last-in-first-out — fit function calls better than, say, a general list any call could remove itself from?
> Because calls genuinely nest that way: the callee of a callee always finishes before its caller does. Given that guarantee, the *most recently pushed* frame is always the correct one to pop next, so no search is ever needed — pop is simply "whatever's on top," which is why it costs one pointer move instead of a lookup.

> [!quiz]- Two different functions each declare a local variable with the same name. Why doesn't calling one from the other cause a conflict?
> They're different objects in different stack frames. A name is resolved at compile time to an offset within *its own function's* frame; nothing about calling another function reaches into or overwrites the caller's frame. See In Code, example 2.

> [!quiz]- Predict: `sum_to` from In Code, example 3, is recompiled at `-O0` and called with `n = 1'000'000`. Does it still print `500000500000`?
> Not reliably — likely a crash instead. Without the tail-call rewrite, each level pushes a real frame (as shown in *Under the Hood*'s `-O0` listing), and a million of them is tens of megabytes, comfortably past a typical thread's fixed stack reservation. The `-O2` version's correctness depended on an optimization the language never promises.

> [!quiz]- Does the C++ Standard guarantee a minimum recursion depth for an ordinary (non-`constexpr`) function?
> No. Annex B gives an informative minimum of 512 for *`constexpr`* recursion evaluated at compile time, and nothing corresponding for run-time recursion — how deep an ordinary call can nest is purely a function of the implementation's stack size and each frame's footprint, neither of which the Standard constrains.

## Sources

- PPP §7.4 "Function call and return": the function activation record introduced with a worked recursive-descent example — `expression()` calling `term()` calling `primary()`, each getting its own record, drawn as a growing stack of them.
- PPP §5.9 "Program structure": an infinite recursion is described as ending only once the running program exhausts the memory available to hold the ever-growing chain of calls.
- Primer §6.1 "Function Basics" (p. 202–203): a function call initializes parameters from arguments and transfers control, suspending the calling function's execution until the callee returns.
- Tour §15.3 "array" (p. 203): the stack named directly as a limited resource, with stack overflow as the cost of relying on it too heavily.
- Tour §4.2 "Exceptions" (p. 44): exception propagation described as unwinding the function call stack to reach a handler.
- Draft standard `[intro.execution]` ¶1: an automatic object's storage persists while its block is suspended by a nested function call — the constraint this note's mechanism answers: https://eel.is/c++draft/intro.execution
- Draft standard Annex B `[implimits]`: an informative minimum of 512 nested `constexpr` function invocations, with no corresponding figure given for ordinary run-time recursion: https://eel.is/c++draft/implimits
- System V Application Binary Interface, AMD64 Architecture Processor Supplement (integer argument-register order `rdi, rsi, rdx, rcx, r8, r9`): https://gitlab.com/x86-psABIs/x86-64-ABI
- Microsoft Learn, *x64 calling convention* (four-register convention `rcx, rdx, r8, r9` plus 32-byte shadow space): https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention
- Microsoft Learn, *Thread Stack Size* (default 1 MB reserved stack; a guard page is used to detect overflow): https://learn.microsoft.com/en-us/windows/win32/procthread/thread-stack-size
- See [[Map — Functions]] for how this note connects to the rest of the domain.
