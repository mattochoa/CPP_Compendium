---
id: std-string
title: string
aliases:
- "std::string"
type: concept
domain: D10
tier: 1
status: reviewed
standard: C++98
prereqs:
- "[[STL Architecture — Containers, Iterators, Algorithms]]"
related:
- "[[vector]]"
- "[[string_view]]"
- "[[Small String Optimization]]"
- "[[Iterator Invalidation]]"
- "[[C-Style Strings]]"
practice:
- 7
tags:
- type/concept
- domain/d10
- tier/1
- tension/safety-vs-performance
- tension/compatibility-vs-evolution
- std/c++98
- std/c++11
- std/c++17
- std/c++20
- std/c++23
created: 2026-09-27
updated: 2026-09-27
reviewed: 2026-09-27
score: 20
rubric:
  accuracy: 2
  first_principles: 3
  clarity: 3
  depth: 3
  visual: 3
  code: 3
  integration: 3
---

# string

> [!essence]
> **`std::string`** owns a growable, contiguous, null-terminated sequence of `char` and manages that buffer through RAII: the same handle-and-buffer split as [[vector]], specialized to text, plus one guarantee `vector` never needs — a trailing `'\0'` so the buffer can always be handed to a C API.

## The Problem

C already had a way to represent text: a pointer to a contiguous run of `char` that ends wherever a `'\0'` happens to sit. That representation is nothing but a convention layered on top of a raw array, and every program using it has to enforce the convention by hand.

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint.** A C-style string carries no length and no owner. The only way to find its end is to scan for the terminator, and the only way to free its storage is for some piece of code to remember to call the matching `delete[]` or `free`.
> 2. **Consequence.** Every length query is an `O(n)` scan (`strlen`); every copy needs a destination the caller must size correctly by hand (`strcpy`/`strcat` overruns are the textbook C buffer-overflow); and nothing ties the buffer's release to a moment the compiler can see, so ownership is a matter of discipline, not of type.
> 3. **Requirement.** Text needs the same thing every other resource-owning value gets in C++: an object that knows its own size, grows its buffer on demand, and releases it automatically at scope exit — while still producing a null-terminated `char*` on request, because every C API and every existing convention expects one.
> 4. **Design.** `std::basic_string<CharT>` reuses the contiguous-buffer-and-handle model [[Map — Standard Library|the library already uses for `vector`]], and adds the one guarantee `vector` never makes: since C++11, `[data(), data()+size()]` is always a valid range and `data()+size()` always points at a `CharT()` null terminator ([basic.string] general, para. 3). On top of that abstract-machine guarantee, real implementations add the **short-string optimization (SSO)**: a short value is stored inline inside the string object itself, so the common case never touches the heap at all (Tour §10.2.1, p. 127).
> 5. **Price.** SSO means almost every mutating member function must branch on "am I short or long right now" — a cost the assembly in *Under the Hood* makes visible. The "reuse `vector`'s model" design still pays a heap allocation for anything longer than roughly fifteen characters, and the mandatory null terminator is bookkeeping a length-prefixed design (like `string_view`, or Rust's `String`) simply wouldn't carry.

> [!tension] safety ⟷ performance, compatibility ⟷ evolution
> `operator[]` stays unchecked and SSO stays branchy because both trade a small safety or clarity cost for speed that shows up in nearly every program that touches text. At the same time, `std::string` can never stop being a bridge to C's null-terminated convention: `c_str()` has to keep working forever, even as `string_view` (C++17) and `<charconv>` (C++17) quietly build a faster, allocation-free layer beside it rather than replacing it.

## Mental Model

A `std::string` object is a fixed-size handle — on a typical 64-bit implementation, 32 bytes, always the same size no matter how long the text is. What varies is where the characters actually live.

```text
 SHORT ("hi", 2 chars)                LONG (41 chars)
 ┌──────────────────────────┐         ┌──────────────────────────┐
 │ data ●───┐               │         │ data ●──────────┐        │
 │ size = 2 │               │         │ size = 41        │       │
 │ buf: h i \0 . . . . . . .│◀────────┘         (union)  │       │
 │      (15-byte inline buf)│         │ capacity = 41    │       │
 └──────────────────────────┘         └──────────────────┼───────┘
   object IS the storage                                 ▼
   (no heap allocation)                     ┌───────────────────────────┐
                                             │ "this string is...sso\0"  │  heap
                                             └───────────────────────────┘
```

> [!model] The business card with room on the back
> A short string is a business card with a short note written directly on the back — the card *is* the storage, nothing else to manage. A long string is a card that says "see attached," stapled to a separate sheet; the card itself only holds that sheet's location. **Where it breaks:** nothing on the card is a labelled "short/long" flag. In libstdc++ (GCC's library) the object doesn't store a bit that says which mode it's in — it decides by comparing where `data()` points to its own address, every time. (Other libraries choose differently: libc++ does keep a mode bit. The Standard mandates none of this.) *Under the Hood* shows the actual comparison a compiler emits for that question.

## Mechanics

| Situation | Rule | Example |
|---|---|---|
| Contiguity & terminator | Every specialization is a contiguous container; `data()+size()` always points at `CharT()` | `s.data()[s.size()] == '\0'` always holds |
| `operator[]` vs `at()` | `[]` is unchecked — UB past `size()`, except `s[size()]` itself, which is defined and yields `'\0'`; `at()` throws `std::out_of_range` | `s.at(s.size()+1)` throws; `s[s.size()+1]` is UB |
| Construct from `const char*` | Stops at the first `Traits::length` null terminator; an explicit count or iterator range copies exactly that many bytes, embedded nulls included | `std::string("ab\0\0cd")` has size 2; `std::string("ab\0\0cd", 6)` has size 6 |
| Reallocating mutation | Any non-`const` member function *except* `[]`, `at`, `data`, `front`, `back`, and the `begin`/`end` family may invalidate every iterator, pointer and reference into the buffer | a pointer taken before `append()` may dangle right after |
| Comparison | Lexicographic via `char_traits::compare`, case-sensitive; `<=>` since C++20 | `"Apple" < "apple"` (uppercase sorts first in ASCII) |
| Character type | `basic_string<CharT>` is a template; `string`, `wstring`, `u8string`, `u16string`, `u32string` are aliases for different `CharT` | the same member functions work unchanged for `wchar_t` or `char16_t` |

> [!standard] [basic.string] general, and [string.require]
> The draft standard states it plainly: *"A specialization of `basic_string` is a contiguous container"* and *"In all cases, `[data(), data()+size()]` is a valid range, `data()+size()` points at an object with value `charT()` (a 'null terminator'), and `size() <= capacity()` is true."* Before C++11, only `c_str()` — not `data()` — was guaranteed to be null-terminated, and contiguity itself wasn't mandated. `[string.require]` paragraph 4 is the invalidation rule in the table above: it lists exactly which member functions are exempt.

## Under the Hood

> [!machine] The branch SSO buys you (GCC 14.2, `-O2`, x86-64, via Compiler Explorer)
> A function that only asks "is this string long?" compiles to one comparison — the object's data pointer against its own address plus 16:
> ```nasm
> is_long(std::string const&):
>         lea  rax, [rdi+16]        ; ① rax = &object + 16  (where the inline buffer starts)
>         cmp  QWORD PTR [rdi], rax ; ② compare it against the stored data pointer (offset 0)
>         je   .L3                  ; ③ equal → pointing at our own buffer → short → return false
>         cmp  QWORD PTR [rdi+16], 15
>         seta al                   ; ④ long → compare the stored capacity to 15
>         ret
> .L3:
>         xor  eax, eax
>         ret
> ```
> There is no stored "is-short" flag. libstdc++'s object layout is `{ char* data; size_t size; union { size_t capacity; char buf[16]; }; }` — 32 bytes total. "Short or long" is answered by comparing `data` (offset 0) to `&object + 16` (where `buf` starts): equal means the string is pointing at its own inline buffer. That test is exactly what `bufferIsInline` computes in example 1 below, and it is why default-constructed and short strings report `capacity() == 15` — one byte of the 16-byte inline buffer is reserved for the terminator. This 15-character figure is an implementation detail, not a Standard guarantee: cppreference itself annotates it `// unspecified`.

## In Code

**1 · Proving the mental model: is a string's buffer actually inline?**

```cpp
#include <iostream>
#include <string>

bool bufferIsInline(const std::string& s) {
    const auto* objBegin = reinterpret_cast<const unsigned char*>(&s);
    const auto* objEnd   = objBegin + sizeof(s);
    const auto* buf      = reinterpret_cast<const unsigned char*>(s.data());
    return buf >= objBegin && buf < objEnd;                          // ①
}

int main() {
    std::string tiny = "short";                                      // ②
    std::string big  = "this string is definitely longer than sso";  // ③

    std::cout << "tiny: size=" << tiny.size() << " capacity=" << tiny.capacity()
              << " inline=" << std::boolalpha << bufferIsInline(tiny) << '\n';
    std::cout << "big:  size=" << big.size()  << " capacity=" << big.capacity()
              << " inline=" << bufferIsInline(big) << '\n';
}
// expect: tiny: size=5 capacity=15 inline=true
// expect: big:  size=41 capacity=41 inline=false
```
1. `data()` is "inline" exactly when the pointer it returns falls inside the string object's own footprint — no separate allocation exists to point outside of it.
2. Five characters fit inside libstdc++'s 16-byte inline buffer; `tiny` never touches the heap.
3. Forty-one characters do not fit; `big` allocates once and stores a pointer instead of the characters themselves.

**2 · Reallocation invalidates pointers into the old buffer**

```cpp
#include <iostream>
#include <string>

int main() {
    std::string s = "abc";
    const char* p = s.data();     // ① a pointer into the current buffer
    std::cout << *p << '\n';      // ② safe: the buffer hasn't moved yet

    s.append(100, 'x');           // ③ forces reallocation; the old buffer is freed
    std::cout << s.size() << '\n';
    // dereferencing p here would read freed memory — see Pitfalls.  // ④
}
// expect: a
// expect: 103
```
1. Taken before any growth, `p` is valid for now.
2. Reading through it here is fine — nothing has moved yet.
3. `append` growing past capacity reallocates. `[string.require]`/4 names exactly the member functions — `[]`, `at`, `data`, `front`, `back`, and the `begin`/`end` family — that do *not* invalidate; every other non-`const` member function might.
4. This example stops short of the actual UB; see *Pitfalls* for what happens if you don't.

**3 · The null terminator is a guarantee, not a courtesy**

```cpp
#include <cstdio>
#include <string>

int main() {
    std::string s = "hello";
    s[2] = 'L';                        // ① non-const operator[]: mutate in place, no reallocation
    std::printf("%s\n", s.c_str());    // ② c_str(): guaranteed null-terminated, safe for a C API
    std::printf("terminator ok: %d\n", s.data()[s.size()] == '\0');  // ③
}
// expect: heLlo
// expect: terminator ok: 1
```
1. `operator[]` returns a reference into the existing buffer; no growth, no invalidation.
2. `c_str()` has offered this guarantee since C++98; `data()` only started guaranteeing the same thing — and the same non-`const` overload — in C++11/C++17.
3. The check in the Mechanics table isn't hypothetical: the byte right after `size()` really is `'\0'`, on every valid `std::string`, always.

## Pitfalls

> [!trap] A literal with embedded nulls gets silently truncated
> `std::string s = "ab\0\0cd";` calls the `const char*` constructor, which stops at the first `'\0'` — `s.size() == 2`. To keep every byte, pass an explicit count or use the `""s` literal: `std::string s2("ab\0\0cd", 6);` or `auto s3 = "ab\0\0cd"s;` (cppreference, *basic_string* constructor notes). See [[C-Style Strings]].

> [!ub] Short-string slack can hide an out-of-bounds read

```cpp
// cc: ub
#include <string>

int main() {
    std::string s = "abc";      // SSO: capacity 15, only 3 used
    char c1 = s[s.size()];      // ① defined: reads the null terminator
    char c2 = s[s.size() + 1];  // ② UB — but still inside the 15-byte inline buffer
    (void)c1; (void)c2;
}
```
1. `s[3]` is `'\0'` by rule.
2. `s[4]` is one past the terminator and undefined — yet because the inline buffer has slack out to index 14, AddressSanitizer (on Linux/macOS) has nothing to flag: **the sanitizer stays silent**, not because the read is safe, but because it landed inside memory the object already owned. Compare with the next example.

> [!ub] The same mistake on a heap-allocated string is caught

```cpp
// cc: ub
#include <string>

int main() {
    std::string s(100, 'x');    // heap-allocated: capacity == size, no slack
    char c = s[s.size() + 1];   // one past the terminator — now past the allocation too
    (void)c;
}
```
With no SSO slack to hide behind, the identical off-by-one reads past the actual heap allocation, and AddressSanitizer on Linux/macOS reports a `heap-buffer-overflow`. (The Compendium's local MinGW toolchain has no ASan runtime, so both blocks are marked `// cc: ub` and were not observed failing locally; the underlying read is UB regardless of whether any tool catches it.) **The lesson:** passing under a sanitizer is not proof of correctness — it only proves nothing was caught *this run, on this input, in this buffer's current shape*.

> [!trap] `find()` and friends return `npos`, not `-1` or `0`
> `std::string::npos` is `static_cast<size_t>(-1)` — the *largest* possible `size_t`, so `find() > 0` is a bug wherever a match at index 0 is possible. Always compare with `== npos` / `!= npos`. See [[Header — string]] for the full search family.

> [!trap] Growth-triggering mutation invalidates every iterator, pointer and reference
> Holding a `char&` or an iterator across a `push_back`, `append`, `insert`, `resize`, or `reserve` is a live bug waiting for a length that finally crosses the current capacity. See [[Iterator Invalidation]] and [[Dangling Pointers and References]].

## Evolution

See [[Map — Evolution of C++]] for the language-wide timeline.

| Standard | Change | Why |
|---|---|---|
| C++98 | `basic_string<char>` alias; value semantics; no guaranteed contiguity or null-terminated `data()` | text needed an owning, RAII sequence type from day one, replacing raw `char*` handling |
| **C++11** | Move constructor/assignment (`O(1)`, cppreference *Complexity*); contiguous storage and a null-terminated `data()` formally mandated ([basic.string] general); `stoi`/`to_string` and friends | move semantics made returning strings by value cheap; C++11's invalidation and complexity rules also ruled out copy-on-write strings, which pushed the major libraries (libstdc++ from GCC 5) to the SSO-based design described above |
| C++14 | `""s` literal | write a `std::string` literal without spelling out a constructor call |
| **C++17** | [[string_view]]; non-`const` `data()` overload; construct from anything `string_view`-like | pass or slice text without allocating, and mutate through `data()` directly |
| C++20 | `starts_with`/`ends_with`; `<=>` three-way comparison | common prefix/suffix checks without a `find()` + `npos` dance |
| C++23 | `contains()`; `resize_and_overwrite()` | a substring test that reads as a question; fill a buffer without paying for `resize`'s zero-initialization |

## Connections

- **Prerequisites:** [[STL Architecture — Containers, Iterators, Algorithms]] — `string` is the same containers/iterators/algorithms split, specialized to characters.
- **Siblings:** [[vector]] — the identical handle-and-buffer model, minus the null-terminator guarantee and SSO.
- **Enables:** [[string_view]] (a non-owning slice of exactly this buffer) · [[Small String Optimization]] (the mechanism deepened) · [[The Algorithms Library]] (any algorithm over `iterator`s works over a string unchanged).
- **Hazards:** [[Iterator Invalidation]] · [[C-Style Strings]] (embedded nulls, interop) · [[Dangling Pointers and References]].
- **Lookup layer:** [[Header — string]] for the full member reference, task recipes (splitting, joining, trimming, numeric conversion) and detailed performance tables.
- **Domain:** [[Map — Standard Library]].
- **Practice:** *Continuum #7 Word & Text Analyzer* — build a tokenizer and frequency counter over `std::string`, then count which operations allocate (a replaced global `operator new` that increments a counter is enough) and which stay inline.

## Check Yourself

> [!quiz]- What does a `std::string` object store directly, versus what it merely points to?
> In libstdc++ (layouts are implementation-specific): directly, a data pointer, a size, and a 16-byte union that holds either the capacity (long strings) or up to 15 inline characters (short strings) — about 32 bytes total, always. A long string's actual characters live in a separate heap allocation the object only points to; a short string's characters live inside that union, inside the object itself.

> [!quiz]- Why does `s[s.size() + 1]` sometimes pass under AddressSanitizer and sometimes get caught?
> Because the read is undefined behavior either way, but whether it lands inside memory the object still owns depends on slack capacity. A short string has up to 15 bytes of inline buffer beyond a small `size()`, so a small overrun often stays inside that buffer and the sanitizer sees nothing wrong. A heap-allocated string with `capacity() == size()` has no slack, so the identical overrun reads past the actual allocation and AddressSanitizer reports `heap-buffer-overflow`. Passing is never proof the code is correct.

> [!quiz]- Predict: `std::string s = "ab\0\0cd"; std::cout << s.size();` — what does this print, and why?
> `2`. The `const char*` constructor stops at the first `'\0'`, so only `"ab"` is copied. To keep the embedded nulls, pass an explicit length (`std::string(ptr, 6)`) or the `""s` literal.

> [!quiz]- A function holds a `const char* p = s.data();` and later calls `s.reserve(1000);`. Is `p` still valid afterward? Why or why not?
> Not necessarily. `reserve` is a non-`const` member function outside the exempt list (`[]`, `at`, `data`, `front`, `back`, `begin`/`end`), so it may reallocate and invalidate every pointer, iterator, and reference into the old buffer, per `[string.require]`/4 — even though `reserve` only grows capacity and never changes `size()` or the string's value.

## Sources

- Primer §3.2 "Library `string` Type" (pp. 84–86): construction forms, `empty`/`size`, and the whitespace-splitting behavior of `>>` vs `getline`.
- Primer §9.1 "Overview of the Sequential Containers" (p. 326) and §9.4 "How a `vector` Grows" (p. 355): "`string` and `vector` hold their elements in contiguous memory."
- Primer §9.5 "Additional `string` Operations" (pp. 360–365): the `insert`/`erase`/`assign`/`append`/`replace` family, `substr`, and `npos` as `static_cast<size_type>(-1)`.
- Tour §10.2 "Strings" and §10.2.1 "`string` Implementation" (pp. 125–128): concatenation via `+=`, the short-string-optimization memory layout, and why it became ubiquitous (allocation cost under multi-threading).
- Tour §10.3 "String Views" (pp. 128–129): `string_view` as a `(pointer, length)` pair.
- cppreference, *`std::basic_string`*: https://en.cppreference.com/w/cpp/string/basic_string
- cppreference, *`std::basic_string::basic_string`* (constructor notes on embedded-null truncation): https://en.cppreference.com/w/cpp/string/basic_string/basic_string
- Draft standard `[basic.string]` general (contiguity, null-terminator guarantee) and `[string.require]` (invalidation rules): https://eel.is/c++draft/basic.string · https://eel.is/c++draft/string.require
