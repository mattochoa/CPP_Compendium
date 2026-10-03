---
id: hdr-cassert
title: Header — Preprocessor, Assertions and Predefined Macros
aliases:
- <cassert>
- assert
- NDEBUG
- static_assert
- "#error"
- "#warning"
- predefined macros
- __cplusplus
- __FILE__
- __LINE__
- feature-test macros
- preprocessor directives
type: header
domain: HDR
tier: 1
status: draft
standard: C++98
prereqs:
- "[[The Preprocessor]]"
related:
- "[[The Preprocessor]]"
- "[[assert and static_assert]]"
- "[[Headers and Include Guards]]"
- "[[The Compilation Pipeline]]"
- "[[Modules (C++20)]]"
tags:
- type/header
- domain/hdr
- tier/1
- header/cassert
- tension/compile-time-vs-run-time
- tension/compatibility-vs-evolution
created: 2026-10-03
updated: 2026-10-03
header: <cassert>
---

# Header — Preprocessor, Assertions and Predefined Macros

> [!essence]
> The **preprocessor** edits your source text before the compiler sees it: it pastes in headers, replaces macros, and keeps or drops blocks of code. It also hosts the first of C++'s **three assertion layers**. `#error` stops the build while preprocessing, `static_assert` stops it while compiling, and `assert` from **`<cassert>`** stops the program while it runs. Each layer can ask the toolchain questions through **predefined macros** such as `__cplusplus`, `__FILE__` and `__LINE__`.

> [!standard] Versions
> - **C++98**: directives, `#` and `##`, `#error`, `assert` + `NDEBUG`, `__cplusplus`, `__FILE__`, `__LINE__`
> - **C++11**: `static_assert`, `__VA_ARGS__`, `_Pragma`, `__func__`, `__STDC_HOSTED__`
> - **C++17**: `static_assert` without a message, `__has_include`
> - **C++20**: `__VA_OPT__`, `__has_cpp_attribute`, standard feature-test macros, `<version>`, `std::source_location`
> - **C++23**: `#elifdef`, `#elifndef`, `#warning`
> - **C++26**: `#embed`, `__has_embed`, variadic `assert(...)`, contract assertions

## The Three Assertion Layers

```text
  source files
       │
       ▼
  ┌─────────────────────────┐
  │ 1  PREPROCESSING        │  sees: macros only
  │    (translation phase 4)│  #error "msg"     stops the build
  │                         │  #warning "msg"   warns (C++23)
  └────────────┬────────────┘
               ▼
  ┌─────────────────────────┐
  │ 2  COMPILATION          │  sees: types, sizeof, constexpr values
  │                         │  static_assert(cond, "msg")   stops the build
  └────────────┬────────────┘
               ▼
  ┌─────────────────────────┐
  │ 3  RUN TIME             │  sees: real values
  │                         │  assert(cond)   prints, then std::abort()
  │                         │  removed when NDEBUG is defined
  └─────────────────────────┘
```

**Rule:** check every fact at the earliest layer that can see it.

## Quick Reference

### DIRECTIVES — Directive | Effect | Note

```cpp
// cc: fragment
// ═══════════════════════════════════════════════════════════════════════════
// INCLUDING
// ═══════════════════════════════════════════════════════════════════════════
#include <vector>                 // system | Paste a library header  | System paths
#include "config.h"               // local  | Paste your own header   | This folder first
#pragma once                      // guard  | Include file only once  | Non-standard
#ifndef CONFIG_H / #define ...    // guard  | Portable include guard  | Wraps the file
#embed "logo.png"                 // bytes  | File bytes as int list  | C++26

// ═══════════════════════════════════════════════════════════════════════════
// DEFINING MACROS
// ═══════════════════════════════════════════════════════════════════════════
#define PI 3.14159                // object | Token replacement       | Prefer constexpr
#define SQ(x) ((x) * (x))         // func   | Replacement with args   | Parenthesize all
#define STR(x) #x                 // #      | Argument → "string"     | STR(a+b) → "a+b"
#define CAT(a, b) a##b            // ##     | Paste two tokens        | CAT(v, 1) → v1
#define F(...) g(__VA_ARGS__)     // ...    | Variadic macro          | C++11
__VA_OPT__(,)                     // opt    | Comma only if args      | C++20
#define S(x) do { x; } while (0)  // stmt   | Acts as one statement   | Safe after `if`
#undef PI                         // remove | Forget a macro          | No scope

// ═══════════════════════════════════════════════════════════════════════════
// CONDITIONAL COMPILATION
// ═══════════════════════════════════════════════════════════════════════════
#if EXPR                          // test   | Keep block if EXPR != 0 | Unknown name = 0
#elif EXPR / #else / #endif       // chain  | Alternatives
#ifdef NAME / #ifndef NAME        // test   | Is NAME defined?        | #if defined(NAME)
#elifdef NAME / #elifndef NAME    // chain  | Defined-test in a chain | C++23
__has_include(<optional>)         // test   | Does the header exist?  | C++17
__has_cpp_attribute(nodiscard)    // test   | Attribute supported?    | C++20
__has_embed("logo.png")           // test   | Resource exists?        | C++26

// ═══════════════════════════════════════════════════════════════════════════
// DIAGNOSTICS, PRAGMAS, LINE CONTROL
// ═══════════════════════════════════════════════════════════════════════════
#error "needs C++17"              // stop   | Build fails with text   | Layer 1
#warning "deprecated"             // warn   | Build continues         | C++23
#pragma message("note")           // note   | Print during build      | GCC, Clang, MSVC
#pragma GCC diagnostic push       // GCC    | Save warning settings   | Also Clang
#pragma warning(push)             // MSVC   | Save warning settings   | MSVC
_Pragma("GCC diagnostic pop")     // op     | #pragma inside a macro  | C++11
#line 100 "gen.cpp"               // line   | Reset __LINE__/__FILE__ | Code generators
#                                 // null   | Does nothing
```

### ASSERTIONS — Expression | Layer | Note

```cpp
// cc: fragment
// ═══════════════════════════════════════════════════════════════════════════
// COMPILE TIME (layer 2)
// ═══════════════════════════════════════════════════════════════════════════
static_assert(cond, "msg")        // build  | Fails if cond is false  | C++11
static_assert(cond)               // build  | Same, no message        | C++17

// ═══════════════════════════════════════════════════════════════════════════
// RUN TIME (layer 3) — <cassert>
// ═══════════════════════════════════════════════════════════════════════════
#include <cassert>                // setup  | Defines assert          | Reads NDEBUG here
assert(i < n)                     // run    | False → message, abort  | Prints expr+line
assert(p && "p is set")           // run    | Adds a message          | Literal is true
assert((same_v<A, B>))            // run    | Extra parens for commas | Fixed in C++26
#define NDEBUG                    // off    | Every assert → nothing  | Before #include
contract_assert(x > 0)            // run    | Contract assertion      | C++26
```

### TOOLS — Command | Shows

```text
g++ -E main.cpp                   preprocessed output (what the compiler actually sees)
g++ -dM -E -x c++ /dev/null       every predefined macro (GCC/Clang; about 460 on GCC 13)
cl /P main.cpp                    MSVC: writes the preprocessed file main.i
```

## Predefined Macros

### `__cplusplus` by Standard

| Standard | Value |
|---|---|
| C++98 / C++03 | `199711L` |
| C++11 | `201103L` |
| C++14 | `201402L` |
| C++17 | `201703L` |
| C++20 | `202002L` |
| C++23 | `202302L` |
| C++26 | `202603L` |

Pre-release modes report interim values (GCC 13 with `-std=c++23` gives `202100L`). **MSVC** reports `199711L` for every standard unless you compile with `/Zc:__cplusplus`; its true value is in `_MSVC_LANG`.

### Standard Macros

| Macro | Value | Since |
|---|---|---|
| `__FILE__` | Current file name | C++98 |
| `__LINE__` | Current line number | C++98 |
| `__DATE__` | Build date, `"Oct  3 2026"` | C++98 |
| `__TIME__` | Build time, `"17:04:47"` | C++98 |
| `__STDC_HOSTED__` | `1` full library, `0` freestanding | C++11 |
| `__STDCPP_THREADS__` | `1` if threads are possible | C++11 |
| `__STDCPP_DEFAULT_NEW_ALIGNMENT__` | `new`'s alignment (16 on x86-64) | C++17 |
| `__STDCPP_FLOAT16_T__` etc. | `1` if `std::float16_t` etc. exist | C++23 |
| `__STDC_EMBED_FOUND__` etc. | Results of `__has_embed` | C++26 |

Optional, implementation-defined: `__STDC__`, `__STDC_VERSION__`, `__STDC_ISO_10646__`, `__STDC_MB_MIGHT_NEQ_WC__`. Removed in C++23: `__STDCPP_STRICT_POINTER_SAFETY__`.

**Not macros, used the same way:** `__func__` (C++11) holds the current function's name. `std::source_location::current()` (C++20) bundles file, line, column and function into an object.

### Feature-Test Macros

| Macro | Tests for | Where |
|---|---|---|
| `__cpp_constexpr` | `constexpr` level | Predefined |
| `__cpp_concepts` | Concepts | Predefined |
| `__cpp_modules` | Modules | Predefined |
| `__cpp_lib_optional` | `std::optional` | `<version>` |
| `__cpp_lib_format` | `std::format` | `<version>` |
| `__cpp_lib_ranges` | Ranges | `<version>` |

Each value is the date the feature was adopted, for example `201606L`. Library macros come from any standard header, most reliably `<version>` (C++20).

### Compiler, Platform and Build Macros

| Macro | Defined by | Note |
|---|---|---|
| `__clang__` | Clang | Check before `__GNUC__` |
| `__GNUC__` | GCC **and** Clang | Clang claims GCC 4.2 |
| `_MSC_VER` | MSVC | `1940` = VS 2022 17.10 |
| `_MSVC_LANG` | MSVC | Real C++ standard |
| `_WIN32` | Windows | Also on 64-bit |
| `_WIN64` | 64-bit Windows | |
| `__linux__` | Linux | |
| `__APPLE__` | macOS, iOS | |
| `__x86_64__` / `_M_X64` | x86-64 | GCC/Clang / MSVC |
| `__aarch64__` / `_M_ARM64` | ARM64 | GCC/Clang / MSVC |
| `NDEBUG` | Release builds | Read by `<cassert>` |
| `_DEBUG` | MSVC debug runtime | MSVC only |
| `__OPTIMIZE__` | `-O1` and higher | GCC/Clang |
| `__PRETTY_FUNCTION__` | GCC/Clang | Full signature |
| `__FUNCSIG__` | MSVC | Full signature |
| `__COUNTER__` | GCC, Clang, MSVC | +1 on each use |

## Patterns

### Ask the Toolchain What It Is (C++11)
```cpp
#include <iostream>

int main() {
#if defined(__clang__)
    const char* compiler = "Clang";
#elif defined(__GNUC__)
    const char* compiler = "GCC";
#elif defined(_MSC_VER)
    const char* compiler = "MSVC";
#else
    const char* compiler = "unknown";
#endif

#if defined(_MSVC_LANG)
    long standard = _MSVC_LANG;           // MSVC's real value
#else
    long standard = __cplusplus;
#endif

    std::cout << compiler << ", " << standard << '\n';
    std::cout << (standard >= 201703L ? "C++17 or newer" : "older") << '\n';
}
// expect: C++17 or newer
```
Test `__clang__` first, because Clang also defines `__GNUC__`.

### Stop the Build Early: `#error` and `static_assert` (C++17)
```cpp
#include <climits>
#include <cstdint>
#include <type_traits>

#if __cplusplus < 201703L && !defined(_MSVC_LANG)
#error "This code needs C++17 or newer"
#endif

static_assert(CHAR_BIT == 8, "bytes must be 8 bits");
static_assert(sizeof(std::int32_t) == 4);          // C++17: no message

template <typename T>
T average(T a, T b) {
    static_assert(std::is_arithmetic<T>::value, "average() needs a number");
    return (a + b) / 2;
}

int main() { return average(4, 6) == 5 ? 0 : 1; }
```
`#error` sees only macros. `static_assert` sees types and constants. Inside a template it runs once per type and prints your message instead of a long template error.

### The Build Stopped by `#error`
```cpp
// cc: ill-formed
#define CONFIG_MAX_USERS 0

#if CONFIG_MAX_USERS <= 0
#error "CONFIG_MAX_USERS must be positive"
#endif

int main() {}
```

### `assert`: Checks That Vanish in Release Builds
```cpp
#include <cassert>
#include <iostream>
#include <vector>

double mean(const std::vector<double>& v) {
    assert(!v.empty() && "mean() of an empty vector");
    double s = 0;
    for (double x : v) s += x;
    return s / static_cast<double>(v.size());
}

int main() {
    std::cout << mean({2, 4, 9}) << '\n';
    // mean({});  → Assertion `!v.empty() && "mean() of an empty vector"' failed.
}
// expect: 5
```
A failed `assert` prints the expression, file, line and function, then calls `std::abort()`. Never put side effects inside it (`assert(++n < 10)`): release builds delete the whole expression.

### `NDEBUG` Is Read at Each `#include <cassert>`
```cpp
#define NDEBUG                 // ① before the include
#include <cassert>
#include <iostream>

int main() {
    assert(1 + 1 == 3);        // ② becomes ((void)0)
    std::cout << "still running\n";
}
// expect: still running
```
1. Release configurations pass `-DNDEBUG`, as CMake's `Release` and Visual Studio's Release do.
2. The expression is not even evaluated.

### A Better Assert Macro
```cpp
#include <cstdio>

#define CHECK(cond, msg)                                         \
    do {                                                         \
        if (!(cond))                                             \
            std::fprintf(stderr, "CHECK failed: %s (%s) %s:%d\n", \
                         #cond, msg, __FILE__, __LINE__);        \
    } while (0)

int main() {
    int stock = -2;
    if (stock < 0) CHECK(stock >= 0, "stock went negative");
    std::puts("done");
}
// expect: done
```
- `#cond` turns the condition into text.
- `__FILE__` and `__LINE__` expand where `CHECK` is used, which only a macro can do.
- `do { } while (0)` makes the macro a single statement, safe after an `if` without braces.
- Unlike `assert`, it stays on in release builds.

### Feature Detection Instead of Version Numbers (C++17)
```cpp
#include <iostream>
#if __has_include(<version>)
#include <version>
#endif

#if defined(__cpp_lib_optional)
#include <optional>
const char* backend = "std::optional";
#else
const char* backend = "fallback";
#endif

int main() { std::cout << "using " << backend << '\n'; }
// expect: using std::optional
```
Testing the exact feature beats testing `__cplusplus`: compilers ship library features at different times.

### Stringize and Token-Paste: the Two-Level Trick
```cpp
#include <iostream>

#define VERSION 3
#define STR_RAW(x) #x
#define STR(x) STR_RAW(x)          // expand first, then stringize
#define CAT_RAW(a, b) a##b
#define CAT(a, b) CAT_RAW(a, b)

int CAT(counter_, VERSION) = 7;    // int counter_3 = 7;

int main() {
    std::cout << STR_RAW(VERSION) << ' ' << STR(VERSION) << ' ' << counter_3 << '\n';
}
// expect: VERSION 3 7
```
`#` and `##` use the argument exactly as written. One extra macro level expands it first.

### X-Macros: One List, Several Expansions
```cpp
#include <iostream>

#define COLOR_LIST(X) X(Red) X(Green) X(Blue)

enum class Color {
#define AS_ENUM(name) name,
    COLOR_LIST(AS_ENUM)
#undef AS_ENUM
};

const char* to_string(Color c) {
    switch (c) {
#define AS_CASE(name) case Color::name: return #name;
        COLOR_LIST(AS_CASE)
#undef AS_CASE
    }
    return "?";
}

int main() { std::cout << to_string(Color::Green) << '\n'; }
// expect: Green
```
The enum and its names come from one list, so they can never drift apart.

### Variadic Logging with `__VA_OPT__` (C++20)
```cpp
// cc: std=c++20
#include <cstdio>

#define LOG(fmt, ...) std::printf("[log] " fmt "\n" __VA_OPT__(,) __VA_ARGS__)

int main() {
    LOG("starting");               // no extra args: no comma
    LOG("disk at %d%%", 91);       // extra args: comma added
}
// expect: [log] disk at 91%
```

### `#elifdef` and `#warning` (C++23)
```cpp
// cc: std=c++23
#include <iostream>

#define USE_FAST_PATH

#ifdef USE_SAFE_PATH
const char* path = "safe";
#elifdef USE_FAST_PATH
const char* path = "fast";
#else
#warning "no path selected"
const char* path = "default";
#endif

int main() { std::cout << path << '\n'; }
// expect: fast
```

## Key Concepts

### Macros Are Text, Not C++
The preprocessor runs before types, scopes and namespaces exist. A macro named `max` replaces every later `max`, including `std::max`; that's why Windows code defines `NOMINMAX`. Name macros in `ALL_CAPS` so they can't collide with ordinary names ([[The Preprocessor]]).

### Function-Like Macros Copy Their Arguments
`SQ(i++)` becomes `((i++) * (i++))`, which is undefined behaviour. `SQ(a + 1)` without the inner parentheses becomes `a + 1 * a + 1`. Prefer `constexpr` functions and templates. Keep macros for what only the preprocessor can do: `#` stringizing, `__FILE__`/`__LINE__` at the call site, conditional compilation, include guards.

### Choosing the Assertion Layer

| Layer | Tool | Sees | Use for |
|---|---|---|---|
| 1 · Preprocessing | `#error`, `#warning` | Macros | Wrong standard, platform, config |
| 2 · Compilation | `static_assert` | Types, constants | Sizes, traits, template rules |
| 3 · Run time | `assert`, `contract_assert` | Real values | Preconditions, invariants |

### `assert` Is for Bugs, Not Errors
An assertion means "if this is false, the program is wrong". A missing file or bad user input is not a bug, so handle it with real error handling that also runs in release builds ([[Exceptions]], [[Error Handling Strategies Compared]]).

### `assert` and Commas
Before C++26, `assert` takes one macro argument, so a top-level comma splits it: `assert(std::is_same_v<int, int>)` fails to compile. Add parentheses: `assert((std::is_same_v<int, int>))`.

### Keep `NDEBUG` the Same Everywhere
An `inline` function containing `assert`, compiled with `NDEBUG` in one file and without it in another, has two different definitions. That breaks the [[The One Definition Rule|One Definition Rule]]. Set `NDEBUG` per build configuration on the command line, never per file.

### Detect Features, Not Versions
A compiler can claim C++20 while missing parts of its library, and MSVC reports `199711L` by default. Test the exact feature (`__cpp_lib_format`, `__has_include(<format>)`) with `<version>` included.

### GCC's Obsolete `#assert`
GCC once had "preprocessor assertions": `#assert machine(x86)`, tested with `#if #machine(x86)`. They are deprecated and non-standard, and unrelated to `assert`. Use `#if defined(...)`.

## Choosing a Tool

```text
Need                                         Use
───────────────────────────────────────────────────────────────────────────
Refuse the wrong standard/platform/config    #if ... #error "why" #endif
Warn but keep building                       #warning (C++23) / #pragma message
Check a size, trait or constexpr value       static_assert(cond, "why")
Restrict a template's types                  C++20 concepts, else static_assert
Check a precondition while developing        assert(cond && "why")
Check something in release builds too        your own CHECK macro, or an error
Report file/line from a helper function      std::source_location (C++20)
Detect a feature                             <version> + __cpp_lib_* / __has_include
Detect compiler / OS / CPU                   __clang__ _MSC_VER _WIN32 __linux__
A named constant                             constexpr variable
A small computation                          constexpr / inline function
Matching enum + name table                   X-macro
Include a header once                        #pragma once or an include guard
```

## Best Practices

1. **Check at the earliest layer** that can see the fact: `#error`, then `static_assert`, then `assert`
2. **Give every assertion a message**
3. **Never put side effects inside `assert`**
4. **Set `NDEBUG` per build configuration**, never per file
5. **Prefer `constexpr` and templates to macros**
6. **Parenthesize macro parameters and bodies**; wrap statement macros in `do { } while (0)`
7. **Name macros in `ALL_CAPS`**, and `#undef` helper macros after use
8. **Detect features, not versions**
9. **On MSVC, use `/Zc:__cplusplus`** and `/Zc:preprocessor`
10. **Read `g++ -E` output** when a macro misbehaves

## Related Headers

```cpp
// cc: std=c++23
#include <cassert>          // assert; reads NDEBUG where included
#include <version>          // C++20: all __cpp_lib_* macros
#include <source_location>  // C++20: file, line, function without macros
#include <stacktrace>       // C++23: call stacks for failure reports
#include <type_traits>      // traits used in static_assert
#include <climits>          // CHAR_BIT, INT_MAX ...
#include <cstdint>          // INT32_MAX, UINT64_C(...)
#include <cstdlib>          // std::abort, EXIT_SUCCESS
```

## Connections

- **Hub:** [[Map — Standard Headers]]
- **Concepts:** [[The Preprocessor]] · [[assert and static_assert]] · [[Headers and Include Guards]] · [[The Compilation Pipeline]] · [[Translation Units]] · [[Modules (C++20)]] · [[Concepts and Constraints]]
- **Hazards:** [[Undefined Behavior]] · [[The One Definition Rule]]
- **Error handling:** [[Exceptions]] · [[Error Handling Strategies Compared]]
- **Sibling cards:** [[Header — Modern IO]] · [[Header — cstdio]]
- **Practice:** *Continuum #1 Hello, Compiler* (print the compiler and standard, dump the macros with `g++ -dM -E`) · *#6 Function Library & Header Refactor* (include guards, `static_assert`, `assert`, then build with `-DNDEBUG`)

## Sources

- Primer §2.6.3 "Writing Our Own Header Files" (p. 76): the preprocessor, preprocessor variables, header guards.
- Primer §6.5.3 "Aids for Debugging" (p. 240): `assert` and `NDEBUG` (p. 241), `__func__`, `__FILE__`, `__LINE__`, `__TIME__`, `__DATE__`.
- Tour §4.5 "Assertions" (p. 48): `assert`, `static_assert`, compile time versus run time.
- Tour §19.2 "C++ Feature Evolution" (p. 263): which standard added which facility.
- cppreference / web, *Preprocessor*, *Replacing text macros*, *Conditional inclusion*, *Feature testing*, *assert*, *static_assert*: https://en.cppreference.com/w/cpp/preprocessor · https://en.cppreference.com/w/cpp/preprocessor/replace · https://en.cppreference.com/w/cpp/feature_test · https://en.cppreference.com/w/cpp/error/assert · https://en.cppreference.com/w/cpp/language/static_assert
- GCC manual, *The C Preprocessor* ("Predefined Macros", "Obsolete Features"): https://gcc.gnu.org/onlinedocs/cpp/
- Microsoft Learn, *Predefined macros* and `/Zc:__cplusplus`: https://learn.microsoft.com/en-us/cpp/preprocessor/predefined-macros
- C++ Core Guidelines ES.30, ES.31, ES.32 (macros), I.6 (preconditions), P.5, P.7 (check early): https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
