---
id: virtual-destructors
title: Virtual Destructors
aliases:
- non-virtual destructor
- delete through base pointer
type: pitfall
domain: D08
tier: 1
status: draft
standard: C++98
prereqs:
- "[[Virtual Dispatch — vptr and vtable]]"
- "[[Destructors]]"
related:
- "[[Abstract Classes and Interfaces]]"
- "[[Object Slicing]]"
- "[[unique_ptr]]"
- "[[Rule of Zero, Three and Five]]"
- "[[Sanitizers — ASan, UBSan, TSan]]"
practice:
- 18
tags:
- type/pitfall
- domain/d08
- tier/1
- tension/safety-vs-performance
- std/c++98
created: 2026-09-29
updated: 2026-09-29
---

# Virtual Destructors

> [!essence]
> Deleting a derived object through a pointer to its base is **undefined behavior** unless the base's destructor is **virtual**. Without `virtual`, `delete` is compiled once, against the pointer's *static* type: it runs only that type's destructor and frees only that type's size, no matter what the pointer actually points at. A base class meant to be deleted polymorphically needs a virtual destructor; a base class that must never be deleted that way is safer with no public destructor at all.

## Symptom

The bug hides well, because the visible part of the object still looks torn down:

- A derived class's own resources — a buffer, a file handle, a second base in a diamond — are **never released**. `~Derived()`'s body simply never runs. Small leaks accumulate quietly; long-running services notice only after hours or days.
- Nothing crashes at the point of the mistake. The program looks fine until whatever `~Derived()` would have released — memory, a handle, a lock — runs out or is needed again elsewhere.
- It survives `std::unique_ptr` and `std::shared_ptr` untouched: the smart pointer still calls `delete` on a pointer of the *base's* type, so wrapping the raw pointer does not, by itself, fix anything.
- Compiler warnings exist and are cheap to enable, yet this remains one of the most common inheritance mistakes in real codebases, because a class with no obvious resources ("just some `int`s and a `vector`") *seems* safe to leave non-virtual — until a later change adds one.

## Root Cause

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint.** A `delete p;` expression is compiled once, at a point where the compiler knows only `p`'s *static* type. The object `p` happens to point at, at run time, may be of a *derived* type the compiler never sees at that call site.
> 2. **Consequence.** If destruction were resolved the way an ordinary (non-virtual) function call is — baked in against the static type — `delete p` would always run the static type's destructor and free a block sized for the static type, whatever the dynamic type actually is.
> 3. **Requirement.** Destroying an object correctly through a pointer to any of its bases needs the same thing every other dynamic-type decision needs: something reachable from the object itself, resolved at the moment of the call, not at compile time.
> 4. **Design.** A virtual destructor is dispatched exactly like any other virtual function ([[Virtual Dispatch — vptr and vtable]]): the vtable carries a *deleting destructor* slot that runs the destructor chain for the object's real dynamic type and then frees the correctly sized block. `delete p` through a virtual destructor reads that slot from `p`'s own vptr.
> 5. **Price.** Without that slot, the compiler has nothing to consult but `p`'s static type, and the Standard makes the result explicit: *"the static type shall have a virtual destructor or the behavior is undefined"* — `[expr.delete]` ¶3, https://eel.is/c++draft/expr.delete#3. Every polymorphic base pays one vtable slot for this; a base nobody will ever delete through pays nothing, if its destructor stays out of the vtable entirely (*Prevention Rules*).

```text
 NON-VIRTUAL ~Base()                          VIRTUAL ~Base()
 Sensor* p = new TempSensor;                  Sensor* p = new TempSensor;
 delete p;                                    delete p;
   │                                            │
   │ compiled against p's STATIC type:          │ p's vptr → vtable → deleting-dtor slot
   │  · call Sensor::~Sensor directly           │  · runs ~TempSensor() first (real dynamic type)
   │  · free sizeof(Sensor) bytes               │  · then chains to ~Sensor()
   ▼                                            │  · frees sizeof(TempSensor) bytes — correct
 ~TempSensor() never runs.                     ▼
 history[] leaks. The freed block            Both parts torn down; the freed block
 is the wrong size for what was              matches what was actually allocated.
 actually allocated — see Detection.
```

The static/dynamic mismatch is exactly the one [[Object Slicing]] exploits on the *copy* side; here it strikes on the *destruction* side of the same value/identity tension named in [[Map — Inheritance & Polymorphism]].

## Minimal Reproduction

**1 · Raw `delete` through a non-virtual base pointer**

```cpp
// cc: ub
#include <iostream>

struct Sensor {
    Sensor() { std::cout << "Sensor ctor\n"; }
    ~Sensor() { std::cout << "Sensor dtor\n"; }               // ① not virtual
    virtual void poll() const { std::cout << "Sensor::poll\n"; }
};

struct TempSensor : Sensor {
    double* history;
    TempSensor() : history(new double[100]) { std::cout << "TempSensor ctor\n"; }
    ~TempSensor() { std::cout << "TempSensor dtor\n"; delete[] history; }  // ② never runs
    void poll() const override { std::cout << "TempSensor::poll\n"; }
};

int main() {
    Sensor* p = new TempSensor();
    p->poll();
    delete p;                                                  // ③ UB: Sensor::~Sensor only
}
```
1. `Sensor` has a virtual function (`poll`), so it is polymorphic, but its destructor is an ordinary, non-virtual one.
2. `TempSensor::~TempSensor` — and the `delete[]` that would free `history` — is exactly the code this bug skips.
3. `p`'s static type is `Sensor`, so `delete p` is compiled as a direct call to `Sensor::~Sensor` followed by a deallocation sized for `Sensor`. Observed on GCC 11.4, x86-64 Linux (this vault's toolchain): the program prints `Sensor ctor`, `TempSensor ctor`, `TempSensor::poll`, `Sensor dtor` — `TempSensor dtor` never appears, and `history` is never freed.

**2 · The same mistake through `std::unique_ptr`**

```cpp
// cc: ub
#include <memory>
#include <iostream>

struct Sensor {
    ~Sensor() { std::cout << "Sensor dtor\n"; }
    virtual void poll() const {}
};
struct TempSensor : Sensor {
    double* history;
    TempSensor() : history(new double[100]) {}
    ~TempSensor() { std::cout << "TempSensor dtor\n"; delete[] history; }
    void poll() const override {}
};

int main() {
    std::unique_ptr<Sensor> s = std::make_unique<TempSensor>();  // ① Sensor's deleter stores a Sensor*
    s->poll();
}   // ② ~unique_ptr() calls delete on that Sensor* — same UB, no raw delete in sight
```
1. `std::unique_ptr<Sensor>`'s deleter is `std::default_delete<Sensor>`: it knows only `Sensor*`, exactly like the raw-pointer case.
2. The smart pointer changes *where* `delete` is called from, not *what* it is called on. Wrapping a base pointer in `unique_ptr` or `shared_ptr` does not add a virtual destructor.

## Detection

| Tool | Catches it? | How |
|---|---|---|
| **`-Wdelete-non-virtual-dtor`** (in `-Wall`, GCC/Clang) | ~ delete-site only | Fires automatically under plain `-Wall -Wextra` for a `delete` expression *visible in source* — caught example 1 above. It cannot see the `delete` inside `std::default_delete<Sensor>::operator()`, so it is silent on example 2. |
| **`-Wnon-virtual-dtor`** (GCC/Clang, not in `-Wall`) | ~ declaration-site | Must be requested explicitly; flags the class *declaration* itself ("has virtual functions and accessible non-virtual destructor") regardless of whether anyone ever deletes through it. GCC also fires it — a known false positive — on a destructor that is `protected`, where deleting through the base cannot compile at all (*Prevention Rules*). Never treat either warning alone as proof; read the class. |
| **AddressSanitizer** (`-fsanitize=address`) | ✓ at run time | Reports `new-delete-type-mismatch`: a non-virtual destructor sizes the deallocation from the pointer's *static* type (`sizeof(Sensor)`, 8 bytes here) while the block was allocated for the *dynamic* type (`sizeof(TempSensor)`, 16 bytes). Verified on GCC 11.4, x86-64 Linux (this vault's toolchain), `-fsanitize=address,undefined`: both examples above abort with exactly this diagnostic, one showing `std::unique_ptr<Sensor>::~unique_ptr()` in the stack trace. |
| **UBSan** (`-fsanitize=undefined`) | ✗ | Verified same toolchain, same examples: UBSan alone runs both programs to completion and prints nothing wrong. A deallocation-size mismatch is an AddressSanitizer check, not one of UBSan's; don't expect UBSan to catch this class of bug. |
| **Static analysis** | ✓ some | clang-tidy `cppcoreguidelines-virtual-class-destructor`: flags a class with a virtual function and an accessible non-virtual destructor. |
| **Code review heuristic** | ✓ if asked | For every class with at least one `virtual` member: *"will an object of a derived type ever be deleted through a pointer to this class?"* Yes → the destructor must be virtual. Must always be no → make it non-public instead of trusting everyone to remember. |

## Fix

**✗ Non-virtual base destructor → ✓ virtual base destructor**

```cpp
#include <memory>

struct Sensor {
    virtual ~Sensor() = default;        // ① one keyword; dispatched like any virtual call
    virtual void poll() const = 0;
};

struct TempSensor : Sensor {
    double* history;
    TempSensor() : history(new double[100]) {}
    ~TempSensor() override { delete[] history; }   // ② now reliably runs
    void poll() const override {}
};

int main() {
    std::unique_ptr<Sensor> s = std::make_unique<TempSensor>();
    s->poll();
}   // ③ ~unique_ptr() → vtable's deleting-dtor slot → ~TempSensor() → ~Sensor()
```
1. `virtual` on the base destructor is all this costs syntactically; the vtable slot it adds is the same one [[Virtual Dispatch — vptr and vtable]] already describes for every other virtual member.
2. `override` on the derived destructor lets the compiler confirm it really is overriding a virtual, exactly as for any other function ([[override and final]]).
3. Verified on GCC 11.4, x86-64 Linux, `-fsanitize=address,undefined`: clean exit, `history` freed, no warnings.

## Prevention Rules

> [!rule] A base deleted through itself needs a public virtual destructor
> If any code anywhere will ever write `delete basePtr;` (directly, or inside a `unique_ptr`/`shared_ptr`), the base's destructor must be `virtual`. This is the design half of *Root Cause*, and it is what `[expr.delete]` ¶3 requires.

> [!rule] A base that must never be deleted that way is safer non-virtual and protected
> *(Core Guidelines C.35)* If polymorphic deletion through the base is never supposed to happen, give it a `protected`, non-virtual destructor instead of a virtual one. It costs no vtable slot, and `delete basePtr;` then fails to *compile* — `error: 'Sensor::~Sensor()' is protected within this context` (verified, GCC 11.4) — turning the mistake from run-time UB into a build error. Deleting through the exact derived type still works: the derived class's own (public, implicit) destructor is a member function and can reach the protected base destructor.

> [!rule] `= default` is not free of side effects
> Declaring a destructor at all — even `virtual ~Base() = default;` — stops the compiler from implicitly generating a move constructor or move assignment operator for that class (`[class.copy.ctor]`; Primer §15.7.1, p. 623, calls this out directly for exactly this case). A base written this way falls back to copying where it might have moved. See [[Rule of Zero, Three and Five]].

> [!rule] Enable both dtor warnings; verify with AddressSanitizer
> `-Wnon-virtual-dtor` is not in `-Wall`; add it explicitly, and don't rely on `-Wdelete-non-virtual-dtor` alone — it is blind to any `delete` that happens inside library code such as a smart pointer's destructor. Run the test suite under `-fsanitize=address` ([[Sanitizers — ASan, UBSan, TSan]]); UBSan will not catch this class of bug.

## Connections

- **Root concept:** [[Virtual Dispatch — vptr and vtable]] (the deleting-destructor vtable slot this pitfall is missing) · [[Destructors]] (the mechanism being skipped) · [[Inheritance]].
- **Related hazards:** [[Object Slicing]] (the same static/dynamic mismatch, on the copy side instead of destruction) · [[Virtual Calls in Constructors and Destructors]] (another destructor-time surprise from the same neighborhood).
- **Structural cures:** [[Abstract Classes and Interfaces]] (a pure virtual destructor is a legitimate way to make an otherwise-empty class abstract, and still needs a definition) · [[unique_ptr]] / [[shared_ptr and Reference Counting]] (do not fix this on their own, as example 2 shows) · [[RAII]].
- **Siblings:** [[Rule of Zero, Three and Five]] (declaring this one destructor changes what else the compiler will and won't generate) · [[Dangling Pointers and References]] (a different way an object's lifetime and a pointer's lifetime disagree).
- **Domain:** [[Map — Inheritance & Polymorphism]].
- **Practice:** *Continuum #18 Shape Hierarchy* — build a small polymorphic hierarchy, delete every instance through a base pointer under AddressSanitizer, and confirm the diagnostic disappears once the destructor is virtual.

## Check Yourself

> [!quiz]- Why does wrapping the base pointer in `std::unique_ptr<Sensor>` not fix example 2?
> `std::unique_ptr<Sensor>`'s deleter is `std::default_delete<Sensor>`, which calls `delete` on a `Sensor*` — the same static-type-only call as the raw-pointer version. A smart pointer changes who calls `delete` and when; it does not change what the destructor call is compiled against. Only a virtual destructor on `Sensor` fixes it.

> [!quiz]- `Sensor` has a protected, non-virtual destructor. Why does `TempSensor* t = new TempSensor(); delete t;` compile and run correctly, while `Sensor* p = new TempSensor(); delete p;` does not compile at all?
> `delete t` calls `TempSensor`'s own (implicitly public) destructor, which — as a member function of `TempSensor` — has access to the protected `~Sensor()` it must chain to. `delete p` tries to call `~Sensor()` directly from `main`, outside any class, where the protected destructor is not accessible: a compile error, not UB. This is exactly the protection *Prevention Rules* describes.

> [!quiz]- A base class has no data members and no resources to release. Is a virtual destructor still needed?
> Yes, if any code will ever delete a derived object through a pointer to that base. The bug is about *how many bytes get freed and which destructor chain runs*, not about whether the base itself owns anything — a derived class added later almost always does, and by then the missing `virtual` is easy to overlook.

## Sources

- Primer §15.2.1 "Defining Base and Derived Classes" (p. 594): why a base almost always needs a virtual destructor, introduced alongside `virtual` on `net_price`.
- Primer §15.7.1 "Virtual Destructors" (pp. 622–623): the mechanics of dispatch through a base pointer, and "Virtual Destructors Turn Off Synthesized Move."
- Tour §5.5 "Class Hierarchies" (p. 65): "A virtual destructor is essential for an abstract class... it may be deleted through a pointer to a base class."
- cppreference, *Destructors* § Virtual destructors: https://en.cppreference.com/w/cpp/language/destructor
- Draft standard `[expr.delete]` ¶3 (the exact UB clause): https://eel.is/c++draft/expr.delete#3
- C++ Core Guidelines C.35 "A base class destructor should be either public and virtual, or protected and non-virtual": https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#c35-a-base-class-destructor-should-be-either-public-and-virtual-or-protected-and-nonvirtual
- clang-tidy `cppcoreguidelines-virtual-class-destructor`: https://clang.llvm.org/extra/clang-tidy/checks/cppcoreguidelines/virtual-class-destructor.html
