# CPP_REFERENCE_INDEX

## Core Definition
Index for the C++ standard library quick-reference set. Each file follows the same shape: a **Target | Operation | Output** signature table, common patterns with runnable examples, important concepts, and best practices.

**Tags**: #cpp #reference #index #stdlib

---

## FILES

### Requested set

| File | Header | Covers |
|---|---|---|
| `IOSTREAM_REFERENCE.md` | `<iostream>` | Stream hierarchy, `cin`/`cout`/`cerr`/`clog`, formatted and unformatted I/O, stream state, format flags, tie/rdbuf, sentries |
| `IOMANIP_REFERENCE.md` | `<iomanip>` + `<ios>` | Every manipulator — parameterized and not. `setw`/`setfill`/`setprecision`, alignment, base, float format, `quoted`, `put_time`/`put_money`, stickiness rules, format-state RAII |
| `FSTREAM_REFERENCE.md` | `<fstream>` | `ifstream`/`ofstream`/`fstream`/`filebuf`, open modes and the mode matrix, positioning, binary I/O, random access, `filesystem` companions |
| `CSTRING_REFERENCE.md` | `<cstring>` | C-string and raw-memory functions, wide counterparts, the safety cheat sheet, why `std::string` usually wins |
| `STRING_REFERENCE.md` | `<string>` | `std::string` full member list, `string_view`, searching, numeric conversion, SSO, iterator invalidation, performance table |
| `CMATH_REFERENCE.md` | `<cmath>` | All math functions, classification, rounding, special functions (C++17), `<numbers>` constants, floating-point comparison, domain table |

### Standard I/O library (per en.cppreference.com/w/cpp/io)

| File | Header | Covers |
|---|---|---|
| `IOS_REFERENCE.md` | `<ios>` | `ios_base` and `basic_ios` — the foundation. All flag types, state semantics, `copyfmt`, `xalloc`/`iword`/`pword`, callbacks, `io_errc` |
| `SSTREAM_REFERENCE.md` | `<sstream>` | `istringstream`/`ostringstream`/`stringstream`/`stringbuf`, parsing and building, C++20 `view()` and move-`str()`, tool-selection table |
| `STREAMBUF_REFERENCE.md` | `<streambuf>` | The buffer model, get/put areas, every protected virtual, working custom buffers (null sink, tee, prefixer, buffered in/out), `char_traits` |
| `CSTDIO_REFERENCE.md` | `<cstdio>` | `FILE*` I/O, full `printf`/`scanf` specifier tables, binary I/O, RAII wrapper, the classic traps, mapping to `std::format` |
| `MODERN_IO_REFERENCE.md` | `<print>` `<format>` `<syncstream>` `<spanstream>` `<iosfwd>` | C++20/23 I/O: format spec grammar, custom `formatter`, thread-safe output, allocation-free streams, forward declarations, removed headers |

---

## WHERE TO LOOK

```
Question                                          File
────────────────────────────────────────────────────────────────────────────
"Why does my getline read an empty line?"         IOSTREAM  (the >> then getline trap)
"How do I make a column line up?"                 IOMANIP   (aligned table output)
"Why is my setw only working once?"               IOMANIP   (stickiness table)
"What does ios::ate do vs ios::app?"              FSTREAM   (open mode matrix)
"How do I read a whole file into a string?"       FSTREAM   (slurp)
"Is strncpy safe?"                                CSTRING   (the strncpy trap)
"How do I split a string?"                        STRING    (splitting) / SSTREAM
"Why doesn't 0.1 + 0.2 == 0.3?"                   CMATH     (comparing floats)
"What's the difference between fail and bad?"     IOS       (state flag decision table)
"How do I reset a stringstream?"                  SSTREAM   (the two-step reset)
"How do I make cout write to a socket?"           STREAMBUF (custom buffers)
"Why is my printf crashing?"                      CSTDIO    (printf is not type-safe)
"How do I print from multiple threads?"           MODERN_IO (osyncstream)
"How do I format my own type?"                    MODERN_IO (custom formatter)
"Which header do I include in my .hpp?"           MODERN_IO (iosfwd)
```

---

## STANDARD VERSION SUMMARY

```
C++11   move semantics on streams; string paths for fstream; getline; stoi/to_string;
        cbrt/hypot/round/isnan and the classification family; io_errc; scoped enums
C++14   std::quoted; ""s literals; gets removed
C++17   filesystem::path in fstream; string_view; charconv; special math functions;
        3-argument hypot; clamp
C++20   std::format; syncstream; stringstream view()/move-str(); numbers constants;
        starts_with/ends_with; lerp; bit_cast; three-way comparison
C++23   std::print/println; spanstream; string::contains; resize_and_overwrite;
        ios::noreplace; range formatting
C++26   strstream removed; println(); runtime_format
```

---

## COMPILER FLAGS WORTH USING

```
-std=c++20                     Or c++23 where the toolchain supports it
-Wall -Wextra -Wpedantic       The baseline
-Wformat=2                     Catches printf/scanf mismatches
-Wshadow -Wconversion          Catches quiet correctness bugs
-fsanitize=address,undefined   Finds the buffer and UB bugs these headers invite
-D_GLIBCXX_ASSERTIONS          libstdc++ bounds checks in debug builds
```

---

## EXTERNAL RESOURCES

- **Input/Output library**: https://en.cppreference.com/w/cpp/io
- **Strings library**: https://en.cppreference.com/w/cpp/string
- **Numerics library**: https://en.cppreference.com/w/cpp/numeric
- **C++ Core Guidelines**: https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
- **Compiler support tables**: https://en.cppreference.com/w/cpp/compiler_support

---

**Last Updated**: September 2026
