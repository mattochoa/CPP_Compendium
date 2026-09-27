---
id: class-overloading
title: Overloading in Classes — Constructors, Members and Operators
aliases:
- overloading in classes
- constructor overloading
- const overloads
- ref-qualified member functions
- overload vs override vs hide
- decorator pattern
- class decorator
- mixin
type: concept
domain: D06
tier: 2
status: draft
standard: C++98
prereqs:
- "[[Function Overloading]]"
- "[[Classes as User-Defined Types]]"
related:
- "[[Operator Overloading]]"
- "[[Constructors]]"
- "[[Comparisons and the Spaceship Operator]]"
- "[[Conversion Operators and explicit]]"
- "[[Name Hiding in Derived Classes]]"
- "[[override and final]]"
practice:
- 17
- 19
tags:
- type/concept
- domain/d06
- tier/2
- tension/abstraction-vs-control
- tension/value-vs-identity
- std/c++98
- std/c++11
- std/c++20
- std/c++23
created: 2026-09-26
updated: 2026-09-26
---

# Overloading in Classes — Constructors, Members and Operators

> [!essence]
> A class uses [[Function Overloading]] in four places. **Constructors** overload to offer several ways to create an object. **Member functions** overload on the object itself: `const` or not, lvalue (`&`) or rvalue (`&&`). **Operators** overload so a user-defined type can be written like a built-in (`a + b`, `v[i]`, `std::cout << x`). And across **inheritance**, a same-named function in a derived class *hides* the base's overloads unless you bring them in, which is different again from *overriding* a virtual function. All four are ordinary compile-time overload resolution applied to a class.

## The Problem

A user-defined type should be as convenient and as safe as a built-in one. An `int` can be created from a literal, copied, compared, added, printed and read through a `const` reference. A `Money` class written with only named methods (`a.add(b).times(3).lessThan(c)`) is clumsy, and one written without `const`-awareness can't even be read through `const Money&`.

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint:** A class's operations are functions. Built-in types get operators, several initialization forms, and correct behaviour for `const` objects and temporaries for free.
> 2. **Consequence:** Without overloading, a class must invent a different name for each creation form, each operator and each `const`/non-const variant, so it can never look or behave like a built-in type.
> 3. **Requirement:** Let a class supply several constructors, several versions of a member keyed on the object's constness and value category, and implementations for the operator symbols, all chosen by the same compile-time rules as ordinary overloads.
> 4. **Design:** Constructors are overloadable functions named after the class. Every non-static member function has a hidden **implicit object parameter** (`*this`), so `const`, `&` and `&&` after the parameter list are just overloading on that parameter. An expression like `a + b` is rewritten to a call, `operator+(a, b)` or `a.operator+(b)`, and resolved like any other call. Name lookup stops at the first scope that declares a name, which is why derived classes hide rather than extend base overloads.
> 5. **Price:** Operators can be given misleading meanings. Implicit converting constructors create surprise conversions. Hiding rules surprise almost everyone once. Getting canonical forms right (`+` from `+=`, both `operator[]` versions, postfix `++`) is boilerplate that C++20 and C++23 are gradually removing.

> [!tension] value ⟷ identity
> Operator overloading is for **value types**: numbers, strings, points, money, where `a + b` and `a == b` have obvious meanings. Types with *identity* (a window, a bank account, a network connection) rarely want arithmetic or equality operators, and giving them some usually misleads.

## Mental Model

> [!model] Every member function has a hidden first parameter
> The compiler treats `r.width() const` roughly as `width(const Rect& self)`, and `r.width()` (non-const) as `width(Rect& self)`. With both declared, a `const Rect` argument can only bind the first, and a non-const one prefers the second, exactly like the `f(const T&)` / `f(T&)` overloads in [[Function Overloading]]. Operators are the same idea again: `a + b` is just a call spelled with a symbol. **Where the model breaks:** the implicit object parameter isn't subject to user-defined conversions, so `2 + money` can never find a *member* `operator+`, only a non-member one (In Code 1). C++23 lets you write the hidden parameter explicitly (`this auto& self`).

```text
  YOU WRITE                         THE COMPILER RESOLVES              MANGLED SYMBOL (Itanium ABI)

  buf.at(3)       (buf non-const)   Buf::at(Buf& self, int)            _ZN3Buf2atEi
  cbuf.at(3)      (cbuf const)      Buf::at(const Buf& self, int)      _ZNK3Buf2atEi    ← K = const
  a + b                             operator+(Meters, Meters)          _Zpl6MetersS_   ← pl = "plus"
  a != b          (C++20)           !(a == b)          rewritten       uses operator==
  a < b           (C++20)           (a <=> b) < 0      rewritten       uses operator<=>
  std::cout << x                    operator<<(std::ostream&, const X&)  (non-member)
```

## Mechanics

### 1 · Constructor overloading

| Kind | Declaration | Resolution notes |
|---|---|---|
| Default | `Point()` / `Point() = default;` | Chosen for `Point p;` and `Point p{};` |
| Value | `Point(double x, double y)` | Ordinary overload by arity and type |
| Converting (one argument) | `Money(long cents)` | Also enables **implicit** conversion `long` → `Money`. Mark it `explicit` unless that conversion is truly natural ([[Conversion Operators and explicit]]) |
| Copy / move | `T(const T&)`, `T(T&&)` | `&` vs `&&` overloads: lvalues copy, rvalues move ([[The Special Member Functions]]) |
| `initializer_list` | `Vec(std::initializer_list<int>)` | **Braces prefer it** over every other constructor when viable: `Vec{3, 7}` ≠ `Vec(3, 7)` |
| Delegating (C++11) | `Point() : Point(0, 0) {}` | Overloads share one real implementation |
| Deleted | `Money(double) = delete;` | Blocks a conversion that would otherwise be picked |

### 2 · Overloading members on the object itself

| Qualifier | Called for | Typical use |
|---|---|---|
| (none) | Any object; for a non-const object when a `const` version also exists | Mutating access: `T& operator[](size_t)` |
| `const` | `const` objects, and through `const&` / pointers to const | Read-only access: `const T& operator[](size_t) const` |
| `&` (C++11) | Lvalue objects only | Forbid a call on temporaries: `T& operator=(const T&) &` |
| `&&` (C++11) | Rvalue objects (temporaries, `std::move`d) | Steal from a dying object: `std::string name() &&` returns by move |
| `this auto& self` (C++23) | Deduced: one template covers `const`/non-const/`&`/`&&` | Replaces duplicated accessor pairs and triplets |

Rule: if any overload of a name has a ref-qualifier, all overloads with the same parameter list must have one. You can't mix `f() &` with a plain `f()`.

### 3 · Operator overloading: the rules

| Rule | Detail |
|---|---|
| At least one operand must be a class or enum type | You can't redefine `int + int` |
| Arity, precedence and associativity are fixed | `a + b * c` still multiplies first |
| Can't overload | `::` `.` `.*` `?:` `sizeof` `typeid` `alignof` `noexcept` and the casts |
| Must be members | `=` `[]` `()` `->` and conversion operators |
| Should be non-members (often `friend`s defined in the class) | Symmetric binary ops `+ - * / == <=>`, and stream `<<` `>>`: both operands then get conversions |
| Lose built-in special behaviour | Overloaded `&&` and `||` don't short-circuit; `,` loses its sequencing before C++17. Don't overload them |
| Prefix vs postfix `++`/`--` | Postfix takes a dummy `int`: `T operator++(int)` returns the old value by value |
| C++20 rewriting | `a != b` may use `operator==`; `<`, `<=`, `>`, `>=` may use `operator<=>`; both may swap operands ([[Comparisons and the Spaceship Operator]]) |
| C++23 | Multidimensional `operator[](i, j)`; `static operator()` and `static operator[]` |

**Canonical forms**, the shapes experienced code converges on:

| Operator | Canonical declaration | Why |
|---|---|---|
| Compound `+=` | `T& operator+=(const T& rhs)` (member), returns `*this` | Modifies the left operand; chains like built-ins |
| Binary `+` | `friend T operator+(T lhs, const T& rhs) { lhs += rhs; return lhs; }` | One implementation (in `+=`); symmetric conversions; returns a new value |
| `==` (C++20) | `bool operator==(const T&) const = default;` | Member-wise; `!=` comes free |
| `<=>` (C++20) | `auto operator<=>(const T&) const = default;` | All four orderings from one line |
| `[]` | `T& operator[](size_t)` **and** `const T& operator[](size_t) const` | Writable and read-only access |
| `++` prefix / postfix | `T& operator++()` / `T operator++(int)` | Postfix returns the old value; prefer prefix |
| `<<` stream | `friend std::ostream& operator<<(std::ostream&, const T&)` | Left operand is the stream, so it can't be a member of `T` |
| `()` | `R operator()(Args...) const` | Makes a function object; lambdas are this |
| Conversion | `explicit operator bool() const` | Allows `if (x)` but not `int n = x;` |

### 4 · Overload vs override vs hide

| | Overload | Override | Hide |
|---|---|---|---|
| Where | Same scope | Derived class, for a `virtual` base function | Derived class declares the same *name* |
| Signature | Different parameter lists | **Same** signature (covariant return allowed) | Any, even different |
| Chosen | At compile time, by argument types | At run time, by the object's dynamic type | Lookup finds the derived name and **stops**: base overloads are invisible |
| Keyword help | — | `override` (C++11) makes a mismatch an error | `using Base::f;` brings the base overloads back |

## Under the Hood

> [!machine] An overloaded operator is an ordinary (usually inlined) function
> `struct Meters { double v; };` with `Meters operator+(Meters, Meters)`, compared with raw `double` addition. GCC 13.3, `-std=c++17 -O2`, x86-64:
> ```nasm
> total(Meters, Meters, Meters):        ; return a + b + c;   (two operator+ calls)
>         addsd  xmm0, xmm1
>         addsd  xmm0, xmm2
>         ret
> total_raw(double, double, double):    ; return a + b + c;   (built-in doubles)
>         addsd  xmm0, xmm1
>         addsd  xmm0, xmm2
>         ret
> ```
> Identical instructions. The strong type costs nothing, the calls are inlined, and a one-`double` struct travels in an `xmm` register. Overload resolution happened during compilation. When not inlined, the operator is an ordinary function with a mangled name (`_Zpl6MetersS_`), and `const` members are distinct symbols (`_ZNK...` vs `_ZN...`) because the implicit object parameter's type differs.

## In Code

**1 · A value type: constructor overloads, `+=`/`+`, comparisons and `<<` (C++11)**

```cpp
#include <iostream>

class Money {
public:
    Money() = default;                                          // ① overloaded constructors
    explicit Money(long cents) : cents_(cents) {}               //   explicit: no silent long → Money
    Money(long dollars, int cents) : Money(dollars * 100 + cents) {}   // delegating (C++11)

    Money& operator+=(const Money& rhs) { cents_ += rhs.cents_; return *this; }
    friend Money operator+(Money lhs, const Money& rhs) { return lhs += rhs; }   // ② symmetric, built on +=
    friend bool operator==(const Money& a, const Money& b) { return a.cents_ == b.cents_; }
    friend bool operator!=(const Money& a, const Money& b) { return !(a == b); }  // free in C++20
    friend bool operator<(const Money& a, const Money& b)  { return a.cents_ < b.cents_; }
    friend std::ostream& operator<<(std::ostream& os, const Money& m) {          // ③ stream is the LEFT operand
        return os << '$' << m.cents_ / 100 << '.' << (m.cents_ % 100 < 10 ? "0" : "") << m.cents_ % 100;
    }
private:
    long cents_ = 0;
};

int main() {
    Money rent(1200, 0), fee(250);                 // $1200.00 and 250 cents
    Money total = rent + fee;
    total += Money(5, 5);
    std::cout << total << ' ' << (fee < rent) << (total != rent) << '\n';
    // Money oops = total + 3;                     // ④ error: no implicit long → Money
}
// expect: $1207.55 11
```
1. Three constructors, picked by arity and type like any overload set.
2. Implementing `+` through `+=` keeps one source of truth. As a non-member (a *hidden friend*, found by [[Name Lookup and ADL]]) both operands are treated symmetrically.
3. `operator<<` can't be a member of `Money`, because its left operand is `std::ostream`.
4. Because the `long` constructor is `explicit`, `total + 3` doesn't compile. Without `explicit`, `3` would silently become three cents.

**2 · Overloading on `const` and on value category**

```cpp
#include <iostream>
#include <string>
#include <utility>
#include <vector>

class Playlist {
public:
    std::string&       operator[](std::size_t i)       { return songs_[i]; }   // ① writable
    const std::string& operator[](std::size_t i) const { return songs_[i]; }   //   read-only
    void add(std::string s) { songs_.push_back(std::move(s)); }

    const std::vector<std::string>& songs() const & { return songs_; }         // ② lvalue: lend a reference
    std::vector<std::string>        songs() &&      { return std::move(songs_); } //  rvalue: hand it over
private:
    std::vector<std::string> songs_;
};

Playlist make() { Playlist p; p.add("intro"); p.add("outro"); return p; }

int main() {
    Playlist p;
    p.add("a"); p.add("b");
    p[0] = "A";                                   // non-const operator[]
    const Playlist& view = p;
    std::cout << view[0] << view[1] << ' ';       // const operator[]
    auto taken = make().songs();                  // ③ && overload: moved out of the temporary
    std::cout << taken.size() << ' ' << p.songs().size() << '\n';
}
// expect: Ab 2 2
```
1. The pair is the standard pattern: the compiler picks by the constness of the object.
2. Ref-qualifiers (C++11) overload on whether the object is an lvalue or an rvalue. Returning a reference to a temporary's member would dangle, so the `&&` version returns by value and moves.
3. `make()` is a prvalue, so `songs() &&` is chosen.

**3 · Overload, override and hide in one hierarchy**

```cpp
#include <iostream>

struct Logger {
    virtual ~Logger() = default;
    virtual void log(const char* msg) { std::cout << "base:" << msg << ' '; }
    void log(int code)                { std::cout << "base-int:" << code << ' '; }   // ① overload
};

struct FileLogger : Logger {
    using Logger::log;                                   // ② without this, log(int) is HIDDEN
    void log(const char* msg) override { std::cout << "file:" << msg << ' '; }   // ③ override
};

int main() {
    FileLogger f;
    Logger& base = f;
    base.log("x");        // virtual: runs FileLogger's override (run-time choice)
    f.log(404);           // found only because of the using-declaration
    f.log("y");
    std::cout << '\n';
}
// expect: file:x base-int:404 file:y
```
1. Two `log` functions in `Logger`: an overload set chosen by argument type.
2. Declaring *any* `log` in `FileLogger` hides *all* of `Logger::log` from lookup through a `FileLogger`. `using Logger::log;` brings them back into the derived scope ([[Name Hiding in Derived Classes]]).
3. `override` makes the compiler verify that this really matches a virtual function. A typo such as `log(std::string)` would otherwise silently create a hiding overload instead ([[override and final]]).

**4 · C++20: defaulted comparisons and rewritten operators**

```cpp
// cc: std=c++20
#include <compare>
#include <iostream>
#include <set>
#include <string>

struct Version {
    int major = 0, minor = 0, patch = 0;
    auto operator<=>(const Version&) const = default;   // ① member-wise, in declaration order
    bool operator==(const Version&) const = default;
};

int main() {
    Version a{1, 4, 2}, b{1, 10, 0};
    std::cout << (a < b) << (a != b) << (b >= a) << ' ';   // ② all rewritten from <=> and ==
    std::set<Version> s{b, a, {0, 9, 9}};
    std::cout << s.begin()->minor << '\n';
}
// expect: 111 9
```
1. Two defaulted lines give all six comparison operators, compared field by field (`major`, then `minor`, then `patch`).
2. The compiler rewrites `a < b` to `(a <=> b) < 0` and `a != b` to `!(a == b)` ([[Comparisons and the Spaceship Operator]]).

**5 · An overload set built from lambdas (C++17)**

```cpp
#include <iostream>
#include <string>
#include <variant>
#include <vector>

template <typename... Fs> struct overloaded : Fs... { using Fs::operator()...; };   // ① inherit every operator()
template <typename... Fs> overloaded(Fs...) -> overloaded<Fs...>;                   //   deduction guide (C++17)

int main() {
    std::vector<std::variant<int, double, std::string>> cells{7, 2.5, std::string("hi")};
    for (const auto& c : cells)
        std::visit(overloaded{
            [](int i)                { std::cout << "int:" << i << ' '; },
            [](double d)             { std::cout << "dbl:" << d << ' '; },
            [](const std::string& s) { std::cout << "str:" << s << ' '; },
        }, c);                                                                      // ② resolution picks per type
    std::cout << '\n';
}
// expect: int:7 dbl:2.5 str:hi
```
1. Each lambda is a class with an `operator()`. Inheriting from all of them and `using` every `operator()` places them in one scope, so they form a single **overload set**.
2. `std::visit` calls the combined object with the active alternative, and ordinary overload resolution picks the matching lambda ([[variant and visit]], [[Lambda Expressions]]).

## Decorators with Classes

Python has three decorator flavours that involve classes: a **class used as a decorator** (an object with `__call__` and state), a **class decorator** (`@counted class Greeter`, which adds behaviour to a whole class), and the classic object-oriented **Decorator pattern** (wrap an object in another that has the same interface). All three map onto C++ features in this note: overloading `operator()`, templates that inherit from their argument, and virtual functions. Function-style decorators (a template returning a wrapping lambda, `@retry(3)`, stacking, decorating overload sets) are covered in [[Function Overloading]], "Decorators: Wrapping Functions Python-Style".

| Python | C++ | Decided |
|---|---|---|
| Class with `__call__` and state, used as `@Memoize` | A class with an overloaded `operator()` and data members | Compile time |
| `@counted class Greeter` (class decorator) | A *mixin* template `Counted<Base> : Base` | Compile time |
| Decorator pattern (wrap an object, same interface) | Abstract base + wrappers that own an inner object | Run time |

**1 · A stateful decorator object: memoization (C++14)**

```cpp
#include <functional>
#include <iostream>
#include <map>

template <typename R, typename Arg>
class Memoized {                                         // ① a decorator with state: a class with operator()
public:
    explicit Memoized(std::function<R(Memoized&, Arg)> f) : f_(std::move(f)) {}
    R operator()(Arg a) {
        auto it = cache_.find(a);
        if (it != cache_.end()) return it->second;       // ② cache hit: the body never runs
        ++computed;
        R r = f_(*this, a);                              // ③ recursion goes back through the cache
        cache_.emplace(a, r);
        return r;
    }
    int computed = 0;
private:
    std::function<R(Memoized&, Arg)> f_;
    std::map<Arg, R> cache_;
};

int main() {
    Memoized<long long, int> fib([](auto& self, int n) -> long long {
        return n < 2 ? n : self(n - 1) + self(n - 2);    // self is the memoized version
    });
    std::cout << fib(50) << ' ' << fib.computed << ' ';
    fib(50);
    std::cout << fib.computed << '\n';                   // second call: pure cache hit
}
// expect: 12586269025 51 51
```
1. `operator()` makes an object callable, so a class can *be* a decorator and remember things between calls (a cache, a counter, a rate limit), like a Python class with `__call__`.
2. On a cache hit the wrapped function doesn't run at all.
3. The subtle part: in Python, `@lru_cache` works for recursion because the name `fib` is rebound, so the inner recursive calls also go through the cache. A C++ function calling *itself* would bypass the decorator. Passing the decorator in as `self` routes every recursive call back through the cache: 51 computations instead of billions.

**2 · A class decorator: a mixin template (C++14)**

```cpp
#include <iostream>
#include <string>

template <typename Base>
struct Counted : Base {                                  // ① a "class decorator": adds behaviour to ANY class
    using Base::Base;                                    //   keep the decorated class's constructors
    template <typename... Args>
    decltype(auto) operator()(Args&&... args) {          // wraps the call operator
        ++calls;
        return Base::operator()(std::forward<Args>(args)...);
    }
    int calls = 0;
};

struct Greeter {
    explicit Greeter(std::string greeting) : greeting_(std::move(greeting)) {}
    std::string operator()(const std::string& name) const { return greeting_ + ", " + name; }
private:
    std::string greeting_;
};

int main() {
    Counted<Greeter> hello("Hello");                     // ② like  @counted class Greeter
    std::cout << hello("Ada") << " | " << hello("Linus") << " | calls=" << hello.calls << '\n';
}
// expect: Hello, Ada | Hello, Linus | calls=2
```
1. `Counted<Base>` inherits from whatever class it decorates and wraps its `operator()`: behaviour added to *any* class without editing it. `using Base::Base;` (C++11 inheriting constructors) keeps the original constructors.
2. `Counted<Greeter>` reads like `@counted` applied to `Greeter`. Everything is resolved at compile time; the wrapper adds one increment.

**3 · The Decorator pattern: wrapping objects at run time**

```text
  log->write("connected")
   │
   ▼
  ┌ Tagged ──────────────────────────────────────────────┐
  │ write(s) → inner("db: " + s)                         │
  │ inner:                                               │
  │   ┌ Timestamped ─────────────────────────────┐       │
  │   │ write(s) → inner("[12:00] " + s)         │       │
  │   │ inner:                                   │       │
  │   │   ┌ Console ───────────┐                 │       │
  │   │   │ std::cout << s     │                 │       │
  │   │   └────────────────────┘                 │       │
  │   └──────────────────────────────────────────┘       │
  └──────────────────────────────────────────────────────┘
```
Each layer adds its piece and forwards to the one inside it: the call travels inward, and the text arrives at `std::cout` as `[12:00] db: connected`.

```cpp
#include <iostream>
#include <memory>
#include <string>

struct Sink {                                            // ① the interface every layer implements
    virtual ~Sink() = default;
    virtual void write(const std::string& s) = 0;
};
struct Console : Sink {
    void write(const std::string& s) override { std::cout << s << '\n'; }
};
struct Timestamped : Sink {                              // ② a decorator IS-A Sink and HAS-A Sink
    explicit Timestamped(std::unique_ptr<Sink> inner) : inner_(std::move(inner)) {}
    void write(const std::string& s) override { inner_->write("[12:00] " + s); }
private:
    std::unique_ptr<Sink> inner_;
};
struct Tagged : Sink {
    Tagged(std::string tag, std::unique_ptr<Sink> inner) : tag_(std::move(tag)), inner_(std::move(inner)) {}
    void write(const std::string& s) override { inner_->write(tag_ + ": " + s); }
private:
    std::string tag_;
    std::unique_ptr<Sink> inner_;
};

int main() {
    std::unique_ptr<Sink> log =                          // ③ layers chosen and stacked at run time
        std::make_unique<Tagged>("db", std::make_unique<Timestamped>(std::make_unique<Console>()));
    log->write("connected");
}
// expect: [12:00] db: connected
```
1. The interface every layer shares.
2. Each decorator both **is** a `Sink` (so callers can't tell the difference) and **owns** an inner `Sink` it forwards to after adding its behaviour. This is the object-oriented Decorator pattern.
3. Layers are chosen and stacked while the program runs. The cost is one virtual call per layer ([[Virtual Dispatch — vptr and vtable]]). The mixin in the previous example is its compile-time counterpart: faster, but fixed when you compile.

## Pitfalls

> [!trap] Implicit converting constructors
> A one-argument constructor that isn't `explicit` is also an implicit conversion. `void pay(Money); pay(500);` compiles and means 500 cents, or worse. Mark single-argument constructors `explicit` by default (Core Guidelines C.46).

> [!trap] Braces pick the `initializer_list` constructor
> If a class has an `initializer_list` constructor, `T{a, b}` chooses it whenever it's viable, even when another constructor matches better. `std::vector<int>{3, 7}` holds two elements, `std::vector<int>(3, 7)` holds three ([[Header — vector]]).

> [!trap] A derived-class function hides every base overload
> Declaring `void f(double)` in a derived class makes all base `f(...)` overloads invisible through the derived type, even ones with a better match. Add `using Base::f;` (In Code 3).

> [!trap] Operators with surprising meanings or signatures
> `operator+` that modifies its left operand, `operator==` that isn't symmetric, postfix `++` that returns a reference, or `operator+` returning a reference to a local all violate what readers assume. Follow the canonical forms, and don't overload `&&`, `||`, `,` or unary `&`.

> [!ub] Returning a reference from an `&&`-qualified accessor
> `const std::string& name() && { return name_; }` returns a reference into a temporary that dies at the end of the full-expression: `auto& n = make().name();` dangles. `&&` accessors should return by value (In Code 2) ([[Dangling Pointers and References]]).

> [!trap] Member `operator+` breaks symmetry
> With `Money Money::operator+(const Money&) const`, `money + 5` can convert `5` (if the constructor allows) but `5 + money` never can, because the implicit object parameter doesn't accept conversions. Make symmetric operators non-members.

## Evolution

| Standard | Change | Why |
|---|---|---|
| **C++98** | Constructor, member, `const` and operator overloading; `explicit` constructors | User-defined types that behave like built-ins |
| **C++11** | Delegating constructors; `= default`/`= delete`; move constructor/assignment overloads; ref-qualifiers `&`/`&&`; `initializer_list` constructors; `explicit operator bool`; `override`/`final` | Less duplication; move-aware overloads; safe conversions; checked overriding |
| C++17 | Class template argument deduction and deduction guides (the `overloaded` idiom); defined order for overloaded `<<`, `>>` and `,` operands | Build overload sets from lambdas; `cout << f() << g()` evaluates left to right |
| **C++20** | Defaulted `==` and `<=>`; rewritten comparison candidates; `explicit(bool)` | Six comparison operators from one line; conditional explicitness in generic wrappers |
| **C++23** | Explicit object parameter ("deducing `this`"); multidimensional `operator[]`; `static operator()` and `static operator[]` | One member template replaces `const`/non-const/`&&` duplicates; `m[i, j]` for matrices |

## Connections

- **Prerequisites:** [[Function Overloading]] (the underlying mechanism) · [[Classes as User-Defined Types]].
- **Deep dives:** [[Operator Overloading]] (every operator in detail) · [[Constructors]] · [[The Special Member Functions]] · [[Comparisons and the Spaceship Operator]] · [[Conversion Operators and explicit]].
- **Inheritance:** [[Name Hiding in Derived Classes]] · [[override and final]] · [[Virtual Functions]] · [[Inheritance]].
- **Resolution details:** [[Overload Resolution]] · [[Name Lookup and ADL]] (why hidden friends are found).
- **Related:** [[Move Semantics]] · [[Rvalue References]] · [[variant and visit]] · [[Lambda Expressions]].
- **Decorators:** [[Function Overloading]] (function decorators) · [[Callables and std-function]] · [[Virtual Dispatch — vptr and vtable]] · [[Composition vs Inheritance]].
- **Practice:** *Continuum #19 Complex Number & Vector Math Library* (implement `+=`/`+`, `==`/`<=>` and `<<` in canonical form, and check that `2.0 * v` and `v * 2.0` both compile) · *#17 Bank Account Simulator* (an `explicit` `Money` type; decide which operators an `Account` should *not* have).

## Check Yourself

> [!quiz]- Why is `operator<<` for printing always a non-member, while `operator[]` must be a member?
> A member operator's left operand is the object itself. For printing, the left operand is `std::ostream`, a class you can't add members to, so it must be a non-member `operator<<(std::ostream&, const T&)`. The language requires `=`, `[]`, `()` and `->` to be members so their left operand is always an object of the class.

> [!quiz]- A class declares `T& get()` and `const T& get() const`. Which one runs for `obj.get()` when `obj` is non-const, and when it's reached through a `const&`?
> Non-const object: `get()` (the implicit object parameter `T&` is an exact match without adding `const`). Through a `const&`: only `get() const` is viable. It's ordinary overloading on the hidden `*this` parameter.

> [!quiz]- Spot the bug: `struct B { void f(int); }; struct D : B { void f(double); }; D d; d.f(1);`. Which function runs?
> `D::f(double)`, with `1` converted to `1.0`. `D`'s declaration of `f` hides `B::f(int)`, so the better-matching base overload isn't even a candidate. Fix with `using B::f;` inside `D`.

> [!quiz]- A memoizing decorator object wraps a recursive `fib`, yet `fib(40)` is still slow. Why, and what's the fix?
> The body's recursive calls invoke the original function by name, not the decorator, so only the outermost call is cached. Python avoids this because `@lru_cache` rebinds the name `fib`. In C++, make the recursion go through the decorator, for example by passing it into the body as a `self` parameter (Decorators with Classes, first example).

## Sources

- Primer §7.1 "Defining Abstract Data Types" (p. 254) and §7.3 "Additional Class Features" (p. 271; overloading based on `const`, p. 276): constructors and `const` member overloads.
- Primer §13.6.3 "Rvalue References and Member Functions" (reference functions, p. 547): `&`/`&&`-qualified members.
- Primer ch. 14 "Overloaded Operations and Conversions": §14.1 "Basic Concepts" (p. 552), I/O operators (p. 556), arithmetic and relational (p. 560), assignment (p. 563), subscript (p. 564), increment/decrement (p. 566), function-call (p. 571), and §14.9 "Overloading, Conversions, and Operators" (p. 579; function matching and overloaded operators, p. 587).
- Primer §15.6 "Class Scope under Inheritance" (p. 617; name collisions and inheritance, p. 618): why derived names hide base overloads.
- Tour §6.4 "Operator Overloading" (p. 80) and §6.5 "Conventional Operations" (p. 81): which operators to define and their conventional meanings.
- PPP ch. 8, §8.6 "Operator overloading"; ch. 9, §9.6–9.7: user-defined `<<` and `>>`.
- cppreference / web, *operator overloading*, *Member functions* (const-, ref-qualified), *Default comparisons*: https://en.cppreference.com/w/cpp/language/operators · https://en.cppreference.com/w/cpp/language/member_functions · https://en.cppreference.com/w/cpp/language/default_comparisons
- Gamma, Helm, Johnson, Vlissides, *Design Patterns* (1994), "Decorator": the object-wrapping pattern in the third decorator example. Python PEP 318 and PEP 3129 (function and class decorators): https://peps.python.org/pep-0318/ · https://peps.python.org/pep-3129/
- C++ Core Guidelines C.46 "By default, declare single-argument constructors `explicit`", C.161 "Use non-member functions for symmetric operators", C.162–C.163, C.167 "Use an operator for an operation with its conventional meaning", C.128 (virtual, `override`, `final`): https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
