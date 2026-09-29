---
id: unique-ptr
title: unique_ptr
aliases:
- "std::unique_ptr"
type: concept
domain: D07
tier: 1
status: draft
standard: C++11
prereqs:
- "[[Ownership — Who Releases What]]"
related:
- "[[RAII]]"
- "[[shared_ptr and Reference Counting]]"
- "[[Owning vs Observing Pointers]]"
- "[[make_unique and make_shared]]"
- "[[Move Semantics]]"
- "[[Virtual Destructors]]"
- "[[Pimpl]]"
practice:
- 25
tags:
- type/concept
- domain/d07
- tier/1
- tension/safety-vs-performance
- std/c++11
- std/c++14
- std/c++17
- std/c++20
- std/c++23
created: 2026-09-29
updated: 2026-09-29
---

# unique_ptr

> [!essence]
> `unique_ptr<T>` turns "exactly one owner" from a convention someone has to remember into a property the compiler checks: its copy constructor and copy assignment are deleted outright, so the only way to hand off the object it manages is an explicit move, and its destructor releases that object automatically — on every exit path, including a thrown exception — at the same size and speed as the raw pointer it replaces.

## The Problem

[[Ownership — Who Releases What|Ownership]] already established that a resource needs exactly one party responsible for releasing it. But naming that party in a comment or a variable name doesn't make it true — the compiler doesn't read comments.

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint.** A raw pointer's type carries no marker for "I am the owner." Whether `Sensor* p` is the one party responsible for `delete p` or just an observer is a fact that lives entirely in documentation and discipline, not in anything the compiler checks.
> 2. **Consequence.** Discipline has no way to survive an early `return` or a thrown exception it didn't anticipate. A `delete` written at the bottom of a function is simply never reached if an earlier line throws — the object leaks — and nothing about the source code looks wrong until a test (or a customer) runs out of memory.
> 3. **Requirement.** The "exactly one owner" rule needs to become a property of a *type*: copying must be refused outright, so there is never a moment where two variables both believe they own the same object; transferring ownership must still be possible, but only through an operation that visibly empties the source; and release must be tied to something the compiler unwinds unconditionally — a destructor — so it fires on every exit, planned or not.
> 4. **Design.** `unique_ptr<T, Deleter = default_delete<T>>` deletes its copy constructor and copy-assignment operator, defines a move constructor and move-assignment operator that steal the managed pointer and leave the source holding `nullptr`, and calls `Deleter` on the managed pointer from its own destructor. The deleter is a **second template parameter**, not a pointer stored at run time, so for the common case — no custom deleter — there is nothing to store beyond the pointer itself.
> 5. **Price.** Baking the deleter into the type means `unique_ptr<T, D1>` and `unique_ptr<T, D2>` are unrelated types: you cannot mix "delete with `delete`" and "delete with `fclose`" pointers in one `std::vector<unique_ptr<T>>` without erasing the deleter behind a function pointer or `std::function` — which then *does* cost extra storage (see *Under the Hood*). And refusing copy outright means a `unique_ptr` cannot cross an API that insists on copying its argument, or sit in pre-C++11-style code that expects `CopyInsertable` elements.

> [!tension] safety ⟷ performance
> The zero-overhead default — one pointer, one inlined destructor call — is what [[Map — Ownership & Move Semantics|the domain's Key Idea]] means by "`unique_ptr` costs nothing at run time." Every deviation from that default (a stateful deleter, a function-pointer deleter, storing it politically through a base class) has a visible, measurable cost, shown below rather than hidden behind the same name.

## Mental Model

```mermaid
stateDiagram-v2
    [*] --> Empty: unique_ptr<T> p;
    Empty --> Owning: p = make_unique<T>(...)
    Owning --> Owning: p2 = std::move(p1)<br/>(p1 becomes Empty)
    Owning --> Empty: release()<br/>caller now owns the raw pointer
    Owning --> Empty: reset()<br/>deletes the object
    Owning --> [*]: destructor runs<br/>deletes the object
    Empty --> [*]: destructor runs<br/>(no-op)
```

> [!model] A relay baton, not a lamp you can lend
> Exactly one runner — one `unique_ptr` variable — holds the baton at a time. Passing it on requires a real hand-off (`std::move`); you cannot photocopy the baton and claim to also be carrying it, which is exactly why the copy constructor is deleted rather than merely discouraged. A runner who collapses mid-race without having passed the baton — the variable's scope ends — triggers the officials to reclaim it immediately, whether the collapse was planned (falling off the end of a block) or not (an exception unwinding through it).
> **Where it breaks:** the object being managed never moves in memory — only which variable is *entitled to release it* changes hands. And a runner who has already handed off the baton isn't merely "no longer carrying the original" the way a general moved-from object is left in an unspecified-but-valid state ([[The Moved-From State]]); `unique_ptr` spells out the exception precisely: a moved-from `unique_ptr` owns **nothing**, guaranteed — `static_cast<bool>(p) == false`.

## Mechanics

| Situation | Rule | Example |
|---|---|---|
| Construct from a raw pointer | Direct-initialization only; no implicit conversion from `T*` | `unique_ptr<Sensor> p(new Sensor);` |
| `make_unique<T>(args...)` (C++14) | Preferred over the line above: one line, no bare `new` in your code at all | `auto p = std::make_unique<Sensor>(1);` |
| Copy constructor / copy assignment | Deleted — always a compile error, not a runtime hazard | `unique_ptr<T> b = a;` ✗ |
| Move constructor / move assignment | Steals the pointer (and the deleter); the source becomes exactly null | `unique_ptr<T> b = std::move(a);` |
| `p.release()` | Returns the raw pointer and sets `p` to null; **nothing will delete it now** unless you hand it to something that will | `T* raw = p.release();` |
| `p.reset(q = nullptr)` | Deletes whatever `p` currently owns (if anything), then makes `p` own `q` | `p.reset(new T);` |
| `p.get()` | Observes the raw pointer without transferring ownership | pass to a legacy `T*`-taking API |
| `*p`, `p->member` | Dereference the managed object — single-object form only | `p->id` |
| `unique_ptr<T[]>` | `operator[]` instead of `*` / `->`; the deleter calls `delete[]` | `p[2] = 5;` |
| `unique_ptr<Derived>` → `unique_ptr<Base>` | Implicit conversion, but the result still releases through `Base*` — see *Pitfalls* | function returning a polymorphic result |
| Incomplete type `T` | Allowed to *hold*; `T` must be complete only where the deleter actually runs (destructor, `reset`, move-assignment) | the Pimpl idiom, see [[Pimpl]] |

> [!standard] A moved-from `unique_ptr` owns nothing — by name, not just by convention
> Most moved-from standard-library objects are left in a "valid but unspecified" state ([[The Moved-From State]]): you may destroy or reassign them, nothing more. `unique_ptr`'s move constructor and move-assignment operator are more specific: the Standard requires the source to hold `nullptr` afterward (cppreference, *std::unique_ptr*, move members: "`u2` no longer owns any pointer after the call"). That's why `assert(!p)` right after `q = std::move(p);` is not just customary — it's guaranteed.

> [!standard] The Standard does not guarantee `sizeof(unique_ptr<T>) == sizeof(T*)`
> cppreference says only that "a typical implementation... holds only one pointer." The compressed layout shown below is a quality-of-implementation choice every mainstream library makes, not a language rule — a `Deleter` with its own state, or one that isn't an empty class type, is exactly what breaks it, deliberately.

## Under the Hood

> [!machine] The deleter's own state — or lack of it — is the entire cost model
> Four `static_assert`s, all of which pass, observed with GCC 11.4.0, libstdc++, x86-64 Linux:
> ```cpp
> #include <memory>
>
> struct Widget {};
> using FnPtr = void(*)(Widget*);
> struct StatelessDeleter { void operator()(Widget* p) const { delete p; } };
> struct StatefulDeleter  { int tag = 0; void operator()(Widget* p) const { delete p; } };
>
> static_assert(sizeof(std::unique_ptr<Widget>) == sizeof(Widget*));                        // ①
> static_assert(sizeof(std::unique_ptr<Widget, StatelessDeleter>) == sizeof(Widget*));       // ②
> static_assert(sizeof(std::unique_ptr<Widget, FnPtr>) == 2 * sizeof(Widget*));              // ③
> static_assert(sizeof(std::unique_ptr<Widget, StatefulDeleter>) == 2 * sizeof(Widget*));     // ④
> ```
> ① The default deleter is an empty class with no data of its own — libstdc++ folds it into the same storage as the pointer, the way empty base optimization would. ② A hand-written *stateless* functor gets the identical treatment: emptiness, not identity, is what's rewarded. ③ A function pointer is itself a full pointer-sized value that has to be *stored*, not just a type to instantiate — the `unique_ptr` grows to two pointers. ④ A functor with even one `int` member can no longer be folded away, so it costs a second pointer-sized slot too (padded up to alignment). Nothing here is free by magic: the "zero-overhead" case is specifically the case where there is no deleter *state*, only deleter *behavior* the compiler already knows at compile time.

```text
 unique_ptr<Widget>                       unique_ptr<Widget, StatefulDeleter>
┌───────────────────────┐                ┌───────────────────────┐
│ ptr ●─────────────────┼──▶ Widget      │ ptr ●─────────────────┼──▶ Widget
└───────────────────────┘                │ deleter{ tag }         │
   8 bytes (x86-64)                      └───────────────────────┘
   (default_delete has no                    16 bytes (x86-64)
    state — nothing to store)                 (the deleter's own data rides along)
```

## In Code

**1 · Copy refused, move accepted, a factory returns by value**

```cpp
// cc: ill-formed
#include <memory>
struct Sensor { int id; };
int main() {
    std::unique_ptr<Sensor> a = std::make_unique<Sensor>(1);
    std::unique_ptr<Sensor> b = a;   // ① copy constructor is deleted
}
```
1. This is a compile error before the program ever runs — "exactly one owner" is enforced at compile time, not discovered at a crash months later.

```cpp
#include <memory>
#include <iostream>

struct Sensor { int id; };

std::unique_ptr<Sensor> make_calibrated(int id) {   // ①
    auto p = std::make_unique<Sensor>(id);
    p->id += 1000;
    return p;                                        // ②
}

int main() {
    auto s = make_calibrated(7);
    std::cout << s->id << '\n';
}
// expect: 1007
```
1. The function's return type states, in the signature, that callers receive ownership — no comment required.
2. Returning a local `unique_ptr` by value moves it (the compiler treats a named local in a `return` as an rvalue when eligible); nothing is copied, and `p` is never used again after this line.

**2 · The twin-`new` leak, and why `make_unique` sidesteps the question entirely**

**✗ Two raw `new`s passed as arguments (historically fragile):**
```cpp
#include <memory>
#include <iostream>
#include <stdexcept>

struct Sensor {
    inline static int alive = 0;
    Sensor() { ++alive; }
    ~Sensor() { --alive; }
};
struct Alarm { explicit Alarm(int) { throw std::runtime_error("boom"); } };  // ①

void arm(std::unique_ptr<Sensor>, std::unique_ptr<Alarm>) {}

int main() {
    try {
        arm(std::unique_ptr<Sensor>(new Sensor), std::unique_ptr<Alarm>(new Alarm(1)));  // ②
    } catch (const std::runtime_error&) {
        std::cout << "caught; Sensor::alive == " << Sensor::alive << '\n';
    }
}
// expect: caught; Sensor::alive == 0
```
1. `Alarm`'s constructor always throws, to force the failure path.
2. **Before C++17**, the order in which the two arguments were evaluated was completely unspecified — a compiler was free to run both raw `new`s before wrapping either in a `unique_ptr`, in which case `Sensor` would leak when `Alarm`'s constructor threw. **Since C++17** (P0145, tightening `[intro.execution]`), each argument's initialization is *indeterminately sequenced* relative to the others — one argument finishes entirely (allocation *and* the wrap into its `unique_ptr`) before the next one starts — so the leak window is closed by the language itself. GCC 11.4.0 (`-std=c++20`, x86-64 Linux) prints `Sensor::alive == 0` here, confirming no leak on this toolchain; the point of *Evolution* below is that this is now a language guarantee, not a lucky compiler choice.

**✓ `make_unique` (write this regardless of which standard guarantees what):**
```cpp
#include <memory>
#include <iostream>
#include <stdexcept>

struct Sensor {
    inline static int alive = 0;
    Sensor() { ++alive; }
    ~Sensor() { --alive; }
};
struct Alarm { explicit Alarm(int) { throw std::runtime_error("boom"); } };

void arm(std::unique_ptr<Sensor>, std::unique_ptr<Alarm>) {}

int main() {
    try {
        auto s = std::make_unique<Sensor>();
        auto a = std::make_unique<Alarm>(1);   // ① throws — but nothing was ever a bare `new`
        arm(std::move(s), std::move(a));
    } catch (const std::runtime_error&) {
        std::cout << "caught; Sensor::alive == " << Sensor::alive << '\n';
    }
}
// expect: caught; Sensor::alive == 0
```
1. There is no bare `new` here to leak in the first place, on any standard — the safety argument for `make_unique` never depended on the C++17 sequencing fix from example 2's ✗ version, which is why it remained the recommended default even after that fix shipped.

**3 · `unique_ptr` of an incomplete type: the Pimpl idiom**

```cpp
#include <memory>
#include <cstdio>

class Engine {                       // ordinarily the class declaration below
public:                              // lives in engine.h and the definitions
    Engine();                        // that follow live in engine.cpp — shown
    ~Engine();                       // ① declared here; Impl is still incomplete
    void run();                      // combined into one file so it compiles standalone
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;     // ② ok: unique_ptr can hold an incomplete type
};

struct Engine::Impl {
    int rpm = 0;
    void spin() { rpm += 100; std::printf("rpm=%d\n", rpm); }
};
Engine::Engine() : impl_(std::make_unique<Impl>()) {}
Engine::~Engine() = default;         // ③ Impl is complete HERE — where the deleter actually runs
void Engine::run() { impl_->spin(); }

int main() {
    Engine e;
    e.run();
}
// expect: rpm=100
```
1. Declaring `~Engine()` (even to later `= default` it) defers the point where the compiler must generate the destructor's body — and therefore instantiate `default_delete<Impl>::operator()` — until that definition, rather than immediately after the class.
2. `unique_ptr<Impl>` compiles here even though `Impl` has only been forward-declared: the class template itself never needs `sizeof(Impl)`.
3. Only *here*, after `struct Engine::Impl` is fully defined, is `Impl` complete — exactly where the destructor's body, and thus the deleter call, is instantiated. In real code this line lives in `engine.cpp`, downstream of `Impl`'s definition, while the class declaration lives in `engine.h` — see *Pitfalls* for what happens when the split is done wrong.

## Pitfalls

> [!trap] The deleter is part of the type — mixing deleters means erasing them
> `unique_ptr<Widget>` and `unique_ptr<Widget, StatelessDeleter>` cannot sit in the same `std::vector`, even though both ultimately call `delete`. A container of "whatever cleanup this particular object needs" has to erase the deleter's type — a function pointer or `std::function<void(Widget*)>` — paying exactly the extra storage measured in *Under the Hood*. [[shared_ptr and Reference Counting|shared_ptr]] sidesteps this by type-erasing its deleter unconditionally, which is part of why it's never pointer-sized.

> [!ub] Deleting a derived object through a non-virtual base destructor
> `unique_ptr<Derived>` converts implicitly to `unique_ptr<Base>`, but the *converted* object still releases through `Base*` using `default_delete<Base>` — `delete` on a `Base*` whose most-derived type is `Derived`. If `~Base()` isn't `virtual`, this is undefined behavior (`[expr.delete]`, the same clause [[Ownership — Who Releases What|Ownership]] cites for a mismatched `delete`): typically `Derived`'s members and destructor never run, and the allocator sees the wrong object size.
> ```cpp
> // cc: ub
> #include <memory>
> struct BadBase { ~BadBase() {} };                       // no virtual destructor
> struct BadDerived : BadBase { int extra = 0; ~BadDerived() {} };
> int main() {
>     std::unique_ptr<BadBase> p = std::make_unique<BadDerived>();
> }   // p's destructor calls delete through BadBase* — UB
> ```
> The fix is the one shown in example 3's cousin above: make the base destructor `virtual`, as [[Virtual Destructors]] covers in full.

> [!trap] `release()` without a catcher leaks exactly like a raw pointer would
> `p.release()` hands you the raw pointer and forgets it *immediately* — nothing will call `delete` on it unless you store it in something that will. `p.release();` alone, with the return value discarded, is a leak with extra steps (Primer §12.1.5, p. 471, calls the same pattern out directly). Prefer `p.reset(...)` when you mean "delete the old one and take a new one"; reach for `release()` only when handing raw ownership to a non-`unique_ptr` API that documents it will take over.

> [!trap] Forgetting the out-of-line destructor breaks Pimpl at the call site, not at the definition
> Omit `~Engine();` from the header in example 3, and `Engine`'s destructor is implicitly defined wherever it is first needed — which, for an inline implicit member, can be a *different translation unit* than the one that defines `Impl`. Compiling a caller that only includes `engine.h` then fails inside `<memory>` itself (GCC 11.4.0): `error: invalid application of 'sizeof' to incomplete type 'Engine::Impl'`, reported from `default_delete<Engine::Impl>::operator()`. The header alone looks correct; the error surfaces in code that never even mentions `Impl`.

## Evolution

| Standard | Change | Why |
|---|---|---|
| C++98 | `auto_ptr` attempts exclusive ownership by transferring on *copy* | Superseded — see [[Ownership — Who Releases What]] *Evolution* for why a copy that secretly moves cannot work |
| **C++11** | `unique_ptr<T, Deleter>` introduced: deleted copy, move-only via [[Rvalue References|rvalue references]] | Needed a type-safe, zero-overhead exclusive-ownership handle the compiler — not the programmer — enforces |
| C++14 | `make_unique<T>(args...)` and `make_unique<T[]>(n)` added (N3656) | `make_shared` already existed; `unique_ptr` deserved the same "no bare `new` in your code" factory |
| C++17 | Function-call argument initializations become indeterminately sequenced (P0145) | Closes the twin-`new` leak window in example 2 even for code that never adopted `make_unique` |
| C++20 | `make_unique_for_overwrite<T>()` added | Skips the default value-initialization `make_unique` performs, for buffers about to be overwritten anyway |
| C++23 | `unique_ptr` operations become `constexpr` (P2273) | Usable inside compile-time evaluation, matching `constexpr` support added elsewhere in `<memory>` |

## Connections

- **Prerequisites:** [[Ownership — Who Releases What]] — names the headcount rule this note enforces in a type.
- **Enables:** [[shared_ptr and Reference Counting]] (the shared-ownership contrast) · [[make_unique and make_shared]] · [[Choosing a Smart Pointer]] · [[Exception Safety Guarantees]].
- **Siblings:** [[Owning vs Observing Pointers]] · [[RAII]] · [[Move Semantics]].
- **Hazards:** [[Virtual Destructors]] (the non-virtual-base-destructor trap above) · [[Pimpl]] (the incomplete-type pattern in example 3) · [[The Moved-From State]] (contrast with `unique_ptr`'s stronger guarantee).
- **Domain:** [[Map — Ownership & Move Semantics]].
- **Practice:** *Continuum #25 Smart Pointer Refactor Lab* — replace every raw `new`/`delete` with `unique_ptr` and `make_unique`, and note every spot a custom deleter is genuinely required.

## Check Yourself

> [!quiz]- Why does `unique_ptr` *delete* its copy constructor instead of just documenting "don't copy this"?
> Because documentation isn't checked by the compiler. A convention lives in a comment or a name and survives only as long as everyone reading the code remembers it; a deleted copy constructor turns any attempt to copy into a compile error, catching the mistake before the program exists, not after it double-frees in production.

> [!quiz]- Why can `unique_ptr<Impl>` be declared as a class member while `Impl` is only forward-declared, when `shared_ptr` constructed directly from a raw pointer generally cannot?
> `unique_ptr` needs `T` complete only at the specific points that actually invoke the deleter — the destructor, `reset()`, and move-assignment — and a class can defer all three past the point where `Impl` becomes complete (the Pimpl idiom). `shared_ptr`, by contrast, captures a type-erased deleter *at construction time* from a raw pointer, which requires `sizeof(T)` right then; it only tolerates incompletion when it's copy-constructed or destroyed from another `shared_ptr` that already captured a complete-type deleter.

> [!quiz]- Predict: before any standard fix, what could go wrong with `handle(std::unique_ptr<A>(new A), std::unique_ptr<B>(new B))` if constructing `B` throws — and does the same risk exist in the `make_unique` version?
> Before C++17, the two arguments' evaluation could interleave enough that both raw `new`s ran before either was wrapped in a `unique_ptr`; if `new B` (or its constructor) then threw, the already-allocated `A` had no owner yet and leaked. The `make_unique` version has no bare `new` anywhere in user code, so there's no window in which an allocated object is unowned — the question doesn't arise regardless of standard version.

> [!quiz]- Why does `sizeof(std::unique_ptr<Widget, StatelessDeleter>)` equal `sizeof(Widget*)`, but `sizeof(std::unique_ptr<Widget, StatefulDeleter>)` does not, even though both deleters are ordinary structs with an `operator()`?
> `StatelessDeleter` has no data members, so the library's internal pointer-plus-deleter storage can fold it away — there's nothing to store beyond a type the compiler already knows how to call. `StatefulDeleter` carries an `int` member that differs from one instance to the next, so that value must physically exist somewhere at run time; it occupies its own pointer-sized slot alongside the managed pointer.

## Sources

- Primer §12.1.5 "unique_ptr" (pp. 470–471): the operations table this note's *Mechanics* section is built on, `release`/`reset` semantics, and the "WRONG: `p2.release()` alone leaks" caution cited in *Pitfalls*.
- Primer §12.2.1 "Dynamic Arrays", Table 12.6 (p. 480): `unique_ptr<T[]>` supports `operator[]` but not `operator*`/`operator->`.
- Tour §15.2.1 "unique_ptr and shared_ptr" (pp. 197–199): `unique_ptr` as "a lightweight mechanism with no space or time overhead compared to correct use of a built-in pointer"; `make_unique` introduced as the safer alternative to a bare `new` handed to a smart pointer.
- cppreference, *std::unique_ptr*: incomplete-type support and its limits, the base-class-conversion UB warning, and the moved-from-is-null guarantee: https://en.cppreference.com/w/cpp/memory/unique_ptr
- cppreference, *std::make_unique, std::make_unique_for_overwrite*: signatures, C++14/C++20 history, and the value- vs default-initialization distinction for arrays: https://en.cppreference.com/w/cpp/memory/unique_ptr/make_unique
- cppreference, *Order of evaluation*: the C++17 change (rule 14) that makes function-argument initializations indeterminately sequenced rather than fully unspecified: https://en.cppreference.com/w/cpp/language/eval_order
- P0145R3, *Refining Expression Evaluation Order for Idiomatic C++* (the paper behind the C++17 change cited above): https://wg21.link/p0145r3
- Draft standard `[unique.ptr]` (the class template's normative definition) and `[expr.delete]` (delete through an incomplete or non-virtually-destructible base is undefined behavior): https://eel.is/c++draft/unique.ptr · https://eel.is/c++draft/expr.delete
