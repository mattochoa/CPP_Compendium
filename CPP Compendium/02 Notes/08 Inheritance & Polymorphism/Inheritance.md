---
id: inheritance
title: Inheritance
type: concept
domain: D08
tier: 1
status: draft
standard: C++98
prereqs:
- "[[Classes as User-Defined Types]]"
- "[[Encapsulation and Class Invariants]]"
related:
- "[[Virtual Functions]]"
- "[[Composition vs Inheritance]]"
- "[[Public, Protected and Private Inheritance]]"
- "[[Object Slicing]]"
practice:
- 18
- 20
tags:
- type/concept
- domain/d08
- tier/1
- tension/value-vs-identity
- std/c++98
- std/c++11
created: 2026-09-26
updated: 2026-09-26
---

# Inheritance

> [!essence]
> A derived class names an existing class in its **derivation list** and, in return, gets every accessible member of that class for free, plus whatever new members it adds. The base becomes a physical **subobject** nested inside every derived object — not a separate, linked thing but a fixed piece of it. Declared `public`, the relationship also means *is-a*: a pointer or reference to the derived type may be used wherever the base type is expected.

## The Problem

A function such as `render(const Shape&)` is translated once, and from that point on it can only name types the compiler already knows about. Yet a real program wants `render` to keep working as new kinds of shape are added later — sometimes in a file its author never opens.

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint.** A class's members are fixed at the point it is defined. Two classes that should share behavior — `Circle` and `Square` both have a name and both compute an area — have no built-in way to say "we are the same kind of thing" without one being copy-pasted from the other.
> 2. **Consequence.** Without such a mechanism, every new related type either re-declares the shared members from scratch (repetition, and the two copies drift out of sync), or every caller that wants to handle "any shape" must be rewritten each time a new shape type appears — a `switch` on a type tag that never stops growing.
> 3. **Requirement.** The language needs a way for one class to say "start from that class's members" so the shared part is declared exactly once, and a way to mark the relationship so that code written against the old type can, at least through a pointer or reference, accept the new one without being told about it by name.
> 4. **Design.** C++'s **class derivation list** — `class Circle : public Shape { ... };` — does both. Every accessible member of `Shape` becomes a member of `Circle` too, as if declared there (Primer §15.2, p. 596–597), and because the specifier is `public`, the Standard also licenses an implicit conversion from `Circle*`/`Circle&` to `Shape*`/`Shape&` (`[class.derived.general]`; cppreference, *Derived classes*, §Public inheritance). `Circle` need not repeat a single line of `Shape`, and `render` need not know `Circle` exists.
> 5. **Price.** Reuse is whole-base-or-nothing: a derived class cannot inherit part of a base and reimplement the rest, and every base class it names becomes a permanent, physical part of its own object. Reaching for this relationship between types that are not genuinely "a kind of" each other — just to avoid retyping a few members — couples the derived class to every detail the base class ever changes. [[Composition vs Inheritance]] is this domain's very next stop for exactly that reason.

> [!tension] value ⟷ identity
> A derivation list is a promise about **identity**: an object's address, read through a pointer or reference, may be treated as its base's. It says nothing about **value**. Copy a `Circle` object into storage typed as `Shape` and the compiler runs `Shape`'s own copy constructor — only the `Shape` part travels. The is-a relationship this note builds survives exclusively through a pointer or reference to the *same* object; through a copy, it collapses. That collapse has a name, [[Object Slicing]], and this note is the reason it is possible at all.

## Mental Model

```text
 Circle object                                     size = sizeof(Shape) + sizeof(radius_)
┌──────────────────────────────────┐  offset 0        (plus alignment padding)
│ Shape subobject          (base)  │
│  ┌──────────────────────────┐    │  ← every Shape member function
│  │ name_ : std::string      │    │     operates on just this part,
│  └──────────────────────────┘    │     and knows nothing beyond it
├──────────────────────────────────┤
│ radius_ : double     (own member)│  ← added by Circle itself
└──────────────────────────────────┘
```

> [!model] A renovation, not a rewrite
> A derived class is a renovation of an existing blueprint: it starts from `Shape`'s plan with every wall already load-bearing and every wire already run, then adds rooms. It cannot quietly delete or resize a room the base blueprint specifies — the base subobject is complete or the derived object does not compile.
> **Where it breaks:** a renovation is something you commission once, by choice. Inheriting a base's members is not partial or optional the way a renovation budget is — you get all of the base's accessible members, unconditionally. And the analogy is silent on *which* operations vary by the object's actual type at run time; that question belongs to the next note, [[Virtual Functions]].

## Mechanics

| Situation | Rule | Example |
|---|---|---|
| Declaring a derived class | `class D : access-specifier B { ... };` names `B` as a direct base; `access-specifier` is one of `public`, `protected`, `private` | `class Circle : public Shape { ... };` |
| Default access specifier | Omitted specifier defaults to `private` when `D` uses the `class` keyword, `public` when it uses `struct` — independent of the member-default rule | `struct S : Base {};` // public · `class C : Base {};` // private — Primer §15.5 (p. 616) |
| Base must be complete | A class must be *defined*, not merely forward-declared, before it can be named as a base | `class Shape; class Circle : public Shape {};` is ill-formed — Primer §15.2.2 (p. 600); `[class.derived.general]` ¶2 |
| Direct vs. indirect base | A class named in the derivation list is a *direct* base; a direct base's own bases are *indirect* bases of the derived class | `struct B{}; struct C:B{}; struct D:C{};` — `B` is indirect to `D` — Primer §15.2.2 (p. 600) |
| What is inherited | Every accessible member of the base (as governed by the derivation's access specifier) becomes a member of the derived class, as if declared there | `Circle` gets `Shape::name()` without redeclaring it — Primer §15.2 (p. 596–597) |
| Object layout | The derived object contains one subobject per base plus a subobject for its own members; the Standard leaves the exact offsets and allocation order unspecified | Primer, Fig. 15.1 (p. 597); `[class.derived.general]` ¶3, ¶5 |
| Construction order | Base subobject(s) are initialized first, in derivation-list order; then the derived class's own members, in declaration order; then the derived constructor's body runs | Primer §15.7 (p. 598): the base part comes into existence before any part that is specific to the derived class. |
| Destruction order | The exact reverse: the derived destructor's body runs, then its own members are destroyed, then the base subobject(s) | Primer §18.3 (p. 805): teardown always undoes construction from the most-derived part backward to the oldest base. |
| `is-a` via public derivation | A pointer or reference to `Derived` converts implicitly to a pointer or reference to an accessible, unambiguous base | `const Shape& r = circle;` — cppreference, *Derived classes*, §Public inheritance; `[conv.ptr]`, `[dcl.init.ref]` |

> [!standard] `class` vs. `struct` in a derivation list
> The only differences between a class defined with `class` and one defined with `struct` are the default *member* access specifier and the default *derivation* access specifier (Primer §15.5, p. 616). Neither keyword changes what inheritance itself does — which is why a privately-derived class should still write `private` explicitly, so the choice reads as intentional rather than a default nobody noticed.

A base class's `static` members are not duplicated per derived class: the whole hierarchy shares exactly one instance of each, reachable through the base name, the derived name, or an object of either (Primer §15.2.2, p. 599).

## Under the Hood

> [!machine] Plain inheritance costs nothing beyond its parts
> With no virtual functions in sight, a derived object is exactly the size of its parts, rounded up for alignment — no hidden pointer, no indirection. Verified with GCC 11, x86-64, `-O2`:
> ```cpp
> struct Base2 { int a; double b; };
> struct Derived2 : Base2 { char c; };
> // sizeof(Base2) == 16   (int padded to 8-byte align, then the double)
> // sizeof(Derived2) == 24  (Base2's 16 bytes, then char c, then padding)
> // (char*)static_cast<Base2*>(&d) - (char*)&d == 0   -- the base sits at offset 0
> ```
> The base subobject sits at offset 0 and the derived member follows it; the Standard permits any offset (`[class.derived.general]` ¶5), but every mainstream ABI places a single, non-virtual base at the start of the derived object. The moment a virtual function enters the picture, an extra pointer-sized field (the vptr) appears — that cost, and the indirect call it enables, belongs to [[Virtual Dispatch — vptr and vtable]], not to inheritance itself.

## In Code

**1 · A derivation list, minimally**

```cpp
#include <iostream>
#include <string>

class Shape {
public:
    explicit Shape(std::string name) : name_(std::move(name)) {}
    const std::string& name() const { return name_; }
private:
    std::string name_;
};

class Circle : public Shape {                                   // ①
public:
    Circle(std::string name, double radius)
        : Shape(std::move(name)), radius_(radius) {}             // ②
    double area() const { return 3.14159265 * radius_ * radius_; }
private:
    double radius_;
};

int main() {
    Circle c{"unit circle", 1.0};
    std::cout << c.name() << " has area " << c.area() << '\n';   // ③
}
// expect: unit circle has area 3.14159
```
1. `: public Shape` names `Shape` as `Circle`'s direct base; `Circle`'s members now implicitly include everything `Shape` declares.
2. The base subobject is initialized *first*, from the constructor initializer list. Omitting `Shape(...)` here would default-initialize the base — impossible, since `Shape` only declares an `explicit` one-argument constructor.
3. `c.name()` calls a member `Circle` never declared. It inherited it.

**2 · Access control and the `is-a` conversion in use**

```cpp
#include <iostream>

class Shape {
protected:
    void log(const char* msg) const { std::cout << msg << '\n'; }  // ①
};

class Circle : public Shape {
public:
    void announce() const { log("drawing a circle"); }             // ②
};

void render(const Shape&) { std::cout << "rendered via base interface\n"; }

int main() {
    Circle c;
    c.announce();
    render(c);                                                      // ③
}
// expect: drawing a circle
// expect: rendered via base interface
```
1. `protected` lets `Circle` (and any other derived class) call `log`; code holding only a `Shape` cannot.
2. `Circle` uses the inherited, protected member as if it had declared it itself.
3. `render` was compiled against `Shape` alone. Because the derivation is `public`, `c` converts implicitly to `const Shape&` — the *is-a* promise from example 1, redeemed here.

**3 · Construction and destruction order, made visible**

```cpp
#include <iostream>

struct Base {
    Base()  { std::cout << "Base()\n"; }
    ~Base() { std::cout << "~Base()\n"; }
};

struct Derived : Base {
    Derived()  { std::cout << "Derived()\n"; }
    ~Derived() { std::cout << "~Derived()\n"; }
};

int main() {
    Derived d;
}
// expect: Base()
// expect: Derived()
// expect: ~Derived()
// expect: ~Base()
```
Construction runs base-to-derived; destruction runs the exact reverse. Neither order is a compiler choice — both are guaranteed by the rules in the Mechanics table above.

**4 · What inheritance alone does *not* give you**

```cpp
#include <iostream>

struct Shape {
    void speak() const { std::cout << "Shape\n"; }
};

struct Circle : Shape {
    void speak() const { std::cout << "Circle\n"; }     // ①
};

void announce(const Shape& s) { s.speak(); }

int main() {
    Circle c;
    announce(c);                                         // ②
}
// expect: Shape
```
1. `Circle::speak` does not override `Shape::speak` in any run-time sense — with no `virtual`, it merely declares a second, unrelated function that happens to share a name and hides the base's from ordinary lookup on a `Circle`.
2. `announce` holds a `const Shape&`. Its *static* type is `Shape`, and a non-virtual call is resolved from the static type alone — so `Shape::speak` runs, even though the object is actually a `Circle`. Making a call vary by the object's *dynamic* type instead is exactly the problem [[Virtual Functions]] solves next.

## Pitfalls

> [!trap] A copy is not a reference
> The *is-a* relationship holds only through a pointer or reference to the original object. `Shape s = circle;` compiles without complaint and runs `Shape`'s copy constructor on a `Circle` argument — only the `Shape` subobject is copied, and the result has no `radius_` at all. This is [[Object Slicing]], and it exists precisely because a derived object always *contains* a complete, self-sufficient base subobject that can be copied on its own.

> [!trap] A derived class must be defined before it can act as a base
> `class Shape;` followed by `class Circle : public Shape {};` fails to compile (`error: invalid use of incomplete type`), because building `Circle`'s layout and inheriting `Shape`'s members both require knowing exactly what `Shape` contains. An incomplete type has no known members and no known size yet.

> [!trap] "Overriding" a non-virtual function is name hiding, not polymorphism
> Example 4 above is not a corner case — it is the default. Declaring `speak` again in `Circle` without `virtual` hides the base version from lookup on a `Circle` object but changes nothing about how a call through a `Shape&` resolves. Mistaking this for polymorphism is the single most common misreading of a first inheritance hierarchy.

## Evolution

| Standard | Change | Why |
|---|---|---|
| C++98 | Single and multiple inheritance, the three access specifiers, base-class subobjects | The foundational is-a and code-reuse mechanism this note describes |
| **C++11** | `final` on a class (`class Last final {};`) forbids further derivation (Primer §15.2.2, p. 600) | Lets a class author close off a hierarchy deliberately, rather than by omission |
| **C++11** | Inheriting constructors: `using Base::Base;` brings a base's constructors into the derived class's overload set | Removes boilerplate `Derived(args) : Base(args) {}` forwarding constructors in simple derivations |

## Connections

- **Prerequisites:** [[Classes as User-Defined Types]] (what a class already is before a derivation list adds a base) · [[Encapsulation and Class Invariants]] (the `public`/`protected`/`private` vocabulary this note extends across a class boundary). See [[Map — Classes & Encapsulation]] for the full frame.
- **Enables:** [[Virtual Functions]] → [[Virtual Dispatch — vptr and vtable]] (making a call vary by dynamic type) · [[Public, Protected and Private Inheritance]] (the access-specifier axis explored in full) · [[Composition vs Inheritance]] (when *not* to reach for this relationship).
- **Hazards:** [[Object Slicing]] (the value/identity tension named above, turned into a bug).
- **Domain:** [[Map — Inheritance & Polymorphism]].
- **Practice:** *Continuum #18 Shape Hierarchy & Polymorphic Area Calculator*: build the `Shape`/`Circle` relationship out further and print `sizeof` at each step to see the subobject layout grow. *Continuum #20 Employee Management System*: before reaching for a base class, ask whether an `Employee`-`Manager` relationship is really is-a, or whether [[Composition vs Inheritance]] would serve better.

## Check Yourself

> [!quiz]- What exactly does a derived class inherit from an accessible base, and where does the inherited part physically live?
> Every accessible member of the base becomes a member of the derived class too, as if declared there. Physically, the base occupies a subobject nested inside the derived object, at an offset the Standard leaves unspecified (though every mainstream ABI places a single non-virtual base at offset 0).

> [!quiz]- Why must a class be fully defined, not merely forward-declared, before it can be named as a base class?
> The derived class must know the base's exact member list and size to build its own layout and to inherit those members. A forward declaration (`class Shape;`) gives the compiler a name but no members and no size — an incomplete type, `[class.derived.general]` ¶2.

> [!quiz]- Predict the output: `Circle` redeclares `void speak() const` without `virtual`; `announce(const Shape&)` calls `s.speak()` on a `Circle` argument. What prints?
> `Shape`. A non-virtual call is resolved from the expression's *static* type, which `announce` sees as `Shape`, regardless of the object's actual dynamic type.

> [!quiz]- `Shape s = circle;` where `circle` is a `Circle`. What ends up in `s`, and why?
> Only the `Shape` part. Assigning or initializing a `Shape` *value* from a `Circle` argument runs `Shape`'s own copy constructor, which knows only about `Shape`'s members — the `Circle`-specific data is not copied at all. See [[Object Slicing]].

## Sources

- Primer §15.2 "Defining Base and Derived Classes" (pp. 596–598): the derivation list, what is inherited, the derived-to-base conversion, and the base-before-derived initialization order (p. 598).
- Primer §15.2.2 (p. 599): static members are shared across the whole hierarchy, not duplicated per derived class.
- Primer §15.2.2 (p. 600): a base class must be defined, not merely declared; direct vs. indirect bases; `final` on a class (C++11).
- Primer §15.5 "Access Control and Inheritance" (p. 616): default derivation access specifier for `class` vs. `struct`.
- Primer §18.3 "Multiple and Virtual Inheritance" (p. 805): states the destructor-order rule generally, in the course of working a multi-base example.
- Tour §5.5 "Class Hierarchies" (p. 63): a class hierarchy as a lattice created by derivation, and the "is a kind of" reading of `: public`.
- PPP ch. 11 §11.10 "Image" and ch. 12 §12.3 "Base and derived classes": a `Shape`/derived-shape hierarchy built up from first principles, including object layout.
- cppreference, *Derived classes*: https://en.cppreference.com/w/cpp/language/derived_class (base-clause grammar; public/protected/private inheritance semantics).
- Draft standard `[class.derived.general]` — direct/indirect base classes, base-class subobjects, unspecified allocation order: https://eel.is/c++draft/class.derived
- See [[Guide — cppreference, the Draft Standard and the Core Guidelines]] for how to navigate cppreference and the draft Standard directly.
- See [[Guide — C++ Primer (5th ed)]] for where this domain's C++11-era citations sit and which claims need a modern-standard check first.
