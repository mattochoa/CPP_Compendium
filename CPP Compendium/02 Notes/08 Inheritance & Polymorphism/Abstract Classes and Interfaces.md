---
id: abstract-classes
title: Abstract Classes and Interfaces
aliases:
- interface
- pure virtual function
- pure abstract class
type: concept
domain: D08
tier: 1
status: draft
standard: C++98
prereqs:
- "[[Virtual Functions]]"
- "[[Virtual Dispatch — vptr and vtable]]"
related:
- "[[Virtual Destructors]]"
- "[[Object Slicing]]"
- "[[override and final]]"
- "[[RTTI and dynamic_cast]]"
practice:
- 18
- 21
tags:
- type/concept
- domain/d08
- tier/1
- tension/compile-time-vs-run-time
- tension/abstraction-vs-control
- std/c++98
- std/c++11
created: 2026-09-29
updated: 2026-09-29
---

# Abstract Classes and Interfaces

> [!essence]
> A class becomes **abstract** the moment it has a **pure virtual function** — one declared with `= 0` instead of a body. The compiler then refuses to let any object of that exact type exist, ever, by any means. What remains is a contract: a set of operations a reader can call through a base pointer or reference, with the promise that some concrete derived class, not yet written or not yet linked, supplies every one of them.

## The Problem

[[Virtual Dispatch — vptr and vtable]] gives every polymorphic class a table with one function-pointer slot per virtual function, filled in when the class is compiled. That mechanism needs *something* in every slot. For a function like `Circle::area()` there's an obvious body. For `Shape::area()` there is not — a generic shape has no formula, no radius, no side length to compute from.

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint.** Every virtual function a class declares or inherits must occupy a slot in that class's vtable, and a slot needs *some* address in it the moment an object of the class is constructed and its vptr stamped.
> 2. **Consequence.** If `Shape::area()` is given a placeholder body — `return 0.0;`, or throw — nothing stops `Shape s;` from compiling: a "shape" with no actual shape now exists and answers every query with a lie. Worse, if a derived class forgets to override `area()`, the placeholder runs silently instead of the compiler catching the omission.
> 3. **Requirement.** The language needs a way to say, at the base class itself, *"this operation has no meaningful body here — postpone it, and refuse to let this exact type come into being until something further down supplies one."*
> 4. **Design.** Write `= 0` where the body would go: a **pure virtual function**. A class with at least one pure virtual function whose final overrider is still pure — declared right here, or simply inherited without ever being overridden — is an **abstract class**. The compiler enforces the postponement by refusing to construct one: no local, no `new`, no by-value parameter or return, anywhere, for that exact type.
> 5. **Price.** The check is purely about the type's completeness as a set of promises, not about whether any given use would ever call the missing function. A `Circle` that overrides `area()` but not some other pure virtual `Shape` also declares is still abstract — silently, until the moment someone tries to instantiate it, which can be far from where the missing override was actually forgotten.

> [!tension] compile time ⟷ run time
> The instantiation ban is enforced entirely by the compiler, before the program runs: `Shape s;` never gets the chance to execute. But *which* concrete class ends up discharging the contract, and which override actually runs through a `Shape&`, is still decided at run time by ordinary [[Virtual Dispatch — vptr and vtable|virtual dispatch]]. An abstract class fixes a compile-time completeness requirement onto a mechanism that otherwise resolves everything late.

> [!tension] abstraction ⟷ control
> An abstract class can still hold data members, constructors, and fully-implemented member functions — being abstract is a fact about one missing override, not a promise of statelessness. Turning it into a genuine **interface** — no data, only pure virtuals and a virtual destructor — is a separate, deliberate design choice (Core Guidelines I.25), not something the language requires.

## Mental Model

> [!model] A contract with a blank line
> `Shape` is a contract: it lists the operations any shape must support, but leaves `area()`'s line blank — there's no formula that fits every shape. You cannot notarize (instantiate) a contract with a blank line. `Circle` copies the contract and fills in the blank with `3.14159 * r * r`; only the filled-in copy can be notarized.
> **Where it breaks:** paper contracts don't inherit their blanks. A C++ class does — if `Square` derives from `Shape` and forgets to fill in `area()`, `Square` is handed a fresh copy of the *same* blank line, and stays exactly as un-notarizable as `Shape` was, with no separate act of "leaving it blank" at the `Square` level to point to.

```text
 Shape's vtable (built once, whether or not Shape is ever "used" alone)
┌──────────────────────────────────────┐
│ [0] Shape::~Shape       (complete)   │  ◀── ordinary slot: Shape supplies this
│ [1] Shape::~Shape       (deleting)   │
│ [2] Shape::area          ??????      │  ◀── the blank line: no body was ever given
└──────────────────────────────────────┘
                     │
                     │  Circle overrides area() → its own vtable has a real address there
                     ▼
┌──────────────────────────────────────┐
│ [2] Circle::area  ──▶ 3.14159 * r * r│  ◀── the blank is filled; Circle is instantiable
└──────────────────────────────────────┘
```

## Mechanics

| Situation | Rule | Example |
|---|---|---|
| Declaring a pure virtual function | Write `= 0` where the body would go — after the declarator and any `override`/`final` | `virtual double area() const = 0;` |
| What makes a class abstract | At least one pure virtual function whose **final overrider**, in that class, is still pure — declared here, or inherited without ever being overridden | a `Square` that overrides `area()` but not an inherited pure virtual `perimeter()` is still abstract |
| Creating objects | Forbidden for the exact abstract type, by any means — a named variable, `new`, a by-value parameter or return, the target of an explicit cast | `Shape s;`, `new Shape`, `Shape make();`'s *definition* are all ill-formed |
| A base-class subobject | Fine — a `Circle` legitimately contains a `Shape` part, built by `Shape`'s own constructor | `struct Circle : Shape { ... };` |
| Pointer or reference to it | Always fine — nothing is manifested, so no object of the abstract type has to exist | `Shape&`, `const Shape*` |
| A pure virtual function's body | Optional, not forbidden — it may be defined, out-of-class; it **must** be defined if it is the destructor | see In Code, examples 2 and the note below |
| Friend declarations | Cannot carry a pure-specifier | `friend void f() = 0;` is ill-formed |

> [!standard] `[class.abstract]` ¶2, ¶3, ¶4, ¶6
> ¶2 defines the pure-specifier and states that a class with at least one pure virtual function is abstract. ¶4 sharpens this: what matters is the **final overrider** — a class that inherits a pure virtual and never overrides it is abstract too, even if it overrides every other virtual the base declares. ¶3 (note) explains *why* an abstract type can't be a parameter, return type, or cast target: each would require manifesting a prvalue of that type, and such a prvalue would itself be of abstract class type, which nothing may create. ¶6 permits ordinary (non-virtual, qualified) calls to a pure virtual from the class's own constructor or destructor, but a *virtual* call to one that is not yet overridden, made while the object's vptr still names the base, is undefined behavior.

GCC applies the parameter/return restriction exactly where ¶3 says an object would have to be manifested, not at a bare declaration: a *declaration* `double describe(Shape s);` compiles (GCC 11.4.0), because no `Shape` needs to exist yet. Only *defining* `describe`, or *calling* it with a real argument, forces the compiler to construct a parameter of abstract type — and that is where it refuses. Say this precisely; "abstract types can't be parameters" overstates what the Standard and the compiler actually check.

## Under the Hood

> [!machine] The missing slot holds a real, callable trap (GCC 11.4.0, x86-64 Linux, `-fdump-lang-class`, observed)
> `Shape`'s vtable is still emitted — a `Circle`'s constructor briefly points its vptr at it, exactly as in [[Virtual Dispatch — vptr and vtable]]. Its `area` slot is not empty; it holds a real, linked address:
> ```text
> Vtable for Shape
> Shape::_ZTV5Shape: 5 entries
> 0     (int (*)(...))0                        ; offset-to-top
> 8     (int (*)(...))(& _ZTI5Shape)            ; typeinfo for Shape
> 16    Shape::~Shape                            ; complete-object destructor
> 24    Shape::~Shape                            ; deleting destructor
> 32    (int (*)(...))__cxa_pure_virtual         ; ◀── area()'s slot
> ```
> `__cxa_pure_virtual` is a real, weak-linked function in the C++ runtime (`libstdc++`/`libc++abi` both ship one). If anything ever calls through that slot — the UB case in ¶6 above, a virtual call to `area()` while the vptr still names `Shape` — the program prints `pure virtual method called` and calls `std::terminate`, instead of jumping to garbage. The compiler cannot always prevent the call (¶6 forbids it, but doesn't have to catch it); the runtime traps it instead of letting it run wild.

`sizeof(Shape)` is **8** (the vptr alone — the same as any other polymorphic class with no data of its own) and `sizeof(Circle)` is **16** (vptr plus one `double`), matching [[Virtual Dispatch — vptr and vtable]]: being abstract changes what may exist, not the object layout.

## In Code

**1 · Only a class with every override in place can be instantiated**

```cpp
// cc: ill-formed
struct Shape {
    virtual ~Shape() = default;
    virtual double area() const = 0;
};

int main() {
    Shape s;   // ①
}
```
```cpp
#include <iostream>

struct Shape {
    virtual ~Shape() = default;
    virtual double area() const = 0;
};
struct Circle final : Shape {              // ②
    double r;
    explicit Circle(double r) : r{r} {}
    double area() const override { return 3.14159 * r * r; }
};

int main() {
    Circle c(2.0);
    Shape& s = c;                          // ③
    std::cout << s.area() << '\n';
}
// expect: 12.5664
```
1. GCC: *"cannot declare variable 's' to be of abstract type 'Shape'"* — `Shape` still has a pure `area()`, so no object of exactly that type may exist.
2. `Circle` overrides the one pure virtual `Shape` declares. Its final overrider is a real function, so `Circle` is concrete.
3. A `Shape&` bound to the `Circle` subobject is fine — no `Shape` object was created; `c` is, and always was, a `Circle`.

**2 · A pure virtual function may still have a body — an override can opt in**

```cpp
#include <iostream>

struct Shape {
    virtual double area() const = 0;
    virtual void describe() const = 0;                          // ①
};
void Shape::describe() const {                                   // ②
    std::cout << "some shape, area " << area() << '\n';
}

struct Circle final : Shape {
    double r;
    explicit Circle(double r) : r{r} {}
    double area() const override { return 3.14159 * r * r; }
    void describe() const override { Shape::describe(); }        // ③
};

int main() {
    Circle c(2.0);
    c.describe();
}
// expect: some shape, area 12.5664
```
1. `describe` is pure — `Circle` still must supply its own override to become concrete.
2. But `=0` only cancels the *requirement* to define a body, not the *permission* to. `Shape::describe` is a genuine, callable function, defined out-of-class as the rule requires.
3. `Circle::describe` satisfies the override requirement, then opts into the base's body with a qualified call — `Shape::describe()` bypasses the (already-resolved) virtual mechanism and calls exactly that function. The naive reading of "pure virtual" as "no implementation, ever" is wrong: this prints `Shape`'s wording, using `Circle`'s own `area()` inside it.

**3 · The parameter/return-by-value restriction bites where an object would have to exist**

```cpp
// cc: ill-formed
struct Shape {
    virtual double area() const = 0;
};

double describe(Shape s) { return s.area(); }   // ①
```
1. GCC: *"cannot declare parameter 's' to be of abstract type 'Shape'"*. Defining this function would need to construct a `Shape` parameter object on every call — exactly the object `[class.abstract]` ¶3 forbids. Change the parameter to `const Shape&` and the same function compiles: nothing is manifested through a reference.

**4 · An empty abstract class as a genuine interface (Core Guidelines I.25)**

```cpp
#include <iostream>
#include <memory>
#include <string>
#include <vector>

struct Drawable {                                    // ① no data members at all
    virtual ~Drawable() = default;
    virtual void draw() const = 0;
};

class Circle final : public Drawable {
public:
    explicit Circle(double r) : r_{r} {}
    void draw() const override { std::cout << "circle r=" << r_ << '\n'; }
private:
    double r_;
};

class Label final : public Drawable {                // ② unrelated concrete type, same contract
public:
    explicit Label(std::string text) : text_{std::move(text)} {}
    void draw() const override { std::cout << "label \"" << text_ << "\"\n"; }
private:
    std::string text_;
};

int main() {
    std::vector<std::unique_ptr<Drawable>> scene;
    scene.push_back(std::make_unique<Circle>(2.0));
    scene.push_back(std::make_unique<Label>("hello"));
    for (const auto& d : scene) d->draw();            // ③
}
// expect: circle r=2
// expect: label "hello"
```
1. `Drawable` carries no state and no implemented behavior — every member is pure, plus a virtual destructor. There is nothing to slice and no implementation for `Circle` or `Label` to inherit by accident.
2. `Circle` and `Label` share no data, no base logic, and no domain in common beyond "can be drawn" — a pure interface unifies types that a data-carrying base class never could.
3. The loop knows only `Drawable`; each call dispatches to the real implementation through the vptr, exactly as in [[Virtual Dispatch — vptr and vtable]].

## Pitfalls

> [!trap] "Pure virtual" does not mean "no implementation"
> Example 2 disproves the common assumption directly: `Shape::describe()` has a full body, and `Circle` calls it. What `= 0` actually cancels is the *requirement* that this class supply the function — not the function's ability to do real work once a derived class opts in with a qualified call.

> [!ub] A virtual call to an unoverridden pure virtual, from the class's own constructor or destructor
> While `Shape`'s own constructor or destructor runs, the object's vptr names `Shape`, and `area`'s slot there is `__cxa_pure_virtual` unless `Shape::area` happens to have a definition. Calling `area()` *virtually* at that point — not through a qualified `Shape::area()` — is undefined behavior per `[class.abstract]` ¶6, and in practice either fails to link (no definition exists anywhere) or reaches the runtime trap shown in *Under the Hood*. Full treatment, including why the vptr says `Shape` at all during construction, is in [[Virtual Calls in Constructors and Destructors]].

> [!trap] An inherited, unoverridden pure virtual keeps the whole subhierarchy abstract
> If `Square` derives from `Shape` and overrides `area()` but `Shape` also declares a pure virtual `perimeter()` that `Square` forgets, `Square` is abstract too — silently, with no diagnostic at the point of the omission. The compiler only complains the moment someone tries `Square sq;`, which can be a different file, written by someone who has never seen `Shape`'s declaration.

> [!rule] Prefer an empty abstract class when the goal is a genuine interface
> A pure interface — only pure virtuals and a virtual destructor, no data (Core Guidelines I.25, C.121) — is more stable than a base class that also carries state: derived classes couple only to the contract, never to implementation details that might later change. See [[Object Slicing]] for what a data-carrying base risks that a pure interface cannot.

## Evolution

| Standard | Change | Why |
|---|---|---|
| C++98 | Pure virtual functions (`= 0`); the instantiation ban on any class with an unresolved one | The core mechanism this note describes, present from the language's first standard |
| **C++11** | `override`/`final` join the grammar as virt-specifiers, sitting *between* the declarator and the pure-specifier (`void f() const override = 0;`) | Lets a pure virtual also be checked as a genuine override, or seal further overriding, without new syntax for the pure-specifier itself |
| Defect reports (retroactive to C++98) | CWG 390: a pure virtual **destructor** must be defined, because destructor chaining calls every base destructor whether or not it was ever overridden. CWG 2153: a friend declaration may not carry a pure-specifier | Both close cases the original wording left ambiguous or wrong |

## Connections

- **Prerequisites:** [[Virtual Functions]] — a pure virtual is a virtual function that omits its body by contract, not by accident. [[Virtual Dispatch — vptr and vtable]] — the vtable-slot mechanics this note completes: what a slot holds when no override has filled it in yet.
- **Enables:** [[Virtual Destructors]] — the one function almost every abstract base needs, pure or not. [[override and final]] — checking that a class's overrides actually discharge the contract it inherited.
- **Hazards:** [[Object Slicing]] — copying through a `Shape` value is exactly as destructive to a data-carrying abstract base as to any other polymorphic type. [[Virtual Calls in Constructors and Destructors]] — the UB case above, developed in full.
- **Domain:** [[Map — Inheritance & Polymorphism]].
- **Practice:** *Continuum #18 Shape Hierarchy & Polymorphic Area Calculator*: make `Shape` genuinely abstract and watch the compiler refuse a bare `Shape` the moment you try one. *Continuum #21 Game Entity System*: an empty `Drawable`- or `Updatable`-style interface, implemented by otherwise-unrelated entity types.

## Check Yourself

> [!quiz]- What exactly makes a class abstract, and does inheriting a pure virtual without overriding it count?
> A class is abstract if it has at least one pure virtual function whose final overrider, in that class, is still pure. Declaring `= 0` directly counts, and so does simply inheriting a pure virtual and never overriding it — the class doesn't have to write `= 0` itself to stay abstract.

> [!quiz]- If `= 0` means "no meaningful implementation here," why does the Standard allow a pure virtual function to have a definition at all?
> `= 0` cancels the *requirement* that this class supply a body, not the *permission* to. A defined pure virtual gives derived classes a default they can opt into with a qualified call (`Base::f()`) after satisfying the override requirement with their own function — useful for a shared default behavior that a subclass can still be forced to acknowledge explicitly. A pure virtual destructor must use exactly this: a body is mandatory there, because destructor chaining always calls it.

> [!quiz]- Predict: does `Shape describe();` (a declaration only, never defined or called) compile, given `Shape` has a pure virtual `area()`?
> Yes. The parameter/return-type restriction bites only where an object of the abstract type would actually have to be manifested — defining the function, or calling it. A bare declaration manifests nothing, so GCC accepts it; only trying to define or call `describe` fails.

> [!quiz]- In example 4, why must `Drawable`'s destructor be `virtual`, given none of the derived classes hold resources that need special cleanup?
> `scene` holds `std::unique_ptr<Drawable>`; when each entry is destroyed, `delete` runs through a `Drawable*` whose dynamic type is `Circle` or `Label`. Without a virtual destructor, that delete would only run `~Drawable()`, skipping `~Circle()`/`~Label()` entirely — undefined behavior regardless of whether those destructors would have done anything observable. See [[Virtual Destructors]].

## Sources

- Primer §15.4 "Abstract Base Classes" (pp. 609–610): pure virtual functions introduced; a pure virtual may have an out-of-class definition; "classes with pure virtuals are abstract base classes."
- Tour §5.3 "Abstract Types" (p. 60): the instantiation-ban error message from the language's own designer's example, and the pointer/reference exception.
- PPP §12.2 "Shape — an abstract class" and §12.3 "Base and derived classes" (ch. 12 "Class Design"): the abstract-class idea built up from a working `Shape` hierarchy, first-principles style.
- cppreference, *Abstract class*: https://en.cppreference.com/w/cpp/language/abstract_class
- Draft standard `[class.abstract]`: https://eel.is/c++draft/class.abstract
- Itanium C++ ABI, `__cxa_pure_virtual`: https://itanium-cxx-abi.github.io/cxx-abi/abi.html
- C++ Core Guidelines I.25, *Prefer empty abstract classes as interfaces to class hierarchies*; C.121, *If a base class is used as an interface, make it a pure abstract class*: https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
