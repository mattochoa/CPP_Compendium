---
id: virtual-functions
title: Virtual Functions
type: concept
domain: D08
tier: 1
status: draft
standard: C++98
prereqs:
- "[[Inheritance]]"
- "[[Pointers]]"
- "[[References]]"
related:
- "[[Virtual Dispatch — vptr and vtable]]"
- "[[override and final]]"
- "[[Abstract Classes and Interfaces]]"
- "[[Object Slicing]]"
- "[[Virtual Destructors]]"
practice:
- 18
tags:
- type/concept
- domain/d08
- tier/1
- tension/compile-time-vs-run-time
- tension/value-vs-identity
- std/c++98
- std/c++11
- std/c++20
created: 2026-09-27
updated: 2026-09-27
---

# Virtual Functions

> [!essence]
> A base class can mark a member function **virtual** to say: a call to this function, made through a pointer or reference, must be resolved by the object's *dynamic* type, not by the pointer's or reference's own *static* type. A derived class **overrides** it by declaring one with the exact same signature. The mechanism that carries this out, and its cost, belong to [[Virtual Dispatch — vptr and vtable]]; this note is the declaration-level promise that mechanism keeps.

## The Problem

[[Inheritance]] ended on a warning shot: a `Circle` that redeclares `speak()` without `virtual` does not change what `announce(const Shape&)` prints. The call `s.speak()` inside `announce` is resolved once, at compile time, from `Shape`'s own declaration — whatever the object actually is when the program runs.

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint.** An ordinary member call is resolved from the *static* type of the expression it's called on — the type visible to the compiler at that line — because that is the only information a separately-compiled function is guaranteed to have about its argument.
> 2. **Consequence.** `render(const Shape&)` can never run `Circle`'s own code through a plain member call, no matter how `Circle` overrides `Shape`'s members: the compiler bakes in `Shape`'s version the moment it compiles `render`, long before any `Circle` exists.
> 3. **Requirement.** For inheritance to buy anything beyond code reuse — for one algorithm to keep working as new derived types appear later — some member functions must be resolved using information that exists only at run time: what the object under the pointer or reference actually is. The base class author must opt specific functions into this, one at a time.
> 4. **Design.** Mark the function `virtual` in the base class. Every call to it made through a pointer or reference to that class, or to any accessible base of it, is now resolved using the object's dynamic type: the compiler defers the choice of which body runs until an actual object exists to ask. A derived class **overrides** the function by declaring one with an identical signature; virtuality, once introduced for a name, is inherited by every class further down that declares a matching function, whether or not it repeats the keyword.
> 5. **Price.** The match must be exact — same name, same parameter types, same cv- and ref-qualification — or the derived declaration merely *hides* the base's, which is a second, unrelated function invisible from a base pointer, not an override. And the class itself changes kind: any class that declares or inherits a virtual function becomes **polymorphic**, which [[Virtual Dispatch — vptr and vtable|carries a real, per-object cost]] that a plain aggregate never pays.

> [!tension] compile time ⟷ run time
> An ordinary call is a promise the compiler keeps entirely on its own, before the program ever runs. A virtual call is a promise the compiler *sets up* — reserving the choice — but keeps only once an object exists and the program is executing. Declaring `virtual` is the one-word decision to move that promise from compile time to run time, for this function only.

## Mental Model

What decides which body runs is not "is the function virtual" alone — it's that, crossed with how the call reaches the object. Only a pointer or reference can carry a dynamic type that differs from what's written at the call site; a named object or a copy has exactly one type, so there's nothing for "dynamic" to mean.

```text
                        function declared virtual?
                     no                          yes
              ┌─────────────────────┬──────────────────────────┐
called through│                     │                          │
a pointer or  │  static type        │  DYNAMIC type decides —  │
reference     │  decides (always)   │  resolved at run time    │
              ├─────────────────────┼──────────────────────────┤
called on a   │  static type        │  static type decides —   │
named object  │  decides            │  identical to non-virtual│
or a copy     │                     │  (no distinct dynamic    │
              │                     │  type to differ) — see   │
              │                     │  [[Object Slicing]]      │
              └─────────────────────┴──────────────────────────┘
```

> [!model] A label read at the door, not an address baked into the route
> A non-virtual call is a delivery address printed on the truck's own manifest: fixed before it leaves the depot (compiled), so every truck with that manifest goes to the same place. A virtual call is an address read off a label glued to the package itself, checked at the moment of delivery: two outwardly similar trucks can be sent to different doors if what they're carrying differs.
> **Where it breaks:** the label is physically part of the package — the object — not of the hand carrying it. A reference or pointer is only a hand; the same hand can carry different packages over its lifetime and gets routed differently each time. But repack a `Circle`'s contents into a plain `Shape`-sized box and the new box only ever had a `Shape` label — nothing about declaring the function virtual put a `Circle` label on it. That repacking is [[Object Slicing]].

## Mechanics

| Situation | Rule | Example |
|---|---|---|
| Declaring a virtual function | Write `virtual` before the return type, in the function's first declaration in the base class | `virtual void speak() const;` |
| Overriding it | A derived member function **overrides** it only if its name, parameter types, cv-qualification, and (since C++11) ref-qualification all match exactly; repeating `virtual` is legal but redundant | `void speak() const override;` |
| A near-miss signature | Doesn't override — declares a second, unrelated function that *hides* every base overload of that name from lookup on the derived type | `void resize(int)` does not override `resize(double)` — see [[Name Hiding in Derived Classes]] |
| `override` (C++11) | An identifier with special meaning, not a keyword. Ill-formed if the function it's attached to does *not* override a base virtual — turns a silent near-miss into a compile error | see In Code, example 3 |
| `final` (C++11) | Ill-formed for any further class to override this function (or, on a class itself, to derive from it at all) | `void speak() const final;` |
| Return type | Must be identical to the base's, or **covariant**: both pointers, or both references, to classes, where the base's class is an accessible, unambiguous base of the derived's | `Shape* clone() const` overridden by `Circle* clone() const` |
| Default arguments | Substituted from the *static* type of the call expression, even though the dynamic type still picks which body runs | see In Code, example 4 |
| Explicit qualification | `p->Base::f()` suppresses the virtual mechanism entirely, calling exactly the named version regardless of `*p`'s dynamic type | `baseP->Shape::speak();` |

> [!standard] What "the same signature" means (`[class.virtual]`)
> A derived member function G *overrides* a base's virtual function F when G's declaration corresponds to F's: same name and the same parameter-type-list, and — since C++11 — the same ref-qualifier or lack of one (`[class.virtual]` ¶2, ¶7). Access control plays no part in the decision: a `private` virtual can be overridden by a `public` one, and the base version need not even be visible at the point of the override (a derived-derived class can override a name hidden in between). Two mismatched return types are allowed only under the covariant-return rule (¶8); anything else with a matching name and parameter list but an unrelated return type is ill-formed.

> [!rule] Specify exactly one of `virtual`, `override`, `final`
> Repeating `virtual` on an override, or writing `override final` where `final` alone already implies it overrides, adds nothing and buries which one actually matters at that declaration (Core Guidelines C.128). Say the strongest true thing: plain `virtual` for a function introduced here, `override` for one that overrides and may still be overridden further, `final` for one that overrides and closes the chain.

Pure virtual functions (`= 0`) — a virtual function with no required definition, which makes its class impossible to instantiate directly — are a design taken to its limit; [[Abstract Classes and Interfaces]] is where that limit is developed in full.

## Under the Hood

> [!machine] Declaring one function virtual makes the whole object polymorphic (GCC 11.4.0, x86-64 Linux, `-O2`, observed)
> ```cpp
> struct Plain       { double name_len; };
> struct WithVirtual { double name_len; virtual void speak() const {} };
> // sizeof(Plain)       == 8
> // sizeof(WithVirtual) == 16
> ```
> The extra 8 bytes appear the instant *any* member function of the class is declared virtual — even `speak`, never called on this particular object — because the hidden field is a property of the class as a whole, not of which functions a given call site happens to use.

```text
 Plain (no virtual function)         WithVirtual (one virtual function)
┌───────────────────┐               ┌───────────────────┐
│ name_len : double │  8 bytes      │ vptr  ●────────────┼──▶ one shared table,
└───────────────────┘               │                    │    per class,
                                     │ name_len : double  │    static storage
                                     └───────────────────┘  16 bytes
```

This is an Itanium-ABI fact (GCC/Clang on Linux and macOS); the Microsoft ABI adds the same one hidden pointer on 64-bit Windows, but neither placement nor size is a language guarantee — only the *existence* of some run-time-readable marker is required, by the behavior `[class.virtual]` specifies. What that pointer points to, how a call reads it, and exactly what the dispatch costs are [[Virtual Dispatch — vptr and vtable|the next note's]] subject; this one only prices the declaration.

## In Code

**1 · Fixing the non-virtual call from [[Inheritance]]**

```cpp
#include <iostream>

struct Shape {
    virtual void speak() const { std::cout << "Shape\n"; }    // ①
};

struct Circle : Shape {
    void speak() const override { std::cout << "Circle\n"; }  // ②
};

void announce(const Shape& s) { s.speak(); }                  // ③

int main() {
    Circle c;
    announce(c);
}
// expect: Circle
```
1. `virtual` on the base declaration is enough; every matching function further down shares in dynamic dispatch without repeating the keyword.
2. `override` documents the intent and lets the compiler check it: this signature matches `Shape::speak` exactly.
3. `announce` still sees only `const Shape&`. Because `speak` is virtual and the call goes through a reference, the object's dynamic type — `Circle` — decides. The identical call in [[Inheritance]] printed `Shape`, because `speak` wasn't virtual there.

**2 · Virtual buys nothing through a value — only through identity**

```cpp
#include <iostream>

struct Shape {
    virtual void speak() const { std::cout << "Shape\n"; }
};
struct Circle : Shape {
    void speak() const override { std::cout << "Circle\n"; }
};

int main() {
    Circle c;
    Shape s = c;    // ①
    Shape& r = c;   // ②
    s.speak();      // ③
    r.speak();      // ④
}
// expect: Shape
// expect: Circle
```
1. Copy-initializing a `Shape` from a `Circle` runs `Shape`'s own copy constructor; the result is a genuine `Shape` object with no `Circle` part at all.
2. `r` is not a new object — it is another name for `c`, with `c`'s dynamic type intact.
3. `s`'s static and dynamic type are both `Shape`: there is only one type here, so declaring `speak` virtual changed nothing about this call.
4. `r`'s static type is `Shape&` but its dynamic type is `Circle`: the two differ, and dispatch reaches `Circle::speak`. Only a pointer or reference can carry that difference — see [[Object Slicing]].

**3 · `override` turns a near-miss into a compile error**

```cpp
// cc: ill-formed
struct Shape {
    virtual void resize(double factor);
};

struct Circle : Shape {
    void resize(int factor) override;   // ①
};

int main() {
    Circle c;
    Shape& s = c;
    s.resize(2.0);
}
```
1. `Circle::resize` takes `int`, not `double`, so it does not override `Shape::resize` — it would silently *hide* it instead. `override` forces the compiler to check, and GCC 11.4.0 rejects it: *"`void Circle::resize(int)` marked `override`, but does not override."*

**4 · Default arguments follow the static type, even though the body follows the dynamic type**

```cpp
#include <iostream>

struct Shape {
    virtual void greet(const char* who = "Shape") const {     // ①
        std::cout << "hello, " << who << '\n';
    }
};
struct Circle : Shape {
    void greet(const char* who = "Circle") const override {   // ②
        std::cout << "hi there, " << who << '\n';
    }
};

int main() {
    Circle c;
    Shape& s = c;
    s.greet();                                                 // ③
}
// expect: hi there, Shape
```
1. Each class may give the shared virtual function its own default argument; nothing requires them to agree.
2. `Circle::greet` is the body that runs — dynamic dispatch through `s` still picks it, exactly as in example 1.
3. But the default argument substituted is the one visible at the call site's *static* type, `Shape`. The result mixes both classes: `Circle`'s wording with `Shape`'s name, `"hi there, Shape"` — the substitution decision and the dispatch decision are made from two different types.

## Pitfalls

> [!trap] A near-miss signature hides instead of overriding
> Before `override` existed (and still, if you omit it), a parameter type, a missing `const`, or an extra argument silently declares a second, unrelated function. Code calling it through a derived object finds the new one; code calling it through a base pointer or reference never sees it and keeps running the base's version. This is arguably the single most common defect in a first hierarchy. Write `override` on every intended override, always. See [[Name Hiding in Derived Classes]].

> [!trap] Default arguments on a virtual function are a trap, not a feature
> Example 4 is not a corner case — any caller who reaches a `Circle` through a `Shape&` and relies on the default gets `Shape`'s value substituted into `Circle`'s body. The Core Guidelines' fix is the safest one: give a virtual function's default argument once, in the base, and never repeat or vary it in an override.

> [!ub] Deleting through a base pointer with a non-virtual destructor
> If `~Shape()` is not virtual, `delete` on a `Shape*` that actually points to a `Circle` is undefined behavior — the derived destructor is never guaranteed to run, resources it owns may leak, and the standard imposes no requirement on what does happen. Making a destructor virtual is usually the *first* function to mark so in a base meant to be used polymorphically. Developed in [[Virtual Destructors]].

> [!trap] A virtual call made from a constructor or destructor never reaches a derived override
> While `Shape`'s own constructor or destructor is running, the object *is* only a `Shape` as far as dispatch is concerned — the derived part hasn't been built yet, or has already been torn down. `[class.cdtor]` requires this, for the same reason [[Object Lifetime]] gives: the more-derived part's lifetime genuinely hasn't started, or has genuinely ended. Full treatment in [[Virtual Calls in Constructors and Destructors]].

## Evolution

| Standard | Change | Why |
|---|---|---|
| C++98 | `virtual`; dynamic binding through a base pointer or reference; pure virtual functions (`= 0`) | The mechanism this note describes, present from the language's first standard |
| **C++11** | `override` and `final`, as identifiers with special meaning rather than reserved keywords | Catches a signature mismatch at compile time instead of letting it silently hide a function |
| **C++11** | Ref-qualifiers (`&` / `&&`) join the signature an override must match (`[class.virtual]` ¶7) | Ref-qualified member functions needed a rule for which overrides count as "the same function" |
| C++20 | Virtual function calls permitted in constant expressions, when the dynamic type is known at compile time (P1064R0) | Lets `constexpr` evaluation use polymorphism instead of forbidding virtual calls outright |

## Connections

- **Prerequisites:** [[Inheritance]] — the is-a relationship a virtual call presupposes; this note is its very next stop. [[Pointers]] · [[References]] — dynamic dispatch fires only when a call travels through one of these two access paths.
- **Enables:** [[override and final]] (the C++11 specifiers introduced above, in full) → [[Virtual Dispatch — vptr and vtable]] (the mechanism and its exact run-time cost) → [[Abstract Classes and Interfaces]] (pure virtual functions taken to their limit).
- **Hazards:** [[Object Slicing]] (In Code, example 2) · [[Virtual Destructors]] · [[Virtual Calls in Constructors and Destructors]] · [[Name Hiding in Derived Classes]].
- **Domain:** [[Map — Inheritance & Polymorphism]].
- **Practice:** *Continuum #18 Shape Hierarchy & Polymorphic Area Calculator*: mark `area()` virtual and watch one loop, written against `Shape&`, dispatch differently for every shape you add.

## Check Yourself

> [!quiz]- What exactly must match for a derived function to override a base's virtual function, rather than merely hide it?
> Name, parameter types, cv-qualification, and — since C++11 — ref-qualification, all exactly. The return type must be identical or covariant. A function that matches the name but not the rest declares an unrelated function that hides every base overload of that name instead of overriding any of them.

> [!quiz]- In example 2, why does declaring `speak()` virtual change nothing about `Shape s = c; s.speak();`?
> `s` is a genuine `Shape` object with no `Circle` part — its static type and its dynamic type are the same thing, `Shape`. Virtual dispatch varies the call by dynamic type, but there is nothing for "dynamic" to mean when only one type exists. Only a pointer or reference to the *original* object can carry a dynamic type that differs from what's written at the call site.

> [!quiz]- Predict: `Shape* p = &c;` where `c` is a `Circle`. What does `p->Shape::speak();` print?
> `Shape`. Explicit qualification with `::` suppresses the virtual mechanism entirely and calls exactly the named version, regardless of `*p`'s dynamic type.

> [!quiz]- `struct Mid : Shape { void speak() const final; }; struct Leaf : Mid { void speak() const override; };` — does this compile?
> No. `Mid::speak` is `final`, so no further class may override it. `Leaf::speak` attempting to do so is ill-formed (`[class.virtual]` ¶4), even though `Leaf::speak`'s own signature matches perfectly.

## Sources

- Primer §15.3 "Virtual Functions" (pp. 603–607): dynamic binding fires only through a reference or pointer; `override`/`final` and how they interact; virtual functions and default arguments (p. 607); using the scope operator to circumvent the virtual mechanism (p. 607).
- Primer §15.4 "Abstract Base Classes" (p. 608): pure virtual functions introduced, previewing [[Abstract Classes and Interfaces]].
- Tour §5.4 "Virtual Functions" (p. 62): the `Container`/`vtbl` motivating example and the space/time cost summary, from the language's designer.
- cppreference, *virtual function specifier*: https://en.cppreference.com/w/cpp/language/virtual
- cppreference, *override specifier*: https://en.cppreference.com/w/cpp/language/override
- Draft standard `[class.virtual]` (matching rule ¶2, ¶7; covariant return ¶8; `final` ¶4; `override` ¶5): https://eel.is/c++draft/class.virtual
- P1064R0, *Allowing Virtual Function Calls in Constant Expressions*: https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/p1064r0.html
- C++ Core Guidelines C.128, *Virtual functions should specify exactly one of `virtual`, `override`, or `final`*: https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
