---
id: what-a-type-is
title: What a Type Is
type: concept
domain: D02
tier: 1
status: draft
standard: C++98
prereqs: []
related:
- "[[Fundamental Types]]"
- "[[Classes as User-Defined Types]]"
- "[[const and Const-Correctness]]"
- "[[The C++ Object Model — What an Object Is]]"
practice: []
tags:
- type/concept
- domain/d02
- tier/1
- tension/compile-time-vs-run-time
- tension/safety-vs-performance
created: 2026-09-25
updated: 2026-09-25
---

# What a Type Is

> [!essence]
> A **type** is the compiler's fixed answer, settled before the program ever runs, to three questions about a name or expression: which values may it hold, which operations are legal on it, and how are those values laid out in bits? Every later idea in this domain — conversions, `const`, `auto`, enumerations — is a variation on that one triple, or a consequence of it.

## The Problem

A CPU moves and stores fixed-width groups of bits. Nothing about a byte at some address announces what it is *for*: the same eight bits could be a small integer, part of a larger number, a character, or a fragment of an address. C++ has to attach meaning to storage before it can let you write `i + j` and have that mean something.

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint:** Hardware stores and moves fixed-width bit patterns; a byte in memory carries no built-in tag saying whether it is a number, a character, or something else.
> 2. **Consequence:** Without an external rule, the same 32 bits could be read as an `int`, a `float`, or a pointer, and an operation like `+` or `*p` would be ambiguous — or meaningless — for at least one of those readings.
> 3. **Requirement:** Something must fix, for every name and expression, *before a single instruction runs*: which bit patterns are legal values, which operations are defined on them, and how many bits they occupy and how those bits are arranged — and it must do this for free at run time, or the cost of checking would swallow the benefit of having simple operations like integer addition in the first place.
> 4. **Design:** C++ makes that fixed triple — **values × operations × representation** — the *type*. A name's type is fixed at its declaration, enforced by the compiler at every subsequent use, and then discarded; it never travels with the bits at run time.
> 5. **Price:** because the tag exists only while compiling, nothing re-checks it while the program runs. A cast, a `union`, or a pointer of the wrong type can make the machine act on bits as though they were a type they never were — and the language's answer to "what happens then" is [[Undefined Behavior]], not a caught error. See Pitfalls.

> [!tension] compile-time ⟷ run-time
> Type checking happens exactly once, while compiling, and leaves nothing behind afterward. An `int` and a `float` occupying the same four bytes are, to the CPU, interchangeable — only the compiler's choice of *instruction* ever distinguished them (see Under the Hood). That single fact is what makes a type free to use: there is no tag to consult, no check to run, at every `+` or assignment. It is also what makes the type system defeatable: nothing at run time stops a `reinterpret_cast` from asking the compiler to apply the wrong lens to a set of bits.

> [!tension] safety ⟷ performance
> Because the check is compile-time-only, C++ buys zero-overhead typing at the price of zero run-time enforcement. A language that re-verified every value against its type at run time could catch the violation in Pitfalls below; C++ instead trusts the program to have already been checked, and optimizes on that trust ([[The As-If Rule]]). [[Map — Errors & Contracts]] returns to this trade-off as a general design choice, not one specific to types.

## Mental Model

```text
   TYPE = int                              TYPE = Meters
  ┌─────────────────────────────┐         ┌─────────────────────────────┐
  │ VALUES                      │         │ VALUES                      │
  │  -2147483648 … 2147483647   │         │  any double a programmer    │
  │  (typical 32-bit; Primer    │         │  chooses to allow — this    │
  │  guarantees only ≥16 bits)  │         │  class enforces none        │
  ├─────────────────────────────┤         ├─────────────────────────────┤
  │ OPERATIONS                  │         │ OPERATIONS                  │
  │  + - * / % ++ -- < <= ==    │         │  operator+   (declared)     │
  │  built into the language    │         │  nothing else — no *, no << │
  ├─────────────────────────────┤         ├─────────────────────────────┤
  │ REPRESENTATION               │        │ REPRESENTATION               │
  │  4 bytes, two's complement  │         │  8 bytes: one double member  │
  │  (mandatory since C++20)    │         │  (sizeof(Meters) == 8)       │
  └─────────────────────────────┘         └─────────────────────────────┘
```

Two very different types, one identical shape: a fixed set of legal values, a fixed set of legal operations, a fixed layout in bits. `int` gets its triple from the language definition; `Meters` gets its triple from a programmer's declarations — see *Mechanics* below.

> [!model] A type is a lens the compiler holds up to a name, not a label glued to memory
> Look at the same four bytes through the `int` lens and you see a whole number; look through the `float` lens and you see a fractional value with an exponent. The bits don't change — only which operations and which meaning are legal changes with the lens.
> **Where it breaks:** a lens is something you consciously pick up and swap. C++ does not let a name switch lenses on its own — every ordinary use of a name goes through its *one* declared type automatically, with no swapping involved. Deliberately changing the lens (a cast, a `union`, copying bytes into a different type) is possible, but it is an explicit act that steps outside the compiler's guarantee rather than something the type system offers you.

## Mechanics

> [!standard] What the Standard actually fixes
> `[basic.types.general]` states that types describe objects, references, or functions, and defines the *object representation* of a type `T` as the `sizeof(T)` bytes a non-bit-field object of type `T` occupies, and the *value representation* as the subset of those bits that participate in representing a value. The Standard fixes representation and (through the grammar and overload resolution) which operations are well-formed; it does not store either fact anywhere the running program can inspect.

| Leg | What it fixes | For `int` | For `Meters` (a user type) |
|---|---|---|---|
| **Values** | The legal contents a variable of the type may hold | Whole numbers in an implementation-defined range, minimum ±32767 (Primer Table 2.1) | Whatever the class permits — here, any `double`, because the class adds no invariant |
| **Operations** | The expressions the compiler accepts | `+ - * / % ++ -- < <= == …`, fixed by the language grammar | Exactly the member and non-member functions declared for it — nothing more |
| **Representation** | The bits: how many, and how they encode a value | 4 bytes, two's-complement (mandatory since C++20, P0907R4) | Whatever its data members lay out — one `double`, so `sizeof(Meters) == sizeof(double)` |

**Built-in vs. user-defined is a difference in who supplies the triple, not in the shape of the triple.** For a built-in type like `int`, the compiler already knows the representation and the legal operations without being told: they are baked into the language itself, with no source-code declaration required to teach the compiler what `int` means (PPP §8.1). For a user-defined type like `Meters` or `std::string`, the *class declaration itself* is what fixes the triple: data members fix the representation, member and friend functions fix the legal operations, and the constructors and any invariant the class maintains fix which values are ever actually reachable ([[Classes as User-Defined Types]], [[Encapsulation and Class Invariants]]). The mechanism is identical; only the source of the answer changes.

**A type is attached to a *name or expression*, once, and does not change.** Declaring `int n;` fixes `n`'s type for every later use of `n` in that scope; nothing in ordinary C++ lets a name's declared type mutate mid-program (templates and `auto` still pick one fixed type per instantiation — they don't defer the choice to run time).

## Under the Hood

> [!machine] The type steers which instructions get emitted, then disappears
> Two functions, both taking two 4-byte operands and adding them, compiled with GCC 11, `-O2`, x86-64:
> ```nasm
> add_int(int, int):        ; int add_int(int a, int b) { return a + b; }
>     lea eax, [rdi+rsi]    ; integer add, done in one lea
>     ret
> add_float(float, float):  ; float add_float(float a, float b) { return a + b; }
>     addss xmm0, xmm1      ; SSE scalar-single add — a completely different unit
>     ret
> ```
> Same operand width, same operator spelled `+` in the source — entirely different instructions, entirely different registers (general-purpose vs. `xmm`). The type decided *at compile time* which hardware operation `+` meant; at run time, nothing re-derives that choice. This is also why the type disappears from the running program: once the right instruction is chosen, there is nothing left for a type to *do*.

```text
 one 4-byte word in memory, address 0x1000
┌──────────┬──────────┬──────────┬──────────┐
│ 0xDB     │ 0x0F     │ 0x49     │ 0x40     │   ← the bits never change
└──────────┴──────────┴──────────┴──────────┘
        read through an `int*`                read through a `float*`
              │                                      │
              ▼                                      ▼
        1078530000                              3.14159…

  Which column applies is decided by the declared type of the pointer or
  variable used to read the memory — nothing at that address says which.
```

## In Code

**1 · Same bits, two different types, two different meanings**

```cpp
#include <bit>
#include <cstdint>
#include <iostream>

int main() {
    float f = 3.14159f;
    std::int32_t bits = std::bit_cast<std::int32_t>(f);   // ①
    std::cout << bits << '\n';
    float back = std::bit_cast<float>(bits);              // ②
    std::cout << back << '\n';
}
// expect: 1078530000
// expect: 3.14159
```
1. `std::bit_cast` (C++20) copies the *object representation* of `f` into a same-sized `int32_t`: identical bits, a different type's rules for interpreting them.
2. Casting back recovers the original float exactly — the bits made the round trip untouched; only how they were read changed.

**2 · Operations belong to the type, not to the bits**

```cpp
#include <iostream>

struct Meters {
    double value;
    Meters operator+(Meters other) const { return {value + other.value}; }  // ①
};

int main() {
    Meters a{3.0}, b{4.5};
    Meters c = a + b;                 // ②
    std::cout << c.value << '\n';
}
// expect: 7.5
```
1. `Meters` declares exactly one operation: addition. Nothing about its representation (one `double`) makes multiplication or comparison legal — the type's *declared* operation set does that, and here it's a set of size one.
2. `a + b` compiles because `operator+` exists. The hardware could multiply two doubles just as easily; the compiler refuses to, because `Meters` never said it could. Example 3 shows the refusal.

**3 · The operation set is enforced, even when the hardware could do the work**

```cpp
// cc: ill-formed
struct Meters {
    double value;
    Meters operator+(Meters other) const { return {value + other.value}; }
};

int main() {
    Meters a{3.0}, b{4.5};
    Meters c = a * b;   // error: no match for 'operator*'
}
```
`a` and `b` are, underneath, just two doubles — the CPU has a multiply instruction ready. The compiler rejects the line anyway, because `Meters`'s type never declared `operator*`. This is the operations leg of the triple enforced at compile time, independent of what the representation would physically allow.

## Pitfalls

> [!ub] Reading bits through the wrong type's lens is undefined behavior
> Take Example 1's `float f` and, instead of `std::bit_cast`, write `*reinterpret_cast<std::int32_t*>(&f)`. It compiles without complaint (GCC still warns: *"dereferencing type-punned pointer will break strict-aliasing rules"*), but reading an object through a glvalue whose type is not the object's own type — nor `char`/`unsigned char`/`std::byte` — is undefined behavior (`[expr.reinterpret.cast]`, the *type-accessibility* rule, sometimes called "strict aliasing"). The Standard permits the compiler to assume a `float*` and an `int32_t*` never point at the same bytes, and optimizes on that assumption; on Linux or macOS, `-fsanitize=undefined` reports this as a type-punning violation at the point of the read. The local Windows/MinGW toolchain has no UBSan runtime, so this pitfall is verified only by confirming it compiles and draws the compiler's own strict-aliasing warning, never by an actual sanitizer trap. `std::bit_cast` (or `std::memcpy`) is the defined way to do the same thing — see [[Strict Aliasing and Type Punning]] for the full reproduction and detection table.

> [!trap] Same representation does not mean same type
> `int` and `float` are both 4 bytes on essentially every mainstream platform, and `sizeof` reports the same number for both — but their value sets and operation sets are completely different (compare the *Mechanics* table). `sizeof(a) == sizeof(b)` says nothing about whether `a` and `b` may be compared, assigned, or reinterpreted as one another; only their *types* decide that. See [[Strict Aliasing and Type Punning]] for the general hazard this enables.

## Evolution

See [[Map — Evolution of C++]] for the language-wide timeline.

| Standard | Change | Why |
|---|---|---|
| C / C++98 | The triple exists for built-in types by language definition; `class` and `struct` let a programmer supply the same triple for a new type, including operator overloading | User-defined types needed to be able to fully replace built-in ones in expressions, not just group data |
| C++11 | `auto` and `decltype` let a declaration *name* a type without spelling it | Reduces repetition without changing what a type is — the triple is still fixed once, just inferred rather than written out |
| **C++20** | `std::bit_cast` gives a *defined*, checked way to reinterpret one type's representation as another's (P0476R2) | Removes the need for the `reinterpret_cast`/`union` idiom in Pitfalls, which was always undefined behavior even though compilers rarely miscompiled it |

## Connections

- **Prerequisites:** none — this is the root of [[Map — Types & Values]]; everything else in the domain assumes this vocabulary.
- **Enables:** [[Fundamental Types]] (the built-in vocabulary of values/operations/representations) · [[Classes as User-Defined Types]] (supplying the triple yourself) · [[const and Const-Correctness]] (a compile-time restriction layered on top of a type) · [[Implicit Conversions and Promotions]] (moving a value from one triple to another under a fixed rule).
- **Siblings:** [[The C++ Object Model — What an Object Is]] — an *object* is a region of storage that holds a value *of* a type; this note is about the type side of that pair.
- **Hazards:** [[Strict Aliasing and Type Punning]] (the general form of this note's UB pitfall) · [[Undefined Behavior]] (what "the contract is broken" means language-wide).
- **Domain:** [[Map — Types & Values]].

## Check Yourself

> [!quiz]- What three things does a type fix, and does either "built-in" or "user-defined" change which three?
> The set of legal values, the set of legal operations, and the bit-level representation. Both built-in and user-defined types fix the same three things — they differ only in who supplies the answer: the language definition for `int`, the class declaration for a programmer's own type.

> [!quiz]- Why must type-checking happen entirely at compile time rather than being re-verified while the program runs?
> Because the whole benefit of having a type system is that operations like integer `+` compile down to a single instruction with no runtime check. If every operation had to re-confirm its operands' types while running, that cost would apply to every `+` in every program, defeating the point of a statically typed, zero-overhead language.

> [!quiz]- Predict the output of Example 1 if `f` were `1.0f` instead of `3.14159f`, and explain why `std::bit_cast` is safe where the Pitfalls callout's `reinterpret_cast` is not.
> `1065353216` then `1`. `bit_cast` is a *defined* operation specified to copy the object representation into a value of the target type (given equal size and trivial copyability) — the compiler must make it work correctly. `reinterpret_cast<int32_t*>(&f)` followed by a dereference instead reads through an lvalue of the wrong type, which is exactly what `[expr.reinterpret.cast]`'s type-accessibility rule forbids.

> [!quiz]- `struct Meters { double value; Meters operator+(Meters) const; };` — why does `Meters{1.0} * 2.0` fail to compile, even though a `double` and a `Meters` both ultimately hold one 8-byte floating-point number?
> Because `operator*` was never declared for `Meters`. The representation (a `double`'s worth of bits) says nothing about which operations are legal; only the type's declared operation set does, and here that set contains only `operator+`.

## Sources

- Primer §2.1 "Primitive Built-in Types" (p. 32): opens the chapter by tying a type to the meaning of the operations performed on its values. (p. 33–34): to give meaning to a byte at some address, the reader has to know its type, since the type is what fixes the bit count and the interpretation of those bits; also Table 2.1's minimum-size guarantees.
- Tour §1.4 "Types, Variables, and Arithmetic" (p. 6): the size of a type is implementation-defined and obtained with `sizeof`.
- PPP §8.1 "User-defined types": the representation/operations framing of what a type supplies, and the built-in-vs-user-defined distinction.
- cppreference, *Fundamental types*: `void` as "type with an empty set of values"; `bool` as "capable of holding one of the two values true or false": https://en.cppreference.com/w/cpp/language/types
- cppreference, *reinterpret_cast conversion* §Type aliasing: the type-accessibility rule and the `std::bit_cast`/`std::memcpy` alternative: https://en.cppreference.com/w/cpp/language/reinterpret_cast
- Draft standard `[basic.types.general]` (object/value representation): https://eel.is/c++draft/basic.types.general · `[expr.reinterpret.cast]` (type-accessibility / strict aliasing): https://eel.is/c++draft/expr.reinterpret.cast
- WG21 P0907R4, *Signed Integers are Two's Complement*: https://wg21.link/p0907r4 — mandates the representation leg for signed integers as of C++20.
- WG21 P0476R2, *bit_cast: A type-safe bitwise cast*: https://wg21.link/p0476r2
