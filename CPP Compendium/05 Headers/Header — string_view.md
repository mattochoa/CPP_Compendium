---
id: hdr-string-view
title: Header — string_view
aliases:
- <string_view>
- std::string_view
- string view
- sv literal
type: header
domain: HDR
tier: 2
status: draft
standard: C++17
prereqs:
- "[[string_view]]"
related:
- "[[string_view]]"
- "[[string]]"
- "[[Dangling Pointers and References]]"
- "[[Temporaries and Lifetime Extension]]"
- "[[span]]"
tags:
- type/header
- domain/hdr
- tier/2
- header/string_view
- tension/safety-vs-performance
- tension/abstraction-vs-control
created: 2026-09-26
updated: 2026-09-26
header: <string_view>
---

# Header — string_view

> [!essence]
> **`<string_view>`** provides `std::string_view`, a **read-only window onto characters that someone else owns**: just a pointer and a length. Creating, copying, slicing (`substr`) and passing one never allocates and never copies characters, so one `string_view` parameter accepts a `std::string`, a literal, a `char` buffer or a slice of any of them for free. The price is the one every non-owning type pays: **the view is only valid while the characters it points at are alive and unchanged**, and nothing checks that for you.

> [!standard] Versions
> C++17 (`string_view` and `wstring_view`/`u16string_view`/`u32string_view`, `""sv` literals, `std::hash`, whole class `constexpr`) / C++20 (`starts_with`, `ends_with`; iterator-pair constructor; `u8string_view`; `<=>` replaces `<`, `>`, `<=`, `>=`, `!=`; models `std::ranges::view` and `borrowed_range`) / C++23 (`contains`; construction from `nullptr` **deleted**; explicit range constructor; guaranteed trivially copyable) / C++26 (`std::string + std::string_view` concatenation)

## Memory Layout

A `string_view` is two machine words (16 bytes on 64-bit): where the characters start and how many there are. It holds no characters of its own.

```text
  OWNER: std::string s = "key=value;mode=fast"          VIEWS (on the stack, 16 bytes each)
                                                        ┌──────────────────────────────┐
  s ──▶ heap: ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐ │ whole = s                    │
              │ k │ e │ y │ = │ v │ a │ l │ u │ e │ ; │ │   data ● → 'k'   size = 19   │
              └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘ ├──────────────────────────────┤
                ▲               ▲                       │ val = whole.substr(4, 5)     │
                │               └── val.data()          │   data ● → 'v'   size = 5    │
                └────────────────── whole.data()        │  (no allocation, no copy)    │
                                                        └──────────────────────────────┘
  If s is destroyed, reassigned or grows (reallocates), BOTH views dangle.
  val.data() is NOT a C string: the character after 'e' is ';', not '\0'.
```

## Quick Reference

```cpp
// cc: fragment
// ═══════════════════════════════════════════════════════════════════════════
// CONSTRUCTION  (all O(1) except from a bare const char*, which runs strlen)
// ═══════════════════════════════════════════════════════════════════════════
std::string_view sv;                    // none        | Empty view            | data() may be nullptr
std::string_view sv = str;              // std::string | View of its chars     | implicit conversion from std::string
std::string_view sv = "text";           // const char* | Up to the '\0'        | strlen at run time (or at compile time if constexpr)
std::string_view sv(ptr, n);            // ptr, count  | Exactly n chars       | may contain '\0'; may be non-terminated
std::string_view sv(first, last);       // iterators   | Contiguous range      | C++20
std::string_view sv(nullptr);           // ✗           | Does not compile      | C++23 (was UB before)
using namespace std::literals;          // enables ""sv (and ""s)
auto sv = "text"sv;                     // literal     | string_view, length known at compile time | C++17
std::string s(sv);                      // view        | Owning copy           | EXPLICIT: never implicit

// ═══════════════════════════════════════════════════════════════════════════
// ELEMENT ACCESS  (read-only: no operator[] that writes)
// ═══════════════════════════════════════════════════════════════════════════
sv[i]                                   // index       | char, unchecked       | UB if i >= size()
sv.at(i)                                // index       | char, checked         | throws std::out_of_range
sv.front()  /  sv.back()                // none        | First / last char     | UB if empty
sv.data()                               // none        | const char*           | NOT guaranteed null-terminated!
sv.size()  /  sv.length()  /  sv.empty()

// ═══════════════════════════════════════════════════════════════════════════
// SHRINKING THE WINDOW  (O(1): moves the pointer / length, never touches chars)
// ═══════════════════════════════════════════════════════════════════════════
sv.remove_prefix(n)                     // count       | Drop n from the front | precondition n <= size()
sv.remove_suffix(n)                     // count       | Drop n from the back  | precondition n <= size()
sv.substr(pos, n)                       // pos, count  | A NEW VIEW            | throws if pos > size(); no allocation

// ═══════════════════════════════════════════════════════════════════════════
// SEARCH & COMPARE  (same names and npos convention as std::string)
// ═══════════════════════════════════════════════════════════════════════════
sv.find(x, pos) / rfind / find_first_of / find_last_of / find_first_not_of / find_last_not_of
                                        // x: view, char, or const char* | Returns index or npos
sv.starts_with(x)  /  sv.ends_with(x)   // view/char   | Prefix / suffix test  | C++20
sv.contains(x)                          // view/char   | Substring test        | C++23
sv.compare(other)                       // view        | <0, 0, >0             |
a == b,  a <=> b                        // views       | Compares characters   | <=> C++20; mixes freely with string and literals
sv.copy(dest, n, pos)                   // char*       | Copy chars out        | does NOT write a '\0'

// ═══════════════════════════════════════════════════════════════════════════
// INTEROP
// ═══════════════════════════════════════════════════════════════════════════
std::string(sv)                         // Owning copy (when you must keep it, or need c_str())
std::string{sv}.c_str()                 // A real C string for C APIs (temporary: use immediately)
str.append(sv) / str += sv / str.insert(pos, sv) / str.compare(sv) / str.find(sv)   // std::string accepts views
str + sv                                // C++26; before: str + std::string(sv), or str.append(sv)
std::cout << sv                         // prints exactly size() chars
std::hash<std::string_view>{}(sv)       // same hash as the equal std::string
std::from_chars(sv.data(), sv.data() + sv.size(), n)   // parse numbers from a view (<charconv>, C++17)
std::wstring_view  std::u8string_view (C++20)  std::u16string_view  std::u32string_view
```

## Patterns

### One Parameter Type for Every Kind of String
```cpp
#include <iostream>
#include <string>
#include <string_view>

std::size_t count_vowels(std::string_view s) {          // by value: it's only 16 bytes
    std::size_t n = 0;
    for (char c : s) n += (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u');
    return n;
}

int main() {
    std::string owned = "education";
    char buffer[] = {'a', 'u', 'x', 'q'};                 // not null-terminated
    std::cout << count_vowels("banana") << ' '            // literal: no std::string built
              << count_vowels(owned) << ' '               // std::string: converts, no copy
              << count_vowels({buffer, 2}) << ' '         // pointer + length
              << count_vowels(std::string_view(owned).substr(0, 3)) << '\n';   // a slice: "edu"
}
// expect: 3 5 2 2
```
With `const std::string&` the literal call would build (and possibly heap-allocate) a temporary `std::string`, and the buffer call wouldn't compile without a copy. See Under the Hood.

### Split Without Allocating Substrings
```cpp
#include <iostream>
#include <string_view>
#include <vector>

std::vector<std::string_view> split(std::string_view s, char delim) {
    std::vector<std::string_view> parts;
    while (true) {
        auto pos = s.find(delim);
        parts.push_back(s.substr(0, pos));               // a view into the caller's text
        if (pos == std::string_view::npos) break;
        s.remove_prefix(pos + 1);                        // slide the window past the delimiter
    }
    return parts;
}

int main() {
    const char* csv = "red,green,,blue";                 // lives for the whole program
    for (auto p : split(csv, ',')) std::cout << '[' << p << ']';
    std::cout << '\n';
}
// expect: [red][green][][blue]
```
The returned views point into `csv`. Keep the source alive for as long as you use them; split a `std::string` that is about to be destroyed and every piece dangles.

### Trim Whitespace
```cpp
#include <iostream>
#include <string_view>

std::string_view trim(std::string_view s) {
    const auto ws = " \t\r\n";
    auto first = s.find_first_not_of(ws);
    if (first == std::string_view::npos) return {};      // all whitespace
    s.remove_prefix(first);
    s.remove_suffix(s.size() - 1 - s.find_last_not_of(ws));
    return s;
}

int main() {
    std::cout << '[' << trim("  \t hello world \n") << "][" << trim("   ") << "]\n";
}
// expect: [hello world][]
```

### Parse key=value and Numbers (C++17)
```cpp
#include <charconv>
#include <iostream>
#include <optional>
#include <string_view>

std::optional<int> to_int(std::string_view s) {
    int value = 0;
    auto [ptr, ec] = std::from_chars(s.data(), s.data() + s.size(), value);   // no '\0' needed
    if (ec != std::errc{} || ptr != s.data() + s.size()) return std::nullopt;  // whole view must parse
    return value;
}

int main() {
    std::string_view line = "timeout=250";
    auto eq = line.find('=');
    std::string_view key = line.substr(0, eq);
    std::string_view val = line.substr(eq + 1);
    auto n = to_int(val);
    std::cout << key << ' ' << (n ? *n * 2 : -1) << ' ' << (to_int("12ms") ? "ok" : "bad") << '\n';
}
// expect: timeout 500 bad
```
`std::stoi` needs a `std::string` (a copy); `std::from_chars` works directly on the view's bounds and never allocates or throws.

### Prefix, Suffix and Contains Checks
```cpp
// cc: std=c++20
#include <iostream>
#include <string_view>

int main() {
    std::string_view file = "report-2026.csv";
    bool csv    = file.ends_with(".csv");                        // C++20
    bool report = file.starts_with("report");                    // C++20
    bool year   = file.find("2026") != std::string_view::npos;   // C++17 form of contains (C++23)
    bool csv17  = file.size() >= 4 && file.compare(file.size() - 4, 4, ".csv") == 0;   // C++17 ends_with
    std::cout << csv << report << year << csv17 << '\n';
}
// expect: 1111
```

### Literals and Embedded Nulls
```cpp
#include <iostream>
#include <string_view>

int main() {
    using namespace std::literals;
    auto full = "a\0b"sv;                           // length taken from the literal: 3
    std::string_view cut = "a\0b";                  // const char* constructor stops at '\0': 1
    std::cout << full.size() << ' ' << cut.size() << '\n';
}
// expect: 3 1
```
`""sv` also avoids the run-time `strlen`, since the literal's length is known at compile time.

### `data()` Is Not a C String
```cpp
#include <cstring>
#include <iostream>
#include <string>
#include <string_view>

int main() {
    std::string s = "hello world";
    std::string_view first = std::string_view(s).substr(0, 5);    // "hello"
    std::cout << first.size() << ' ' << std::strlen(first.data()) << ' ';   // strlen runs to s's '\0'
    std::string copy(first);                                       // owning, null-terminated
    std::cout << std::strlen(copy.c_str()) << '\n';
}
// expect: 5 11 5
```
Never pass `sv.data()` to a function expecting a null-terminated string (`fopen`, `printf("%s")`, `atoi`, most OS APIs). Here `strlen` happened to find `s`'s terminator; with a plain `char` buffer it would read off the end. Make a `std::string` first.

### Look Up Without Allocating: Transparent Comparators
```cpp
#include <functional>
#include <iostream>
#include <map>
#include <string>
#include <string_view>

int main() {
    std::map<std::string, int, std::less<>> prices{{"apple", 3}, {"pear", 5}};   // std::less<> is transparent
    std::string_view key = "pear-and-more";
    key.remove_suffix(9);                                  // "pear"
    auto it = prices.find(key);                            // compares with the view: no std::string built
    std::cout << (it != prices.end() ? it->second : -1) << '\n';
}
// expect: 5
```
With the default `std::less<std::string>`, `find` would need a `std::string` key and a copy. `std::unordered_map` gets the same ability in C++20 with a transparent hash (`is_transparent`) plus `std::equal_to<>`.

### Compile-Time String Processing (C++17)
```cpp
#include <iostream>
#include <string_view>

constexpr std::string_view extension(std::string_view path) {
    auto dot = path.rfind('.');
    return dot == std::string_view::npos ? std::string_view{} : path.substr(dot + 1);
}

constexpr std::string_view config = "settings/app.json";
static_assert(extension(config) == "json", "checked by the compiler");   // evaluated at compile time

int main() { std::cout << extension(config) << ' ' << extension("README").size() << '\n'; }
// expect: json 0
```
Every `string_view` member is `constexpr` since C++17, so parsing literals, checking names and building lookup keys can all happen during compilation ([[constexpr and consteval Functions]]).

### The Dangling View
```cpp
// cc: ub
#include <iostream>
#include <string>
#include <string_view>

int main() {
    std::string_view sv = std::string("a string long enough to live on the heap") + "!";
    std::cout << sv << '\n';      // the temporary std::string died at the ';' above: use-after-free
}
```
The right-hand side is a temporary `std::string`. The view keeps only its pointer, and **binding a view does not extend the temporary's lifetime** (a `const std::string&` would have). ASan reports a heap-use-after-free. The same trap springs from returning a `string_view` to a local string, storing a view of a function's temporary result, or keeping a view while the source `std::string` is appended to (reallocation) ([[Temporaries and Lifetime Extension]], [[Dangling Pointers and References]]).

## Under the Hood

> [!machine] A view travels in two registers; a `const std::string&` from a literal builds a string
> The same call, `f("configuration-file-name.json")`, against two parameter types. GCC 13.3, `-std=c++17 -O2`, x86-64:
> ```nasm
> call_view():                                  ; f(std::string_view)
>         mov  edi, 28                          ; size, computed at compile time
>         lea  rsi, .LC0[rip]                   ; pointer to the literal
>         jmp  by_view(std::string_view)        ; that's all: 3 instructions
>
> call_ref():                                   ; f(const std::string&)
>         ...                                   ; reserve a std::string on the stack
>         call std::string::_M_create(...)      ; 28 chars > 15-char SSO buffer: HEAP ALLOCATION
>         movups [rax], xmm0                    ; copy the characters in
>         ...
>         call by_ref(std::string const&)
>         ...
>         call operator delete(void*, unsigned long)   ; free it again afterwards
> ```
> libstdc++ lays out `string_view` as `{size, pointer}`, so the pair fits in `rdi`/`rsi` and is passed **by value** with no memory traffic. That's why the guideline is `std::string_view` by value, not `const std::string_view&`.

## Key Concepts

### Owning vs Viewing
`std::string` **owns**: it allocates, copies and frees its characters. `std::string_view` **borrows**: it's a pointer plus a length into characters owned elsewhere. The same split appears as `std::vector<T>` vs `std::span<T>` ([[span]]). Views make passing and slicing cheap and put the whole burden of lifetime on you.

### The Lifetime Rule
A view is valid only while its characters exist and haven't been moved. That's invalidated by the owner's destruction, by any `std::string` operation that may reallocate (`+=`, `append`, `insert`, `reserve`, `shrink_to_fit`, assignment), and by the end of a temporary's full-expression. **Views are ideal as function parameters** (the caller's argument outlives the call). They're dangerous as **return types, data members and long-lived variables** unless the source is a literal or otherwise clearly outlives them.

### No Null Terminator
A view is defined by its length, not by a `'\0'`. `substr` and `remove_suffix` can't add one, so `data()` may point at text that continues past the view, or at a buffer with no terminator at all. Everything that expects a C string needs `std::string(sv).c_str()`.

### `substr` Differs Between string and string_view
`std::string::substr` returns a new **owning copy** (allocates). `std::string_view::substr` returns a **view** (O(1)). The same code can change from "safe and slow" to "fast and dangling" when a variable's type changes from `std::string` to `std::string_view`, or back.

### Conversions Are Deliberately One-Way
`std::string` → `std::string_view` is **implicit** (cheap and always safe at the moment of conversion). `std::string_view` → `std::string` is **explicit** (it allocates). So passing a string to a view parameter is free, while getting an owner back makes you write `std::string(sv)` where the cost is visible.

### Read-Only
`string_view` has no mutating access to characters; its iterators and `operator[]` are `const`. To modify characters in place, use `std::span<char>` or the `std::string` itself.

## Choosing a Tool

```text
Need                                                       Best choice
─────────────────────────────────────────────────────────────────────────────────────────────
Read-only string parameter                                 std::string_view   (by value)
Parameter that will be STORED (sink)                       std::string by value, then std::move it in
Parameter passed on to a C API needing '\0'                const std::string& (or const char*)
Return a string built inside the function                  std::string
Return a slice of a member / static / literal text         std::string_view (document the lifetime)
Data member                                                std::string (a view member usually dangles)
Split / tokenize / trim a buffer you keep alive            std::string_view slices
Modify characters in place                                 std::string& or std::span<char>
Keys for a std::map you look up with views                 std::map<std::string, V, std::less<>>
Compile-time string constants                              constexpr std::string_view (or ""sv)
```

## Best Practices

1. **Take read-only string parameters as `std::string_view` by value** (C++ Core Guidelines SL.str.2)
2. **Never return a `string_view` into a local or temporary `std::string`**; return `std::string`
3. **Don't store views in long-lived objects** unless the source is a literal or clearly outlives them
4. **Never initialize a view from a temporary string** (`sv = make_string();`, `sv = a + b;`)
5. **Don't keep a view across operations that may reallocate the source** (`+=`, `append`, `reserve`)
6. **Never pass `sv.data()` to a C API**; convert with `std::string(sv)` first
7. **Use `""sv` literals** for constants: length known at compile time, embedded `'\0'` kept
8. **Parse numbers with `std::from_chars`**, which works on a view's bounds without allocating
9. **Use `std::less<>` for maps** you search with views, to avoid building temporary strings
10. **Remember that `substr` on a view is another view**: convert to `std::string` before the source goes away

## Related Headers

```cpp
#include <string_view>   // std::string_view and friends, ""sv literals, std::hash
#include <string>        // std::string: the owner; converts to string_view implicitly
#include <charconv>      // std::from_chars / to_chars: number parsing on views (C++17)
#include <span>          // C++20: the same view idea for any contiguous T (span<char> is writable)
#include <functional>    // std::less<> / std::equal_to<>: transparent comparators for lookups
#include <format>        // C++20: std::format accepts string_view arguments and format strings
#include <algorithm>     // search, count, equal... work on string_view iterators
```

## Connections

- **Hub:** [[Map — Standard Headers]]
- **Concept notes (the why behind this card):** [[string_view]] · [[string]] · [[span]] · [[Temporaries and Lifetime Extension]] · [[constexpr and consteval Functions]] · [[Functions and Parameters — The Complete Picture]] (choosing parameter types)
- **Hazards:** [[Dangling Pointers and References]] (the dangling view) · [[Undefined Behavior]] (`sv[i]` out of range, `remove_prefix(n)` with `n > size()`)
- **Sibling cards:** [[Header — string]] · [[Header — cstring]] · [[Header — sstream]] · [[Header — Modern IO]]
- **Practice:** *Continuum #7 Word & Text Analyzer* (tokenize a file's text into views and count words without allocating per word; keep the file buffer alive for the whole analysis)

## Sources

- Tour §10.3 "String Views" (p. 128): `string_view` as a (pointer, length) pair, its motivation, and the dangling hazard; §10.5 "Advice" (p. 136).
- Tour §10.2 "Strings" (p. 125): the owning `std::string` the view complements.
- cppreference / web, *`std::basic_string_view`*: https://en.cppreference.com/w/cpp/string/basic_string_view (every member and version label on this card)
- cppreference / web, *`<string_view>`*: https://en.cppreference.com/w/cpp/header/string_view · *`std::from_chars`*: https://en.cppreference.com/w/cpp/utility/from_chars
- C++ Core Guidelines SL.str.2 "Use `std::string_view` or `gsl::span<char>` to refer to character sequences" and F.15–F.16 (parameter passing): https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
