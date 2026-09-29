---
id: abstraction-layers
title: Levels of Abstraction — From Bits to Libraries
type: concept
domain: D00
tier: 1
status: draft
standard: C++98
prereqs:
- "[[The C++ Design Philosophy]]"
related:
- "[[The C++ Abstract Machine]]"
- "[[The ISO Standard, Compilers and Conformance]]"
- "[[Zero-Overhead Principle]]"
- "[[Translation Units]]"
practice: []
tags:
- type/concept
- domain/d00
- tier/1
- tension/abstraction-vs-control
- std/c++98
- std/c++11
- std/c++20
created: 2026-09-28
updated: 2026-09-28
---

# Levels of Abstraction — From Bits to Libraries

> [!essence]
> A C++ program is a stack of vocabularies — hardware, machine code, assembly, the core language, and libraries — where each level's words are defined entirely in terms of the level directly below it. Climbing the stack changes what you're allowed to say, never what the machine ends up doing, which is exactly what lets [[The C++ Design Philosophy|zero-overhead abstraction]] hold as a promise rather than an aspiration.

## The Problem

> [!principle] Constraint → Consequence → Design
> 1. **Constraint:** A processor executes only fixed-width binary instructions that name registers and memory addresses. No person can reliably write, or read back, a program of any real size directly in that vocabulary — not because it's tedious, but because nothing in it groups related decisions together or names an intention.
> 2. **Consequence:** Without an intermediate vocabulary, every concern a program touches — how a number is represented, how a resource is released, how a set of related operations belongs together — would have to be re-decided at the point of every single instruction, and a reader would have to hold the entire machine state in mind to follow any one part of it.
> 3. **Requirement:** The language needs a *sequence* of vocabularies, each one defined strictly in terms of the vocabulary beneath it, so that a person working at one level can trust — rather than re-derive — everything below, and so that moving up a level costs nothing the level below wasn't already going to cost.
> 4. **Design:** C++ is built as such a tower. Machine code is a sequence of bit patterns an instruction-set architecture (ISA) gives meaning to; assembly language is a one-to-one mnemonic naming for those same bit patterns; the core language (types, expressions, functions, pointers) compiles down to that machine code with nothing added; the class/template abstraction mechanisms are themselves written in the core language and compile down through it; and libraries — the standard library and your own — are built from those mechanisms with no access a user's own code doesn't also have (Tour §2.1, p. 21).
> 5. **Price:** A claim true at one level is not automatically true at the level above or below it. "This variable has a name" is a core-language fact; the optimized binary may keep its value only in a register, or nowhere at all. Reading a program correctly means knowing, sentence by sentence, which level a given statement belongs to — and mixing levels by accident is the single most common way to reason wrongly about what a C++ program does.

> [!tension] abstraction ⟷ control
> Every level above hardware exists to let you stop thinking about the level below it — but [[The C++ Design Philosophy]] refuses to let that convenience cost anything extra, and refuses to stop you from dropping back down when you need to. A level you can't afford to leave, and a level you can't afford to climb into, are both failures of the same design goal.

## Mental Model

```text
 LIBRARIES        std::vector · std::string · your own TinyStack        ▲ what you usually write
┌──────────────────────────────────────────────────────────────────┐   │ built from, no special access
│ ABSTRACTION MECHANISMS   classes · templates · RAII · overloading │   │
├──────────────────────────────────────────────────────────────────┤   │ compiles down to, unchanged
│ CORE LANGUAGE     types · expressions · functions · pointers      │   │
├──────────────────────────────────────────────────────────────────┤   │ compiles down to
│ ASSEMBLY LANGUAGE     mnemonics: mov · lea · call · ret           │   │ 1-to-1 naming of
├──────────────────────────────────────────────────────────────────┤   │
│ MACHINE CODE      bit patterns: 8d 04 37 · f3 0f 1e fa            │   │ interpreted by
├──────────────────────────────────────────────────────────────────┤   │
│ HARDWARE          registers · memory cells · wires                │   ▼ what actually runs
└──────────────────────────────────────────────────────────────────┘
```

> [!model] A relay of translators, and where it breaks
> Think of each level as a translator who only ever has to know the vocabulary directly above and directly below them — the library author needn't know an ISA, and the ISA's designer needn't know what `std::vector` is. **Where it breaks:** a chain of human translators paraphrases, and meaning can drift or shrink with each handoff. C++'s levels don't paraphrase — the whole point of the tower is that a translation is mechanical and exact enough that the compiler is free to erase intermediate levels entirely. "Level" describes how you *think* about the program, not a separate thing that persists once it's built.

## Mechanics

| Level | Vocabulary | Who fixes its rules | Example |
|---|---|---|---|
| Hardware | registers, memory cells, wires | the physical machine and its ISA manual | a 64-bit general-purpose register |
| Machine code | opcodes and operands as bit patterns | the ISA (e.g. x86-64, AArch64) | the byte sequence `8d 04 37` |
| Assembly language | mnemonics, one name per opcode | the assembler for that ISA | `lea eax, [rdi+rsi]` |
| Core language | types, expressions, functions, pointers | the C++ Standard | `int add(int a, int b) { return a + b; }` |
| Abstraction mechanisms | classes, templates, RAII, overloading | the C++ Standard (same jurisdiction) | a class that wraps that same addition |
| Libraries | containers, algorithms, domain types | the Standard (for `std::`) or the library's author | `std::vector`, or a hand-written `TinyStack` |

> [!standard] The Standard's jurisdiction starts at the core language
> The C++ Standard defines a program's meaning only through the abstract machine's *observable behavior* — what it does with `volatile` objects and with input/output (`[intro.abstract]`). It says nothing about registers, opcodes, or voltages: machine code and hardware are the implementation's business, bound only by the obligation to reproduce that observable behavior faithfully. Everything from the core language upward is what a conforming compiler is actually held to; everything below it is a real machine's affair, not the language's. See [[The C++ Abstract Machine]] for the object this boundary is drawn around.

The highest level that can express a problem's actual requirements is the one to work at (Tour §18.7, p. 253, "Advice" §18.1) — not because lower levels are forbidden, but because every level above hardware was built precisely so you wouldn't need them unless a specific requirement (raw layout control, a missing safety net, a hardware feature no library exposes) forces you back down.

## Under the Hood

> [!machine] Assembly and machine code are two notations for the same fact
> The core-language function `int add(int a, int b) { return a + b; }`, compiled with GCC 11.4.0 (Ubuntu 22.04, x86-64, `-O2`), produces exactly one meaningful instruction plus a mandatory prologue check:
> ```nasm
> add(int, int):
>         endbr64                    ; CET landing pad, not part of the addition
>         lea    eax, [rdi+rsi]      ; the addition itself: one instruction
>         ret
> ```
> That mnemonic line is a human-readable name for a fixed byte sequence; nothing is lost translating between them:
> ```text
>  bytes (hex)     mnemonic                    meaning
>  f3 0f 1e fa      endbr64                     mark a valid indirect-call target
>  8d 04 37         lea eax, [rdi+rsi*1]        eax := rdi + rsi   (the "add")
>  c3               ret                         return to caller
> ```
> Assembly language adds nothing machine code didn't already have — it is the same three instructions, spelled so a person can read them. Climbing from core language to assembly to machine code changed the notation twice and the computation not at all.

## In Code

**1 · Two levels, one line**

```cpp
#include <iostream>

int main() {
    int a = 3, b = 4;
    std::cout << (a + b) << '\n';   // ①
}
// expect: 7
```
1. `a + b` and `std::cout <<` belong to different levels of the tower. `a + b` is core-language arithmetic on a built-in type — the same operation compiled above to one instruction. `std::cout << x` is a library-level function call: `operator<<` is an ordinary overloaded function, not a facility the compiler treats specially. Neither half needs to know how the other is implemented; that's the entire benefit of a level boundary.

**2 · A leak in the tower: `sizeof(long)` is not the core language's to promise**

```cpp
#include <cstdio>

int main() {
    std::printf("%zu\n", sizeof(long));   // ①
}
// prints: 8 on LP64 (Linux/macOS x86-64) · 4 on LLP64 (64-bit Windows)
```
1. `long`'s width is implementation-defined, not a core-language guarantee: the language deliberately does not paper over this hardware/ABI fact, because doing so would either misdescribe the machine or force every platform to pay for a width its hardware doesn't natively hold. Verified on this vault's toolchain, GCC 11.4.0, Ubuntu 22.04 x86-64 (LP64): the program prints `8`. A caller on 64-bit Windows must still ask with `sizeof`, never assume — the abstraction leaks exactly here, by design.

**3 · Libraries have no special access — you can build one**

```cpp
#include <iostream>

class TinyStack {
public:
    explicit TinyStack(int capacity) : data_(new int[capacity]), cap_(capacity) {}
    ~TinyStack() { delete[] data_; }
    void push(int v) { data_[size_++] = v; }   // ①
    int pop() { return data_[--size_]; }
    int size() const { return size_; }
private:
    int* data_;
    int cap_;      // ②
    int size_ = 0;
};

int main() {
    TinyStack s(4);
    s.push(10);
    s.push(20);
    std::cout << s.pop() << ' ' << s.size() << '\n';
}
// expect: 20 1
```
1. `push` and `pop` are ordinary member functions doing ordinary pointer arithmetic — ASan/UBSan-clean on this vault's toolchain (GCC 11.4.0, x86-64). Nothing here calls into the compiler for a privilege user code lacks.
2. `TinyStack` is a pointer, a capacity, and a size — the same three fields `std::vector` itself is built from (PPP §15.2, "vector basics," walks through exactly this construction). The library level buys convenience and (elsewhere) bounds checking, never access to a lower level that your own code is denied.

## Pitfalls

> [!ub] A hardware fact is not a language guarantee
> x86-64 happens to represent signed overflow as silent wraparound in two's-complement arithmetic. Writing `INT_MAX + 1` and expecting the wrapped value because "that's what the hardware does" mistakes a machine-code-level fact for a core-language rule: signed integer overflow is undefined behavior at the source level regardless of what any one ISA happens to do with the bits. See [[Undefined Behavior]].

> [!trap] "The stack" is a hardware-level nickname, not a source-level rule
> A variable's *storage duration* is a core-language concept the Standard defines; "the stack" is the name one common implementation strategy gives to automatic storage at the hardware/OS level. Treating "it's on the stack" as something a C++ program can rely on skips past the level where the guarantee would actually have to live. See [[Storage Duration]] and [[Process Memory Layout — Stack, Heap, Static]].

> [!trap] Debugging with assembly from the wrong build
> [[The As-If Rule|The as-if rule]] lets a compiler erase or rearrange levels freely, so long as observable behavior matches. Assembly captured at `-O0` (nothing inlined, close to one instruction group per statement) can look nothing like the `-O2` binary that actually shipped. Reading the *wrong* level's translation and drawing conclusions about the level above it is a common, avoidable mistake — always state the flags a disassembly came from.

## Evolution

| Standard | Change | Why |
|---|---|---|
| "C with Classes" (1979–1985) | No distinct abstraction-mechanism level yet; classes translated straight into C source | Prove the idea worked before asking any compiler vendor to standardize its cost |
| **C++98** | Templates and classes formalized as a level every conforming compiler must give the same meaning | Fix "abstraction mechanisms" as a portable vocabulary, not one vendor's convention |
| C++11 | `constexpr` lets a computation move from the run-time layer into the compile-time layer without leaving the source language | Push cost out of the running program entirely, not merely out of an abstraction's design (Pikus, "Lifting knowledge from runtime to compile time," p. 365) |
| C++20 | Modules replace the textual, preprocessor-level header layer with a compiled interface boundary | Remove a layer that existed only as a historical workaround, not a level the design ever needed |

## Connections

- **Prerequisites:** [[The C++ Design Philosophy]] — the two pillars this tower is built to satisfy at every level.
- **Enables:** [[The C++ Abstract Machine]] (draft) — the formal object that marks exactly where the Standard's jurisdiction over this tower begins · [[The ISO Standard, Compilers and Conformance]] (planned) — who is bound by the core-language-and-up levels, and how.
- **Siblings:** [[Zero-Overhead Principle]] — the testable claim that climbing a level costs nothing · [[Translation Units]] — how source text at the core-language level is assembled, file by file, into the machine-code level.
- **Domain:** [[Map — What C++ Is]].
- **Practice:** no Continuum project is registered against this note yet; every project exercises the tower implicitly by asking you to choose a level.

## Check Yourself

> [!quiz]- Name the five levels this note identifies, from hardware to libraries, and state the one relation that holds between every adjacent pair.
> Hardware → machine code → assembly language → core language → abstraction mechanisms/libraries. Each level's vocabulary names, exactly and without adding anything, what the level directly below it already does.

> [!quiz]- Why must climbing a level (writing a class instead of raw pointers) cost nothing extra, rather than merely being convenient?
> If naming an idea cost anything beyond what the unnamed, lower-level equivalent already cost, every program with a performance budget would be forced back down to the lowest level for everything, and the tower would collapse into one level in practice. Zero cost is what keeps the higher levels usable everywhere, not just where performance doesn't matter — see [[Zero-Overhead Principle]].

> [!quiz]- In example 3, is `TinyStack` doing anything `std::vector` doesn't also do underneath?
> No. Both are a pointer, a capacity, and a size, manipulated with `new[]`/`delete[]` and ordinary arithmetic — the same core-language tools available to any program. `std::vector` adds convenience and (in `.at()`) a bounds check; it has no access to a level `TinyStack` is denied.

> [!quiz]- Which level does the fact "`sizeof(long)` is 8 on this machine" belong to, and why can't the core language settle it once and for all?
> The hardware/ABI level (implementation-defined, per the platform's data model — LP64 vs. LLP64). Fixing a single width in the core language would force one hardware convention onto every platform C++ targets, contradicting the reason the abstract machine leaves hardware specifics out of its own definition in the first place.

## Sources

- Tour §2.1 "Introduction" (p. 21): built-in types are deliberately low-level and hardware-reflecting; abstraction mechanisms are layered on top so programmers can build high-level facilities out of them.
- Tour §18.7 "Advice" (p. 253), point [2]: work at the highest level of abstraction you can afford (§18.1).
- PPP §1.1 "Programs" (ch. 1): a program is a precise description translated from human-readable form into machine instructions by a compiler, then executed (PPP has no printed page labels; cited by section).
- PPP §15.2 "vector basics" (ch. 15): building a minimal vector-like type from a pointer, a capacity, and a size — the technique `TinyStack` mirrors in this note's own words and code.
- Pikus, "Lifting knowledge from runtime to compile time" (p. 365): moving a computation from the run-time layer to the compile-time layer as a distinct optimization move, not just a stylistic one.
- Draft standard `[intro.abstract]`: the abstract machine and observable behavior, marking where the Standard's jurisdiction over this tower begins: https://eel.is/c++draft/intro.abstract
- C++ Core Guidelines, P.1 "Express ideas directly in code": https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#rp-direct
