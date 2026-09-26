---
id: compilers-and-flags
title: Compilers and Essential Flags
type: guide
domain: D14
tier: 1
status: draft
standard: C++98
prereqs: []
related:
- "[[Map — Tooling & Engineering]]"
- "[[Undefined Behavior]]"
practice:
- 1
tags:
- type/guide
- domain/d14
- tier/1
- tension/safety-vs-performance
created: 2026-09-26
updated: 2026-09-26
---

# Compilers and Essential Flags

> [!essence]
> A compiler that produces an executable has satisfied the Standard's only universal obligation: reject what is ill-formed. Everything else — the warning that would have caught a sign-comparison bug, the optimization that makes a release build fast, the instrumentation that catches undefined behavior the instant it fires — is a flag you have to ask for by name.

## Purpose

[[Map — Tooling & Engineering|This domain]] exists because a conforming compiler is required to diagnose what is *ill-formed* and nothing more; a huge second category, undefined behavior, is explicitly exempt from any diagnostic requirement at all. A compiler is therefore free to accept a program that reads past the end of an array or compares a signed loop counter against an unsigned size and say nothing about either, not because the tool is broken but because nothing in its contract obliges it to look. The consequence lands on whoever types the compile command: a clean, silent compile is evidence that nothing *ill-formed* was found, never evidence that the program is correct. Both the Primer and PPP treat the fix as a first lesson rather than an advanced one: the Primer states its authors' own preference for `-Wall` on the GNU compiler and `/W4` on Microsoft's, right beside the very first compile command a reader ever types (Primer §1.2, p. 5), and PPP goes further, telling a beginner to make finding and enabling a warning flag — usually `-Wall` — one of the first things they learn to do, on the grounds that skipping it costs far more grief later (PPP §2.10). GCC and Clang answer with three largely independent families of flag: which dialect of the language to accept (`-std=`), how hard to look for constructs a human would call suspicious even though the grammar permits them (`-Wall`, `-Wextra`, `-Wpedantic`), and how much liberty to give the optimizer once the code is accepted (`-O0` through `-O3`, `-Os`, `-Og`). A fourth family, sanitizers, is not a compiler check at all: it rewrites the program to check itself while it runs.

> [!tension] safety ⟷ performance
> `-Wall` and `-Wextra` buy defect detection for close to nothing: they extend a compiler pass that already ran, reporting what the front end already noticed. Sanitizers buy something stronger — a checked *execution* — at a real cost the tooling states plainly: AddressSanitizer's typical instrumented slowdown is 2×, and its runtime "is not meant to be linked against production executables" (Clang, *AddressSanitizer*). No single build config gets both properties at once, which is why a real project keeps a checked build and a release build and never confuses the two.

## How to Use It

### Choosing the compiler and the standard

`g++`, `clang++` and MSVC's `cl` each accept a flag naming the language dialect: `-std=c++20` (GNU/Clang) or `/std:c++20` (MSVC). Omit it and you get whichever dialect that specific compiler release defaults to — never assume it matches the standard a note here describes. The Primer's own installation instructions, current in 2012, told readers they might need `-std=c++0x` just to turn on C++11 support at all (Primer §1.2, p. 5): the flag's entire job was opting into a standard the compiler didn't yet default to, and every `-std=` flag since has done the same job for a newer target.

### Warnings: checks the compiler already ran, for free

```cpp
#include <iostream>
#include <vector>

int sum_first(const std::vector<int>& v, int count) {
    int total = 0;
    for (int i = 0; i < count; ++i)   // ①
        if (i < v.size())             // ②
            total += v[i];
    return total;
}

int main() {
    std::vector<int> data{1, 2, 3};
    std::cout << sum_first(data, 5) << "\n";   // expect: 6
}
```
① `i` is a signed `int` counter — nothing about the loop looks wrong.
② `v.size()` returns `std::vector<int>::size_type`, an unsigned type. Every iteration compares a signed value against an unsigned one.

```text
$ g++ -std=c++20 -O0 -o prog prog.cpp
$                                          # silent: nothing here is ill-formed

$ g++ -std=c++20 -Wall -O0 -o prog prog.cpp
prog.cpp:6:15: warning: comparison of integer expressions of different
signedness: 'int' and 'std::vector<int>::size_type' {aka 'long unsigned int'}
[-Wsign-compare]
```
Both compiles produce the same binary; only the second one tells you anything. `-Wsign-compare` is exactly the flag the GCC manual lists as one that `-Wall` "turns on" for C++, though in plain C it waits for `-Wextra` (GCC, *Warning Options*) — a version-of-the-language distinction that changes nothing about the code, only about which flag admits it exists. The program above runs correctly today because `count` stays within bounds after the check; the same comparison misbehaves the day `count` goes negative, since a negative `int` compared against an unsigned `size_type` is promoted to a huge unsigned value and the "safety check" stops protecting anything.

`-Wall` "enables all the warnings about constructions that some users consider questionable, and that are easy to avoid" (GCC, *Warning Options*); `-Wextra` layers on flags the manual describes as "extra warning flags that are not enabled by `-Wall`" — unused parameters, empty statement bodies, type-limit comparisons that can never be true. `-Wpedantic` is a different axis entirely: it "issue[s] all the warnings demanded by strict ISO C and ISO C++," diagnosing GNU extensions the other two accept without comment, and it does so "following the version of the ISO C or C++ standard specified by any `-std` option used" (GCC, *Warning Options*) — so its verdict moves with whichever `-std=` flag you chose. `-Werror` promotes every enabled warning to a hard compile failure; a team that wants warnings enforced rather than merely visible turns it on in the build, not in each programmer's head.

### Optimization levels: what "compiled" doesn't mean

| Flag | What GCC says it does | Reach for it when |
|---|---|---|
| `-O0` (default) | "Reduce compilation time and make debugging produce the expected results" | Every ordinary edit-compile-debug cycle |
| `-Og` | "keeping in mind debugging experience… a reasonable blend of optimization, fast compilation and debugging" | `-O0` itself feels too slow to iterate on |
| `-O1` | "tries to reduce code size and execution time, without performing any optimizations that take a great deal of… time" | Rarely chosen directly; GCC's own first rung toward `-O2` |
| `-O2` | "performs nearly all supported optimizations that do not involve a space-speed tradeoff" | The default release flag for most projects |
| `-O3` | turns on everything `-O2` does, plus more aggressive, sometimes size-costly transforms | Compute-heavy code, only after measuring against `-O2` |
| `-Os` | "enables all `-O2` optimizations except those that often increase code size" | Binary size is the binding constraint |

(GCC, *Optimize Options*, for every cell above.) The gap between rows is not cosmetic: Pikus reports that an unoptimized build, "optimization level zero," can "run an order of magnitude slower" than the same program built with every optimization enabled (Pikus ch. 10, §"Compilers optimizing code," p. 348) — which is exactly why timing a `-O0` debug build tells you nothing about the binary you intend to ship, and why the sanitizer runs below are usually built at `-O1` or `-Og`, not `-O0`, when the timing has to mean anything at all.

### Debug info and sanitizers: checking one real execution

`-g` embeds debug symbols; both a debugger and a symbolized sanitizer report need it — Clang's own instructions for a readable UBSan stack trace start with "compile with `-g`… to get proper debug information in your binary" (Clang, *UndefinedBehaviorSanitizer*). `-fsanitize=address,undefined` rewrites the build to check every access and every arithmetic operation as it happens, catching the exact class of bug no warning flag can see because no warning flag runs the program. The cost is the one stated in the tension above: real, measured, and confined to a build nobody ships.

Not every toolchain links the sanitizer runtime the checks above assume. Clang's manual documents the fallback directly: `-fsanitize-trap=…` makes a check "execute a trap instruction" instead of calling into the runtime, a mode that "doesn't require UBSan run-time support" (Clang, *UndefinedBehaviorSanitizer*). Trap mode still stops the program at the exact faulting operation; it just reports a bare signal instead of naming the rule that broke, which is the trade a platform without the sanitizer runtime accepts rather than losing the check entirely.

### A baseline invocation

```text
# development: catch what you can before running, catch the rest while running
$ g++ -std=c++20 -Wall -Wextra -Wpedantic -Og -g -fsanitize=address,undefined -o prog prog.cpp

# release: nothing left turned on that a shipped binary should pay for
$ g++ -std=c++20 -O2 -DNDEBUG -o prog prog.cpp
```
No single invocation is "the" right one — it is a choice about which half of the tension above you are paying for on this particular build.

## Coverage Map
| Section | What it covers | Compendium notes |
|---|---|---|
| Warnings (`-Wall`, `-Wextra`, `-Wpedantic`, `-Werror`) | Compile-time checks for legal but suspicious code | [[Warnings as Guardrails]] |
| Optimization levels (`-O0`…`-O3`, `-Os`, `-Og`) | What the compiler is licensed to change once code is accepted | [[The As-If Rule]], [[Map — Performance & the Machine]] |
| Sanitizers (`-fsanitize=…`) | Run-time instrumentation for memory errors and undefined behavior | [[Sanitizers — ASan, UBSan, TSan]] |
| Driving these flags the same way on every machine | Build systems and multi-file projects | [[CMake Fundamentals]] |
| Rule-based checking beyond the compiler's own warnings | Static analyzers layered on top of these flags | [[Static Analysis and clang-tidy]] |

## Connections
- **Prerequisites:** none formally, but [[Map — What C++ Is]] is where "a clean compile isn't proof of correctness" is derived from the Standard's own ill-formed/undefined-behavior split; this guide is that idea turned into a command line.
- **This enables:** every later note in [[Map — Tooling & Engineering|this domain]] assumes a reader who already knows what `-Wall` and `-O2` do — [[Warnings as Guardrails]], [[CMake Fundamentals]], [[Debugging with a Debugger]] and [[Sanitizers — ASan, UBSan, TSan]] all build on the vocabulary fixed here.
- **Practice:** *Continuum #1 Hello, Compiler* — compile the same file with no flags, then with `-Wall -Wextra`, and read what changes before letting a build system hide the command from you.
- **Domain:** [[Map — Tooling & Engineering]].

## Sources
- Primer §1.2 "A First Look at Input/Output" (p. 5): recommends `-Wall` (GNU) / `/W4` (Microsoft), and notes the historical `-std=c++0x` flag needed to enable C++11 support at all.
- PPP §2.10 "Type deduction: auto": urges the reader to find and enable a warning flag (typically `-Wall`) and to keep code clean of the warnings it reports, warning that skipping the habit costs real grief later.
- Pikus ch. 10 "Compiler Optimizations in C++," §"Compilers optimizing code" (p. 348): an unoptimized build ("optimization level zero") can run "an order of magnitude slower" than a fully optimized one.
- GCC documentation, *Options to Request or Suppress Warnings*: exact wording and flag lists for `-Wall`, `-Wextra`, `-Wpedantic`, `-Wsign-compare`, `-pedantic-errors` — https://gcc.gnu.org/onlinedocs/gcc/Warning-Options.html
- GCC documentation, *Options That Control Optimization*: exact wording for `-O0`, `-O1`, `-O2`, `-O3`, `-Os`, `-Og` — https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html
- Clang documentation, *UndefinedBehaviorSanitizer*: `-fsanitize=undefined` usage, `-g` for symbolized stack traces, and `-fsanitize-trap=` as the runtime-free fallback — https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html
- Clang documentation, *AddressSanitizer*: typical instrumented slowdown of 2×; the runtime "is not meant to be linked against production executables" — https://clang.llvm.org/docs/AddressSanitizer.html
- Verified against the vault's own toolchain, 2026-09-26: `g++` (GCC 11, MinGW) reproduces the `-Wsign-compare` warning above exactly as GCC's manual describes it.
