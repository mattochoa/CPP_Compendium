---
id: hdr-chrono
title: Header — chrono
aliases:
- <chrono>
- std::chrono
- steady_clock
- duration_cast
- chrono literals
type: header
domain: HDR
tier: 2
status: draft
standard: C++11
prereqs:
- "[[chrono — Durations, Clocks, Time Points]]"
related:
- "[[chrono — Durations, Clocks, Time Points]]"
- "[[Benchmarking Correctly]]"
- "[[Threads — thread and jthread]]"
- "[[format and print]]"
tags:
- type/header
- domain/hdr
- tier/2
- header/chrono
- tension/safety-vs-performance
- tension/compile-time-vs-run-time
created: 2026-09-23
updated: 2026-09-23
header: <chrono>
---

# Header — chrono

> [!essence]
> **`<chrono>`** puts time into the type system. A **duration** is a count of ticks with its unit (`ms`, `s`, `h`) carried by its type. A **time_point** is a duration measured from a clock's epoch. A **clock** says which epoch and whether it can jump. Units convert automatically when no precision is lost, and only with an explicit cast when it is. A seconds-versus-milliseconds bug therefore becomes a compile error instead of a production incident.

> [!standard] Versions
> C++11 (durations, time points, `system_clock`/`steady_clock`/`high_resolution_clock`) / C++14 (literals `h min s ms us ns`, constexpr arithmetic) / C++17 (`floor`/`ceil`/`round`/`abs`, `treat_as_floating_point_v`) / C++20 (calendar, time zones, `hh_mm_ss`, `days`/`weeks`/`months`/`years`, `utc`/`tai`/`gps`/`file_clock`, `clock_cast`, formatting and `operator<<`, literals `d` and `y`) / C++26 (`std::hash` specializations)

## Class Family

```text
                  duration<Rep, Period>          "how long":  count() ticks × Period seconds
                    ├── nanoseconds … hours      C++11 aliases
                    └── days weeks months years  C++20 aliases
  Clock  ──now()──▶ time_point<Clock, Duration>  "when":      duration since Clock's epoch
    ├── steady_clock            monotonic, never jumps → measuring intervals, timeouts
    ├── system_clock            wall clock, can jump   → timestamps, calendar, to_time_t
    ├── high_resolution_clock   alias of one of the above (implementation-defined)
    └── utc / tai / gps / file_clock                  → C++20
  Calendar (C++20): year / month / day / weekday / year_month_day / hh_mm_ss / zoned_time
```

## Quick Reference

```cpp
// cc: fragment
// ═══════════════════════════════════════════════════════════════════════════
// DURATIONS  (namespace std::chrono)
// ═══════════════════════════════════════════════════════════════════════════
std::chrono::milliseconds ms{250};      // Rep value   | 250 ticks of 1/1000 s | Aliases: nanoseconds … hours
std::chrono::duration<double> secs{1.5};// double      | Fractional seconds    | Floating Rep: conversions are implicit
std::chrono::duration<int, std::ratio<60>> mins{3};    // Custom period (= minutes)
d.count()                               // none        | Raw tick count        | Rep, NOT seconds; unit is in the type
std::chrono::seconds s = ms;            // ✗ ERROR     | Lossy implicit conv.  | ms → s truncates: needs a cast
std::chrono::milliseconds m = s;        // ✓ OK        | Lossless implicit     | s → ms is exact
std::chrono::duration_cast<seconds>(ms) // target type | Truncating convert    | Toward zero
std::chrono::floor<seconds>(ms)         // target type | Round down            | C++17
std::chrono::ceil<seconds>(ms)          // target type | Round up              | C++17
std::chrono::round<seconds>(ms)         // target type | Nearest, ties → even  | C++17 (integral target)
std::chrono::abs(d)                     // duration    | Absolute value        | C++17
d1 + d2, d1 - d2, d * n, d / n, d1 / d2, d % n        // Arithmetic; d1/d2 is a plain number
d1 < d2, d1 == d2, d1 <=> d2            // Compare across units (converted to a common type) | <=> C++20
Duration::zero() / min() / max()        // Special values
std::chrono::days / weeks / months / years            // C++20 aliases (months/years are average lengths)

// ═══════════════════════════════════════════════════════════════════════════
// LITERALS  (C++14)  using namespace std::chrono_literals;
// ═══════════════════════════════════════════════════════════════════════════
2h   30min   15s   250ms   100us   50ns // → hours, minutes, seconds, milliseconds, microseconds, nanoseconds
1.5s                                    // → seconds with an unspecified floating-point Rep
23d  2026y                              // C++20: day, year (calendar types, not durations!)

// ═══════════════════════════════════════════════════════════════════════════
// CLOCKS & TIME POINTS
// ═══════════════════════════════════════════════════════════════════════════
auto t0 = std::chrono::steady_clock::now();   // time_point<steady_clock>
Clock::is_steady                        // constexpr   | Monotonic?            | steady_clock: always true
t1 - t0                                 // tp - tp     | → duration            | Same clock only
t0 + 5s,  t0 - 5s                       // tp ± dur    | → time_point          |
tp.time_since_epoch()                   // none        | → duration            | Epoch is clock-specific
std::chrono::time_point_cast<seconds>(tp)             // Change a time_point's duration type (truncating)
std::chrono::floor<seconds>(tp) / ceil / round        // C++17 for time_points too
std::chrono::system_clock::to_time_t(tp)              // → std::time_t for <ctime> printing
std::chrono::system_clock::from_time_t(t)             // ← std::time_t
std::chrono::sys_seconds / sys_days     // C++20 aliases: time_point<system_clock, seconds / days>
std::chrono::clock_cast<utc_clock>(tp)  // Convert between clocks                 | C++20

// ═══════════════════════════════════════════════════════════════════════════
// CALENDAR, TIME OF DAY, TIME ZONES  (C++20)
// ═══════════════════════════════════════════════════════════════════════════
2026y/std::chrono::September/23         // year_month_day via operator/ (also 23d/9/2026y)
ymd.ok()                                // Valid date?   (2026y/2/30 → false)
std::chrono::sys_days{ymd}              // Date → time_point (day precision)
std::chrono::weekday{sys_days{ymd}}     // Day of the week
std::chrono::year_month_day_last{2026y/std::chrono::February/std::chrono::last}   // last day of month
std::chrono::hh_mm_ss{d}                // Split a duration: hours() minutes() seconds() subseconds()
std::chrono::zoned_time{"America/Chicago", sys_now}   // Wall time in a zone (needs tz database)
std::chrono::current_zone(), locate_zone("Europe/Paris")
std::format("{:%Y-%m-%d %H:%M}", tp)    // Format time points / durations  (<format>)
std::cout << 250ms                      // Prints "250ms"                   | C++20
```

## Patterns

### Measuring How Long Something Takes
```cpp
#include <chrono>
#include <iostream>
#include <thread>

int main() {
    using namespace std::chrono;
    const auto start = steady_clock::now();            // steady: can't jump backwards
    std::this_thread::sleep_for(milliseconds(20));      // the work being timed
    const auto elapsed = steady_clock::now() - start;   // a duration in clock ticks
    const auto ms = duration_cast<milliseconds>(elapsed).count();
    std::cout << (ms >= 20 ? "took at least 20 ms" : "too fast?!") << '\n';
}
// expect: took at least 20 ms
```

### Converting Between Units
```cpp
#include <chrono>
#include <iostream>

int main() {
    using namespace std::chrono;
    const milliseconds total{7'384'125};
    const auto h = duration_cast<hours>(total);                   // truncates toward zero
    const auto m = duration_cast<minutes>(total - h);
    const auto s = duration_cast<seconds>(total - h - m);
    const auto rest = total - h - m - s;
    std::cout << h.count() << "h " << m.count() << "m " << s.count() << "s "
              << rest.count() << "ms\n";
}
// expect: 2h 3m 4s 125ms
// C++20: std::chrono::hh_mm_ss{total} does this split for you.
```

### Readable Timeouts with Literals (C++14)
```cpp
#include <chrono>
#include <iostream>

using namespace std::chrono_literals;

void configure(std::chrono::milliseconds poll, std::chrono::seconds timeout) {
    std::cout << poll.count() << " ms / " << timeout.count() << " s\n";
}

int main() {
    configure(250ms, 30s);                              // units are visible at the call site
    configure(1s, 2min);                                // s → ms and min → s convert losslessly
}
// expect: 250 ms / 30 s
// expect: 1000 ms / 120 s
```

### Fractional Seconds for Reporting
```cpp
#include <chrono>
#include <iostream>

int main() {
    using namespace std::chrono;
    const microseconds measured{1'234'567};
    const duration<double> secs = measured;              // floating Rep: implicit, no cast
    const duration<double, std::milli> ms = measured;
    std::cout << secs.count() << " s = " << ms.count() << " ms\n";
}
// expect: 1.23457 s = 1234.57 ms
```

### Rounding Instead of Truncating (C++17)
```cpp
#include <chrono>
#include <iostream>

int main() {
    using namespace std::chrono;
    const milliseconds t{2'700};
    std::cout << duration_cast<seconds>(t).count() << ' '    // 2  (truncate)
              << floor<seconds>(t).count() << ' '            // 2
              << ceil<seconds>(t).count() << ' '             // 3
              << round<seconds>(t).count() << '\n';          // 3
}
// expect: 2 2 3 3
```

### A Deadline Loop (retry until a time limit)
```cpp
#include <chrono>
#include <functional>
#include <thread>

bool retry_until(const std::function<bool()>& attempt, std::chrono::milliseconds budget) {
    const auto deadline = std::chrono::steady_clock::now() + budget;   // a time_point
    while (std::chrono::steady_clock::now() < deadline) {
        if (attempt()) return true;
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
    return false;
}
// Compute the deadline once. Re-adding the budget on every retry would stretch the limit.
```

### A Fixed-Rate Loop that Doesn't Drift
```cpp
#include <chrono>
#include <iostream>
#include <thread>

int main() {
    using namespace std::chrono;
    const auto period = milliseconds(10);
    auto next = steady_clock::now();
    int ticks = 0;
    for (int i = 0; i < 5; ++i) {
        ++ticks;                                       // the periodic work
        next += period;                                // schedule from the plan, not from "now"
        std::this_thread::sleep_until(next);           // absorbs the work's own duration
    }
    std::cout << ticks << " ticks\n";
}
// expect: 5 ticks
```

### Printing the Current Wall-Clock Time (C++11/14/17)
```cpp
#include <chrono>
#include <ctime>
#include <iomanip>
#include <iostream>

int main() {
    const auto now = std::chrono::system_clock::now();          // wall clock, NOT steady
    const std::time_t t = std::chrono::system_clock::to_time_t(now);
    std::tm local{};
#if defined(_WIN32)
    localtime_s(&local, &t);                                     // thread-safe variants
#else
    localtime_r(&t, &local);
#endif
    std::cout << std::put_time(&local, "%Y-%m-%d %H:%M:%S") << '\n';   // e.g. 2026-09-23 14:05:09
}
// C++20: std::cout << std::format("{:%F %T}", std::chrono::floor<std::chrono::seconds>(now));
```

### Dates Without a Calendar Library (C++20)
```cpp
// cc: std=c++20 remote
#include <chrono>
#include <iostream>

int main() {
    using namespace std::chrono;
    const year_month_day due{2026y / September / 23};
    const year_month_day later{sys_days{due} + days{30}};         // arithmetic on day-precision time points
    std::cout << static_cast<int>(later.year()) << '-'
              << static_cast<unsigned>(later.month()) << '-'
              << static_cast<unsigned>(later.day()) << ' '
              << (2026y / February / 29).ok() << '\n';            // not a leap year → 0
}
// expect: 2026-10-23 0
```

## Key Concepts

### The Unit Lives in the Type
`count()` returns a bare number. Its meaning comes from the duration's `Period` (`std::milli`, `std::ratio<60>`, …). Keep values as durations for as long as possible, and call `count()` only at the edge (printing, a C API). A function parameter of type `std::chrono::milliseconds` accepts `2s` and `500ms` alike.

### Implicit Conversion Only When Lossless
Converting to a finer unit (s → ms) is implicit because it is exact. Converting to a coarser integral unit (ms → s) would truncate, so it requires `duration_cast` (truncates toward zero) or, since C++17, `floor`/`ceil`/`round`. Floating-point `Rep` converts implicitly both ways.

### `steady_clock` for Intervals, `system_clock` for Timestamps
`system_clock` follows the wall clock, which NTP, daylight-saving changes or the user can move backwards or forwards. Measuring an interval with it can give negative or wildly wrong results. `steady_clock` is monotonic: use it for timing, timeouts and scheduling.

### `high_resolution_clock` Is Just an Alias
It is typically `steady_clock` or `system_clock`, depending on the library, so its steadiness varies by platform. Prefer naming `steady_clock` explicitly.

### Time Points Are Tied to Their Clock
You cannot subtract a `system_clock::time_point` from a `steady_clock::time_point`: the types differ, so it doesn't compile. Their epochs are unrelated. C++20's `clock_cast` converts between clocks that define a relationship.

### Overflow Is Silent
The standard only guarantees minimum `Rep` widths: `nanoseconds` at least 64 bits (about ±292 years), down to `seconds` at least 35 bits and `hours` at least 23. Mainstream libraries use 64-bit integers for all of them. Multiplying or casting huge values can still overflow the `Rep`, and signed overflow is undefined behavior. Keep units coarse when the magnitude is large.

### `sleep_for` Sleeps *At Least* That Long
The OS may wake a thread later than requested (scheduler granularity is often 1–16 ms on desktop systems). For periodic work, schedule against absolute `time_point`s with `sleep_until` so the lateness doesn't accumulate.

### `months` and `years` Are Averages
`std::chrono::months` is 1/12 of an average Gregorian year (2,629,746 s), so it is not a calendar month. For "one month later", use calendar arithmetic on `year_month_day` (C++20).

## Best Practices

1. **Pass durations, not integers**: `void wait(std::chrono::milliseconds)` instead of `void wait(int ms)`
2. **Use `steady_clock`** for every elapsed-time measurement and timeout
3. **Write literals** (`250ms`, `30s`) in C++14 and later; they make units visible at the call site
4. **Call `count()` last**, only when leaving the chrono type system
5. **Use `floor`/`ceil`/`round` (C++17)** when truncation toward zero isn't what you mean
6. **Compute deadlines once** as time points; compare `now() < deadline`
7. **Use `sleep_until` for periodic loops** to avoid drift
8. **Use `duration<double>`** for human-readable reports of fractional seconds
9. **Don't mix clocks**; convert with `clock_cast` (C++20) or go through `time_t`
10. **Prefer C++20 calendar and `std::format`** over `<ctime>` for dates when available

## Related Headers

```cpp
#include <chrono>              // durations, clocks, time points, calendar (C++20), time zones (C++20)
#include <thread>              // std::this_thread::sleep_for / sleep_until
#include <ratio>               // std::milli, std::micro, std::ratio<N, D>: duration periods
#include <ctime>               // std::time_t, std::tm, std::strftime, std::localtime
#include <iomanip>             // std::put_time (pre-C++20 formatting)
#include <format>              // C++20: std::format("{:%F %T}", tp)
#include <condition_variable>  // wait_for / wait_until take chrono durations and time points
#include <mutex>               // timed_mutex::try_lock_for / try_lock_until
```

## Connections

- **Hub:** [[Map — Standard Headers]]
- **Concept notes (the why behind this card):** [[chrono — Durations, Clocks, Time Points]] · [[Benchmarking Correctly]] · [[Strong Types]] · [[format and print]]
- **Sibling cards:** [[Header — thread and stop_token]] · [[Header — atomic]] · [[Header — condition_variable]]
- **Practice:** [[Kit — Background Worker (C++14-17)]] (`steady_clock`-based `PeriodicWorker`) · *Continuum #32 Performance Profiling & Optimization Challenge*

## Sources

- Tour §16.2 "Time" (p. 214): durations, clocks and C++20 calendar types from the language's designer.
- Pikus ch. 2 "Performance Measurements": timing code correctly and why wall clocks mislead.
- cppreference / web, *`<chrono>`*: https://en.cppreference.com/w/cpp/header/chrono
- cppreference / web, *`std::chrono::duration`* · *`steady_clock`*: https://en.cppreference.com/w/cpp/chrono/duration · https://en.cppreference.com/w/cpp/chrono/steady_clock
- Howard Hinnant, *date* library documentation (the design that became C++20 calendar/time zones): https://howardhinnant.github.io/date/date.html
