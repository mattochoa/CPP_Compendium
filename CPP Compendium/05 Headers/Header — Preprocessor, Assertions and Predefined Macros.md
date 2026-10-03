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
> The **preprocessor** rewrites your source text before the compiler sees it: it pastes in headers, replaces macros, and keeps or deletes blocks of code depending on conditions. It also gives you the earliest of C++'s three **assertion layers**: `#error`/`#warning` stop or warn *while preprocessing*, `static_assert` stops *while compiling*, and `assert` (from **`<cassert>`**) stops *while running*. Every layer can ask the toolchain questions through **predefined macros** (`__cplusplus`, `__FILE__`, `__LINE__`, feature-test macros, compiler and platform macros), which is how one source file adapts to many compilers, standards and operating systems.

> [!standard] Versions
> C++98 (`#include`, `#define`, `#if`/`#ifdef`/`#elif`, `#`/`##`, `#error`, `#pragma`, `#line`, `assert`/`NDEBUG`, `__cplusplus`/`__FILE__`/`__LINE__`/`__DATE__`/`__TIME__`) / C++11 (`static_assert`, variadic macros `__VA_ARGS__`, `_Pragma`, `__func__`, `__STDC_HOSTED__`, `__STDCPP_THREADS__`) / C++17 (`static_assert` without a message, `__has_include`, `__STDCPP_DEFAULT_NEW_ALIGNMENT__`) / C++20 (`__VA_OPT__`, `__has_cpp_attribute`, feature-test macros standardized, `<version>`, `std::source_location`, `module`/`import` directives) / C++23 (`#elifdef`, `#elifndef`, `#warning`, `__STDCPP_FLOAT16_T__` and the other extended floating-point macros; `__STDCPP_STRICT_POINTER_SAFETY__` removed) / C++26 (`#embed`, `__has_embed`, variadic `assert(...)`, contract assertions `pre`/`post`/`contract_assert`)

## Class Hierarchy / Family

**Where the preprocessor runs, and the three layers of assertion.**

```text
  your .cpp + headers
         │
         ▼
  ┌──────────────────────────────┐   #include #define #if #ifdef #elif #else #endif
  │ TRANSLATION PHASE 4:         │   #  ##  __VA_ARGS__  __VA_OPT__   predefined macros
  │ PREPROCESSING  (text/tokens) │   ── ASSERT LAYER 1 ──▶ #error "msg"  stops the build
  │                              │                         #warning "msg" (C++23) warns
  └──────────────┬───────────────┘
                 │ one expanded "translation unit"  (see it with:  g++ -E file.cpp)
                 ▼
  ┌──────────────────────────────┐   types, templates, constexpr, overloads
  │ PHASES 5-7: COMPILATION      │   ── ASSERT LAYER 2 ──▶ static_assert(cond, "msg")
  │ (types and constants known)  │                         stops the build
  └──────────────┬───────────────┘
                 │ object files → linker → program
                 ▼
  ┌──────────────────────────────┐   real input, real data
  │ RUN TIME                     │   ── ASSERT LAYER 3 ──▶ assert(cond)  (<cassert>)
  │                              │                         prints + std::abort(); gone if NDEBUG
  └──────────────────────────────┘                         C++26: contract_assert / pre / post
```

Rule: **check each fact at the earliest layer that can see it.** `#error` sees only macros (the standard, the platform, configuration flags). `static_assert` sees types and constants (`sizeof`, traits, `constexpr` values). `assert` sees run-time values (function arguments, loop state).

## Quick Reference

```cpp
// cc: fragment
// ═══════════════════════════════════════════════════════════════════════════
// INCLUDING
// ═══════════════════════════════════════════════════════════════════════════
#include <vector>                       // <…> searches the system/library include paths
#include "config.h"                     // "…" searches next to the current file first, then like <…>
#if __has_include(<optional>)           // C++17: does this header exist?
#pragma once                            // non-standard but universal: include this file only once
#ifndef APP_CONFIG_H                    // the portable include guard...
#define APP_CONFIG_H                    //   ...wrapping the whole header
#endif
#embed "logo.png"                       // C++26: a file's bytes as a comma-separated list of ints

// ═══════════════════════════════════════════════════════════════════════════
// MACROS
// ═══════════════════════════════════════════════════════════════════════════
#define PI 3.14159                      // object-like: plain token replacement
#define SQUARE(x) ((x) * (x))           // function-like: parenthesize every use AND the whole body
#define STR(x)  #x                      // # stringizes the argument: STR(a+b) → "a+b"
#define CAT(a, b) a##b                  // ## pastes tokens: CAT(var, 1) → var1
#define LOG(fmt, ...) printf(fmt __VA_OPT__(,) __VA_ARGS__)   // ... + __VA_ARGS__ (C++11), __VA_OPT__ (C++20)
#define DO_TWICE(s) do { s; s; } while (0)   // statement macro: safe after if without braces
#undef PI                               // forget a macro
//   macros have NO scope, NO types, NO namespaces: they apply from #define to #undef / end of TU

// ═══════════════════════════════════════════════════════════════════════════
// CONDITIONAL COMPILATION
// ═══════════════════════════════════════════════════════════════════════════
#if EXPR  /  #elif EXPR  /  #else  /  #endif   // EXPR: integer constant expression of macros
#ifdef NAME   /  #ifndef NAME                  // same as #if defined(NAME) / #if !defined(NAME)
#elifdef NAME /  #elifndef NAME                // C++23
#if defined(_WIN32) && !defined(NDEBUG)        // undefined identifiers in #if evaluate to 0
#if __has_cpp_attribute(nodiscard)             // C++20: attribute support (value = version date)
#if __has_embed("logo.png")                    // C++26

// ═══════════════════════════════════════════════════════════════════════════
// ASSERTIONS & DIAGNOSTICS (earliest layer first)
// ═══════════════════════════════════════════════════════════════════════════
#error "This library needs C++17"       // preprocessing: stop the build with a message
#warning "deprecated config"            // C++23 (long-standing GCC/Clang extension): warn, keep going
static_assert(sizeof(int) == 4, "need 32-bit int");   // C++11: compile time, needs a constant
static_assert(sizeof(void*) == 8);                     // C++17: message optional
#include <cassert>                      // brings in assert, reading NDEBUG at THIS point
assert(index < size);                   // run time: if false → prints expr, file, line, function; abort()
assert(ptr && "ptr must not be null");  // idiom: && "message" puts text in the diagnostic
#define NDEBUG                          // before including <cassert>: every assert becomes ((void)0)
contract_assert(x > 0);                 // C++26 contract assertion (also pre(...) / post(...) on functions)

// ═══════════════════════════════════════════════════════════════════════════
// PRAGMAS, LINE CONTROL, NULL DIRECTIVE
// ═══════════════════════════════════════════════════════════════════════════
#pragma GCC diagnostic push / ignored "-Wunused" / pop     // GCC & Clang
#pragma warning(push) / warning(disable: 4996) / pop       // MSVC
#pragma message("building debug")       // print a note during compilation (GCC, Clang, MSVC)
_Pragma("GCC diagnostic ignored \"-Wunused\"")   // C++11: a pragma as an operator, usable INSIDE macros
#line 100 "generated.cpp"               // set __LINE__ / __FILE__ (used by code generators)
#                                       // null directive: does nothing

// ═══════════════════════════════════════════════════════════════════════════
// SEE WHAT THE PREPROCESSOR DID
// ═══════════════════════════════════════════════════════════════════════════
//   g++ -E main.cpp                  full preprocessed output
//   g++ -dM -E -x c++ /dev/null      every predefined macro (GCC/Clang; ~460 on GCC 13)
//   cl /P main.cpp                   MSVC: writes main.i
```

## Predefined Macros

**Standard macros** (defined by every conforming implementation):

| Macro | Value | Since |
|---|---|---|
| `__cplusplus` | `199711L` C++98/03 · `201103L` C++11 · `201402L` C++14 · `201703L` C++17 · `202002L` C++20 · `202302L` C++23 · `202603L` C++26 (per cppreference); pre-release modes report interim values, e.g. GCC 13 `-std=c++23` gives `202100L` | C++98 |
| `__FILE__` | Current source file name, a string literal (changes inside headers) | C++98 |
| `__LINE__` | Current line number, an integer constant | C++98 |
| `__DATE__` | Compilation date, `"Mmm dd yyyy"` (e.g. `"Oct  3 2026"`) | C++98 |
| `__TIME__` | Compilation time, `"hh:mm:ss"` | C++98 |
| `__STDC_HOSTED__` | `1` hosted (full library), `0` freestanding (embedded, kernels) | C++11 |
| `__STDCPP_DEFAULT_NEW_ALIGNMENT__` | Alignment `operator new` guarantees, a `std::size_t` literal (16 on x86-64 GCC) | C++17 |
| `__STDCPP_FLOAT16_T__` `__STDCPP_FLOAT32_T__` `__STDCPP_FLOAT64_T__` `__STDCPP_FLOAT128_T__` `__STDCPP_BFLOAT16_T__` | `1` if `std::float16_t` etc. exist (`<stdfloat>`) | C++23 |
| `__STDC_EMBED_NOT_FOUND__` / `__STDC_EMBED_FOUND__` / `__STDC_EMBED_EMPTY__` | `0` / `1` / `2`: results of `__has_embed` | C++26 |

**Standard but implementation-defined** (present only if the implementation chooses):

| Macro | Meaning | Since |
|---|---|---|
| `__STDC__` | C conformance indicator (GCC defines it as `1` even in C++) | C++98 |
| `__STDC_VERSION__` | C standard version, if any | C++11 |
| `__STDC_ISO_10646__` | `wchar_t` holds Unicode code points (`yyyymmL`) | C++11 |
| `__STDC_MB_MIGHT_NEQ_WC__` | `1` if `'x' == L'x'` might be false (EBCDIC systems) | C++11 |
| `__STDCPP_THREADS__` | `1` if the program can have more than one thread | C++11 |
| `__STDCPP_STRICT_POINTER_SAFETY__` | Garbage-collection support flag | C++11, **removed C++23** |

**Not macros, but used the same way:** `__func__` (C++11) is a function-local `static const char[]` holding the function's name. `std::source_location::current()` (C++20, `<source_location>`) packages file, line, column and function name as an object you can pass to a logging function as a default argument, with no macro needed ([[Header — Modern IO]]).

**Feature-test macros** (C++20 made them standard; compilers had them earlier). *Language* macros `__cpp_*` are predefined; *library* macros `__cpp_lib_*` come from any standard header, most reliably `<version>` (C++20):

| Macro (examples) | Tests for | Example value |
|---|---|---|
| `__cpp_constexpr` | `constexpr` capabilities | `201603L` (C++17 constexpr lambdas) |
| `__cpp_concepts` | Concepts | `202002L` |
| `__cpp_modules` | Modules | `201907L` |
| `__cpp_lib_optional` | `std::optional` | `201606L` |
| `__cpp_lib_format` | `std::format` | `201907L` (GCC 13) |
| `__cpp_lib_ranges` | Ranges library | `202110L` (value grows as the feature is extended) |
| `__has_include(<h>)` / `__has_cpp_attribute(a)` | Header present / attribute supported | `1` / date value |

**Compiler, platform and build macros** (not standard, but universal in practice):

| Macro | Defined when | Note |
|---|---|---|
| `__GNUC__` `__GNUC_MINOR__` | GCC **and Clang** (Clang pretends to be GCC 4.2) | Check `__clang__` first |
| `__clang__` `__clang_major__` | Clang | Also defined by Apple Clang |
| `_MSC_VER` | MSVC (e.g. `1940` for VS 2022 17.10) | `_MSC_FULL_VER` for build number |
| `_MSVC_LANG` | MSVC: the *real* standard value | MSVC's `__cplusplus` stays `199711L` unless you compile with **`/Zc:__cplusplus`** |
| `_WIN32` / `_WIN64` | Windows (`_WIN32` also on 64-bit) | |
| `__linux__` · `__APPLE__` (+ `TARGET_OS_*`) · `__unix__` · `__ANDROID__` | Operating system | |
| `__x86_64__` / `_M_X64` · `__aarch64__` / `_M_ARM64` | CPU architecture (GCC/Clang / MSVC spelling) | |
| `__BYTE_ORDER__` (GCC/Clang) | Endianness | C++20: `std::endian` in `<bit>` instead |
| `NDEBUG` | Release builds (CMake Release, `-DNDEBUG`, VS Release) | The only macro `<cassert>` looks at |
| `_DEBUG` | MSVC debug runtime (`/MDd`, `/MTd`) | MSVC only |
| `__OPTIMIZE__` | GCC/Clang with `-O1` or higher | |
| `__PRETTY_FUNCTION__` (GCC/Clang) · `__FUNCSIG__` (MSVC) · `__FUNCTION__` | Full signature / name of the current function | Extensions; prefer `__func__` or `source_location` |
| `__COUNTER__` | Increments on each use (unique names) | Extension (GCC, Clang, MSVC) |
| `__INCLUDE_LEVEL__` · `__BASE_FILE__` · `__TIMESTAMP__` | Include depth · main file · file modification time | GCC/Clang extensions |

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
    long standard = _MSVC_LANG;                       // MSVC's honest value
#else
    long standard = __cplusplus;
#endif
    std::cout << compiler << ", C++ " << standard << ", hosted=" << __STDC_HOSTED__ << '\n';
    std::cout << (standard >= 201703L ? "C++17 or newer" : "older than C++17") << '\n';
}
// expect: C++17 or newer
```
Test `__clang__` before `__GNUC__`, because Clang defines both. On MSVC read `_MSVC_LANG` (or compile with `/Zc:__cplusplus`), otherwise every version reports `199711L`.

### Stop the Build Early: `#error` and `static_assert` (C++17)
```cpp
#include <climits>
#include <cstdint>
#include <type_traits>

#if __cplusplus < 201703L && !defined(_MSVC_LANG)
#error "This code needs C++17 or newer"          // layer 1: decided from macros alone
#endif

static_assert(CHAR_BIT == 8, "bytes must be 8 bits");             // layer 2: constants
static_assert(sizeof(std::int32_t) == 4);                          // C++17: no message needed

template <typename T>
T average(T a, T b) {
    static_assert(std::is_arithmetic<T>::value, "average() needs a number type");   // checked per T
    return (a + b) / 2;
}

int main() { return average(4, 6) == 5 ? 0 : 1; }
```
`#error` can only see macros. `static_assert` sees types, `sizeof` and `constexpr` values, and inside a template it fires per instantiation with your message instead of a page of template errors.

### The Build Stopped by `#error`
```cpp
// cc: ill-formed
#define CONFIG_MAX_USERS 0

#if CONFIG_MAX_USERS <= 0
#error "CONFIG_MAX_USERS must be positive"       // compilation ends here, with this exact text
#endif

int main() {}
```

### `assert`: Run-Time Checks That Vanish in Release Builds
```cpp
#include <cassert>
#include <iostream>
#include <vector>

double mean(const std::vector<double>& v) {
    assert(!v.empty() && "mean() of an empty vector");      // documents AND checks the precondition
    double s = 0;
    for (double x : v) s += x;
    return s / static_cast<double>(v.size());
}

int main() {
    std::cout << mean({2, 4, 9}) << '\n';
    // mean({});   // debug build: "Assertion `!v.empty() && "mean() of an empty vector"' failed."
    //             //   + file, line, function name, then abort()
}
// expect: 5
```
The `&& "text"` idiom works because a string literal is always "true", and the whole expression is what gets printed. Never put work with side effects inside `assert` (`assert(++count < 10)`): in a release build the whole expression disappears.

### NDEBUG Is Read at Each `#include <cassert>`
```cpp
#define NDEBUG                 // ① must come BEFORE the include
#include <cassert>
#include <iostream>

int main() {
    assert(1 + 1 == 3);        // ② expands to ((void)0): not even evaluated
    std::cout << "still running\n";
}
// expect: still running
```
1. Release configurations pass `-DNDEBUG` (CMake's `Release` and `RelWithDebInfo` do; Visual Studio's Release does). `<cassert>` is special: it re-reads `NDEBUG` *every* time it is included, so a file can switch assertions on and off part-way through (rarely a good idea).
2. Because the expression vanishes, code that only works if the assert runs is a bug that appears only in release builds.

### A Better Assert Macro: Message, Location, and Values
```cpp
#include <cstdio>
#include <cstdlib>

#define CHECK(cond, msg)                                                         \
    do {                                                                         \
        if (!(cond)) {                                                           \
            std::fprintf(stderr, "CHECK failed: %s (%s) at %s:%d in %s\n",       \
                         #cond, msg, __FILE__, __LINE__, __func__);              \
            /* std::abort(); */                                                  \
        }                                                                        \
    } while (0)

int main() {
    int stock = -2;
    if (stock < 0) CHECK(stock >= 0, "stock went negative");   // do/while(0): safe after if
    std::puts("done");
}
// expect: done
```
`#cond` turns the expression into text, `__FILE__`/`__LINE__` expand at the *call site* (that's why this has to be a macro), and `do { ... } while (0)` makes the macro behave like a single statement after an `if` with no braces. Unlike `assert`, this one stays on in release builds; production code often keeps a check like this for invariants that guard data. In C++20, a function taking `std::source_location loc = std::source_location::current()` gets the location without a macro, but it still can't stringize the expression.

### Feature Detection Instead of Version Numbers (C++17)
```cpp
#include <iostream>
#if __has_include(<version>)
#include <version>                                  // C++20: all __cpp_lib_* macros in one place
#endif

#if defined(__cpp_lib_optional)
#include <optional>
using MaybeInt = std::optional<int>;
const char* backend = "std::optional";
#else
struct MaybeInt { bool has = false; int value = 0; };   // fallback for old libraries
const char* backend = "fallback struct";
#endif

int main() {
    std::cout << "using " << backend
#if defined(__cpp_concepts)
              << ", concepts available"
#endif
              << '\n';
}
// expect: using std::optional
```
Testing the specific feature (`__cpp_lib_optional`) is more reliable than testing `__cplusplus`: a compiler can claim C++20 while still missing parts of its library, or support a feature early.

### Stringize and Token-Paste, Including the Two-Level Trick
```cpp
#include <iostream>

#define VERSION_MAJOR 3
#define STR_RAW(x) #x
#define STR(x) STR_RAW(x)                 // ① expand first, THEN stringize
#define CAT_RAW(a, b) a##b
#define CAT(a, b) CAT_RAW(a, b)

int CAT(counter_, VERSION_MAJOR) = 7;     // ② defines: int counter_3 = 7;

int main() {
    std::cout << STR_RAW(VERSION_MAJOR) << ' '        // "VERSION_MAJOR": # does not expand
              << STR(VERSION_MAJOR) << ' '            // "3": the extra level expands it
              << STR(__LINE__) << ' ' << counter_3 << '\n';
}
// expect: VERSION_MAJOR 3
```
1. `#` and `##` use the argument *exactly as written*, before macro expansion. Passing it through one more macro level expands it first. This is the standard trick for `STR(__LINE__)` and for building unique names such as `CAT(guard_, __LINE__)`.
2. Token pasting builds identifiers; reach for it rarely, because generated names are invisible to search and to the debugger.

### X-Macros: One List, Several Expansions
```cpp
#include <iostream>

#define COLOR_LIST(X) \
    X(Red)            \
    X(Green)          \
    X(Blue)

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

int main() { std::cout << to_string(Color::Green) << ' ' << to_string(Color::Blue) << '\n'; }
// expect: Green Blue
```
The enum and its name table can never drift apart, because both come from one list. This is one of the few jobs where macros still beat every language feature (until C++26 reflection).

### Variadic Logging Macro with `__VA_OPT__` (C++20)
```cpp
// cc: std=c++20
#include <cstdio>

#define LOG(level, fmt, ...) \
    std::printf("[%s] %s:%d " fmt "\n", level, __func__, __LINE__ __VA_OPT__(,) __VA_ARGS__)

int main() {
    LOG("info", "starting");                          // no extra args: __VA_OPT__(,) vanishes
    LOG("warn", "disk at %d%%", 91);                  // extra args: the comma appears
}
// expect: disk at 91%
```
Before C++20, an empty `__VA_ARGS__` left a dangling comma; compilers offered the non-standard `, ##__VA_ARGS__` fix. `__VA_OPT__(,)` is the standard spelling.

### `#elifdef` and `#warning` (C++23)
```cpp
// cc: std=c++23
#include <iostream>

#define USE_FAST_PATH

#ifdef USE_SAFE_PATH
constexpr const char* path = "safe";
#elifdef USE_FAST_PATH                    // C++23: shorthand for #elif defined(USE_FAST_PATH)
constexpr const char* path = "fast";
#else
#warning "no path selected, defaulting"   // C++23: standard (GCC/Clang had it as an extension)
constexpr const char* path = "default";
#endif

int main() { std::cout << path << '\n'; }
// expect: fast
```

## Key Concepts

### The Preprocessor Works on Tokens, Not on C++
Macro replacement happens in translation phase 4, before the compiler knows any type, scope or namespace. A macro named `max` replaces *every* later token `max`, including `std::max` (the reason `<windows.h>` users write `#define NOMINMAX`). Macros are therefore named in `ALL_CAPS` by convention, so they can't collide with normal identifiers ([[The Preprocessor]]).

### Function-Like Macros Evaluate Arguments Textually
`SQUARE(i++)` becomes `((i++) * (i++))`: two unsequenced increments of the same variable, which is undefined behaviour. Missing parentheses turn `SQUARE(a + 1)` into `a + 1 * a + 1`. Prefer `constexpr` functions, templates and `inline` variables; keep macros for what only the preprocessor can do: stringizing, `__FILE__`/`__LINE__` at the call site, conditional compilation, and include guards.

### Three Assertion Layers, One Rule: Earliest Wins
| Layer | Tool | Sees | Cost | Typical use |
|---|---|---|---|---|
| Preprocessing | `#error`, `#warning` (C++23) | Macros only | Zero | Wrong standard, platform, configuration |
| Compilation | `static_assert` (C++11) | Types, `sizeof`, `constexpr` values, traits | Zero | Layout assumptions, template requirements |
| Run time | `assert` (`<cassert>`), C++26 `contract_assert` / `pre` / `post` | Actual values | A branch, unless `NDEBUG` | Preconditions, invariants, "can't happen" states |

C++20 concepts replace many template `static_assert`s with constraints that also take part in overload resolution ([[Concepts and Constraints]]).

### `assert` Is for Bugs, Not for Errors
An assertion says "if this is false, the *program* is wrong". It is not for things that can legitimately fail (a missing file, bad user input, a network timeout); those need error handling that also works in release builds ([[Exceptions]], [[Error Handling Strategies Compared]]). Asserts document preconditions and get deleted in release builds, so they must never be the only defence against invalid input.

### `assert` and Commas (Before C++26)
`assert` is a macro with one parameter, so a comma not inside parentheses splits the argument: `assert(std::is_same<int, int>::value)` fails to compile. Wrap the expression in extra parentheses: `assert((std::is_same<int, int>::value))`. C++26 made `assert(...)` variadic to fix this.

### Different `NDEBUG` in Different Files Can Break the ODR
An `inline` function or template that contains `assert` and is compiled in one file with `NDEBUG` and in another without has two different definitions, which violates the One Definition Rule, and the linker keeps one at random. Set `NDEBUG` once per build configuration, on the command line, never with `#define` in individual files.

### Feature-Test Macros Beat Version Checks
`#if __cplusplus >= 202002L` assumes the whole C++20 library exists; real compilers ship features at different times, and MSVC reports `199711L` by default. Test the exact feature (`__cpp_lib_format`, `__has_include(<format>)`) and include `<version>` to get all library macros.

### GCC's Obsolete `#assert` Directive
GCC once supported "preprocessor assertions", `#assert machine(x86)` tested with `#if #machine(x86)`, and `#unassert`. They are deprecated, non-standard and rejected by other compilers. Use ordinary macros and `#if defined(...)` instead. They are unrelated to `assert`.

## Choosing a Tool

```text
Need                                                    Best choice
────────────────────────────────────────────────────────────────────────────────────────
Refuse to build on the wrong standard/platform/config   #if ... #error "why" #endif
Warn but keep building                                  #warning (C++23) or #pragma message
Check a type's size, trait or a constexpr value         static_assert(cond, "why")
Restrict which types a template accepts                 C++20 concepts / requires; else static_assert
Check a precondition or invariant while developing      assert(cond && "why")      (<cassert>)
Check something that must hold in release builds too    a custom CHECK macro, or throw/return an error
Report file/line/function from a helper function        std::source_location (C++20); before: __FILE__/__LINE__ macro
Detect a library/language feature                       <version> + __cpp_lib_xxx / __cpp_xxx / __has_include
Detect compiler / OS / CPU                              __clang__ · __GNUC__ · _MSC_VER · _WIN32 · __linux__ · __x86_64__
A named constant                                        constexpr variable, not #define
A small reusable computation                            constexpr / inline function, not a macro
Generate parallel lists (enum ↔ names)                  X-macro (or C++26 reflection)
Include a header once                                   #pragma once or an include guard
Embed a binary file in the program                      #embed (C++26); before: a generated array
```

## Best Practices

1. **Check each fact at the earliest layer that can see it**: `#error` → `static_assert` → `assert`
2. **Always give assertions a message** (`static_assert(c, "why")`, `assert(c && "why")`)
3. **Never put side effects in `assert`**; they disappear when `NDEBUG` is defined
4. **Set `NDEBUG` per build configuration** on the command line, never per file
5. **Prefer `constexpr`, `inline` and templates to macros**; use macros only for what needs the preprocessor
6. **Parenthesize every macro parameter and the whole body**; wrap statement macros in `do { } while (0)`
7. **Name macros in `ALL_CAPS`** and `#undef` local helper macros after use
8. **Detect features, not versions**: `<version>` + `__cpp_lib_*`, `__has_include`, `__has_cpp_attribute`
9. **On MSVC, compile with `/Zc:__cplusplus`** (and `/Zc:preprocessor` for the standard-conforming preprocessor), or read `_MSVC_LANG`
10. **When a macro misbehaves, look at the output of `g++ -E`** (or `cl /P`) rather than guessing

## Related Headers

```cpp
// cc: std=c++23
#include <cassert>          // assert, reads NDEBUG at the point of inclusion
#include <version>          // C++20: every library feature-test macro (__cpp_lib_*)
#include <source_location>  // C++20: std::source_location, the macro-free __FILE__/__LINE__/__func__
#include <stacktrace>       // C++23: std::stacktrace for richer failure reports
#include <type_traits>      // traits used inside static_assert
#include <climits>          // macro limits: CHAR_BIT, INT_MAX ...
#include <cstdint>          // INT32_MAX, UINT64_C(...) and other integer macros
#include <cstdlib>          // std::abort, EXIT_SUCCESS / EXIT_FAILURE
#include <cerrno>           // errno and its E* macros
```

## Connections

- **Hub:** [[Map — Standard Headers]]
- **Concept notes (the why behind this card):** [[The Preprocessor]] · [[assert and static_assert]] · [[Headers and Include Guards]] · [[The Compilation Pipeline]] · [[Translation Units]] · [[Modules (C++20)]] · [[Concepts and Constraints]]
- **Hazards:** [[Undefined Behavior]] (redefining standard macros, side effects in macro arguments) · [[The One Definition Rule]] (mixed `NDEBUG`)
- **Error handling:** [[Exceptions]] · [[Error Handling Strategies Compared]]
- **Sibling cards:** [[Header — Modern IO]] (`source_location`-based logging) · [[Header — cstdio]] (`printf`-style logging macros)
- **Practice:** *Continuum #1 Hello, Compiler* (print the compiler, `__cplusplus` and platform macros; dump them with `g++ -dM -E`) · *#6 Function Library & Header Refactor* (include guards, `static_assert` on your types, `assert` on every precondition, then build with `-DNDEBUG` and compare)

## Sources

- Primer §2.6.3 "Writing Our Own Header Files" (p. 76): a brief introduction to the preprocessor, preprocessor variables and header guards.
- Primer §6.5.3 "Aids for Debugging" (p. 240): the `assert` preprocessor macro and the `NDEBUG` preprocessor variable (p. 241), with `__func__`, `__FILE__`, `__LINE__`, `__TIME__`, `__DATE__`.
- Tour §4.5 "Assertions" (p. 48): `assert`, `static_assert` and when to check at compile time versus run time.
- Tour §19.2 "C++ Feature Evolution" (p. 263): which standard introduced which facility.
- cppreference / web, *Preprocessor*, *Replacing text macros* (predefined macros, `__VA_OPT__`, `#`, `##`), *Conditional inclusion*, *Diagnostic directives*, *Feature testing*, *assert*, *static_assert*: https://en.cppreference.com/w/cpp/preprocessor · https://en.cppreference.com/w/cpp/preprocessor/replace · https://en.cppreference.com/w/cpp/preprocessor/conditional · https://en.cppreference.com/w/cpp/preprocessor/error · https://en.cppreference.com/w/cpp/feature_test · https://en.cppreference.com/w/cpp/error/assert · https://en.cppreference.com/w/cpp/language/static_assert
- GCC manual, *The C Preprocessor*: "Predefined Macros", "Common Predefined Macros", "Obsolete Features: Assertions": https://gcc.gnu.org/onlinedocs/cpp/
- Microsoft Learn, *Predefined macros* and *`/Zc:__cplusplus`*: https://learn.microsoft.com/en-us/cpp/preprocessor/predefined-macros
- C++ Core Guidelines ES.30 "Don't use macros for program text manipulation", ES.31 "Don't use macros for constants or functions", ES.32 "Use ALL_CAPS for all macro names", I.6 "Prefer `Expects()` for expressing preconditions", P.5 "Prefer compile-time checking to run-time checking", P.7 "Catch run-time errors early": https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
