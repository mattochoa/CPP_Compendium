---
id: const-correctness
title: const and Const-Correctness
aliases:
- const correctness
- top-level const
- low-level const
type: concept
domain: D02
tier: 1
status: reviewed
standard: C++98
prereqs:
- "[[Fundamental Types]]"
related:
- "[[Top-Level vs Low-Level const]]"
- "[[constexpr Variables and Constant Expressions]]"
- "[[References]]"
- "[[Pointers]]"
- "[[The Named Casts]]"
practice:
- 17
- 19
tags:
- type/concept
- domain/d02
- tier/1
- tension/safety-vs-performance
- std/c++98
created: 2026-09-26
updated: 2026-09-26
reviewed: 2026-09-27
score: 20
rubric:
  accuracy: 3
  first_principles: 3
  clarity: 3
  depth: 3
  visual: 2
  code: 3
  integration: 3
---

# const and Const-Correctness

> [!essence]
> `const` is a compile-time promise attached to a name: *through this expression, the object may not be modified*. **Const-correctness** is the discipline of stating that promise everywhere it is true — in variables, references, pointers, and member functions — so the type system, not the reader's memory, catches every place the promise would be broken.

## The Problem

A program is full of names that must never be written through at a particular point: a function that only inspects its argument, a getter that reports a class's state without changing it, a buffer size fixed once at startup. Nothing about the type `int` or `std::string` says which of its objects are meant to be read-only; that meaning lives only in the programmer's head, unless the language gives it somewhere else to live.

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint.** Many names in a program refer to objects that a given function, or a given piece of code, must only read. The compiler cannot infer this from the object's type alone — `int` supports both reading and writing, and nothing distinguishes "this int must not change here" from any other `int`.
> 2. **Consequence.** Left unstated, that intent is enforced only by the programmer remembering it. A stray `=` where `==` was meant, a refactor that adds a write three call-frames deep, or a caller who assumes a function won't touch its argument (and is wrong) — none of these are caught, because nothing in the type system was ever told the rule.
> 3. **Requirement.** The language needs a promise that (a) is checked by the compiler rather than trusted to convention, (b) costs nothing at run time, since the underlying object is exactly as mutable as it always was, and (c) attaches at every layer where "read-only from here" can be said: a variable, a reference, a pointer, and the implicit object a member function operates on.
> 4. **Design.** `const` qualifies a type, producing a distinct const-qualified version of it (`[basic.type.qualifier]`). A const object may not be modified through an expression of that type; a reference or pointer to a const-qualified type may not be used to write to what it refers to; and a member function marked `const` receives a const-qualified `this`, so it cannot write to the object's non-`mutable` members. One qualifier, applied uniformly, closes off every ordinary write path.
> 5. **Price.** The promise is purely about what you may do *through a given expression*, not a fact about the referred-to storage — so `const` does not, by itself, mean the bytes are frozen (see Pitfalls). And because the promise is contagious — a function can only pass a `const T&` on to something that itself promises not to write — committing to it in one place tends to require restating it everywhere that value flows. That discipline, applied consistently across a whole interface, is what "const-correctness" names.

> [!tension] safety ⟷ performance
> `const` buys exactly the kind of safety this Atlas keeps returning to: a rule the compiler enforces *before* the program runs, so that catching the mistake costs nothing while the program is running. [[Map — Types & Values|The domain's core tension]] is resolved here in safety's favor without spending a single byte or instruction on it — the qualifier disappears entirely once compilation ends (see Under the Hood).

## Mental Model

> [!model] A read-only window onto a room
> A `const` reference or pointer is a window onto an object: you can see the room's current contents through it, but you cannot reach through the glass to rearrange anything. The room itself is unaffected by the window's existence.
> **Where it breaks:** a room can have more than one opening. If someone rearranges the furniture through a different, non-const door while you watch through your window, the room changes anyway — your window was only ever a promise about *your* access, not a lock on the room. `const` restricts an expression, not the underlying object's mutability in general.

The qualifier can attach independently to two different things whenever a pointer is involved: the pointer itself, and the object it points to. Primer's terms for this split are now in wide use:

```text
                          is the OBJECT the pointer refers to const?
                          no                        yes
                    ┌─────────────────────────┬─────────────────────────┐
  is the POINTER    │                         │                         │
  itself const?      │      int *p             │      const int *p       │
             no      │  read/write object,     │  read-only object,      │
                     │  reseat p freely         │  reseat p freely        │
                    ├─────────────────────────┼─────────────────────────┤
             yes     │      int *const p        │  const int *const p     │
                     │  read/write object,      │  read-only object,      │
                     │  p is fixed once set     │  p is fixed once set    │
                    └─────────────────────────┴─────────────────────────┘
                       "low-level const" runs along the top edge — it says
                       what you may do to the OBJECT through this name.
                       "top-level const" runs down the side — it says
                       whether the NAME ITSELF may be reassigned.
```

A reference has no top-level column: a reference is not an object, so there is nothing to make const *besides* what it refers to — every "const reference" is really a reference to a const type, which is why Primer calls the popular phrase "const reference" a convenient but technically loose abbreviation.

## Mechanics

| Situation | Rule | Example |
|---|---|---|
| Reference to const | Binds to const or non-const objects, literals, and temporaries; cannot write through the reference | `const int &r = i;` |
| Pointer to const (low-level) | May point at a const or non-const object; the pointer itself may still be reseated | `const int *p = &i; p = &j;` — OK |
| Const pointer (top-level) | The pointer's own address binding is fixed after initialization; what it points to may still be written, unless that type is also const | `int *const p = &i; *p = 5;` — OK; `p = &j;` — error |
| const member function | The implicit object parameter is const-qualified; may call other `const` members, may not write non-`mutable` data members | `double balance() const { return balance_; }` |
| Copying past top-level const | Ignored — copying an object never changes the source, so its top-level const is immaterial to the copy | `int j = ci;` is legal even though `ci` is `const int` |
| Copying past low-level const | Never ignored without an explicit cast — a plain pointer cannot be initialized from a pointer to const | `int *p = pc;` where `pc` is `const int*` — error |

> [!standard] What "top-level" actually means, and what doesn't have a Standard name
> `[basic.type.qualifier]` ¶6 defines the term precisely: for a type "*cv* T", the **top-level cv-qualifiers** are the ones denoted by *cv* itself, not any qualifier buried inside T. `const int *const` has the top-level qualifier `const` (the pointer); `const int&` has *no* top-level qualifier — the reference type itself is never cv-qualified, only what it refers to. "Low-level const" is Primer's teaching term for the complementary case (a qualifier that survives *through* an indirection); the Standard doesn't name it separately, but the behavior — that it is never dropped silently on assignment or copy — comes from the qualification-conversion rules (`[conv.qual]`), which let an implicit conversion *add* cv-qualifiers below the top level of a pointer type but never remove one; `[basic.type.qualifier]` ¶5 supplies the "more cv-qualified" ordering those rules are stated in.

**Const member functions and `this`.** Only a member function can be marked `const`, because only a member function has an implicit object to protect — free functions must say the same thing explicitly, with a `const` parameter type.

> [!standard] What the implicit object parameter actually is
> Primer's C++11-era account says the implicit `this` inside a `const` member function has type "`const X *const`" — a const pointer to a const `X` — matching the intuition that `this` can never be reseated. The modern Standard states it more precisely: `this` is a **prvalue** of type "pointer to *cv-qualifier-seq* X" (`[expr.prim.this]` ¶4). Because a prvalue has no identity to reassign in the first place, `this` cannot be "reseated" for a reason one level more fundamental than "it's a const pointer" — there's no variable there to write to at all.

**Overload resolution follows constness too.** A `const` member function can be called on both const and non-const objects; a non-`const` member function can be called only on a non-const object (Tour §5.2). When both are defined, the compiler prefers the non-`const` overload for a non-const object and falls back to the `const` overload otherwise — the same "most specific match wins" rule that governs every other overload set.

## Under the Hood

> [!machine] The qualifier costs nothing — it doesn't survive to codegen
> Two accessor functions, identical except for the qualifier, compiled with GCC 11, `-O2`, x86-64:
> ```nasm
> getx_const(Point const&):    ; int getx_const(const Point& p) { return p.x; }
>     mov  eax, DWORD PTR [rdi]
>     ret
> getx_plain(Point&):          ; int getx_plain(Point& p) { return p.x; }
>     mov  eax, DWORD PTR [rdi]
>     ret
> ```
> The generated instructions are byte-for-byte identical. `const` changes only the *mangled name* (`RK5Point` versus `R5Point`) — enough for the compiler and linker to tell the two overloads apart — and which call sites are legal. It leaves no trace in the object code: no flag, no check, no branch. This is `const`'s share of [[Map — What C++ Is|zero overhead]]: the entire cost of the promise is paid once, by the compiler, before the program exists.

## In Code

**1 · Top-level and low-level const, side by side**

```cpp
#include <iostream>

int main() {
    int i = 0;
    const int ci = i;             // ① top-level const: ci itself can't be reassigned
    const int *cp = &i;           // ② low-level const: can't write *cp; cp itself can be reseated
    cp = &ci;                     // ③ fine — reseating cp doesn't touch what it points to
    int *const fixed = &i;        // ④ top-level const: fixed can't be reseated
    *fixed = 5;                   // ⑤ fine — writing through fixed is allowed

    int copy_of_ci = ci;          // ⑥ ci's top-level const is ignored when copying
    const int &r = i;             // ⑦ a "const reference": low-level const on a reference
    std::cout << *cp << ' ' << copy_of_ci << ' ' << r << '\n';
}
// expect: 0 0 5
```
1. `ci` cannot appear on the left of `=` again; this is the const the Standard calls top-level.
2. `cp` may be pointed elsewhere, but never used to write to whatever it points at.
3. Reseating a pointer never writes to either object, so a pointer's own top-level const is irrelevant here — `cp` now points at `ci`, whose value is `0`.
4. `fixed`'s *address* is locked in at initialization; it still points at `i`, not `ci`.
5. `fixed`'s low-level qualification is absent — the pointee is plain `int` — so writing through it is legal, and it changes `i`, not `ci`.
6. Copying reads `ci`'s value (`0`); the value doesn't care that its source was const.
7. `r` is bound to `i`, which step 5 changed to `5` — `r` reports that current value, not the `0` `i` started with.

**2 · A const member function, and what happens without one**

```cpp
#include <iostream>

class Account {
public:
    explicit Account(double balance) : balance_(balance) {}
    double balance() const { return balance_; }     // ①
    void deposit(double amt) { balance_ += amt; }    // ②
private:
    double balance_;
};

void print_balance(const Account &a) {               // ③
    std::cout << a.balance() << '\n';                 // ④
}

int main() { print_balance(Account{100.0}); }
// expect: 100
```
1. `const` after the parameter list: this function's implicit object is read-only.
2. No `const`: this function is only callable on a non-const `Account`.
3. `a` is a reference to const — so only `Account`'s `const` members are reachable through it.
4. `balance()` qualifies; calling `a.deposit(10.0)` here would not compile — see Pitfalls.

**3 · `mutable`: an escape hatch for state outside the object's logical value**

```cpp
#include <iostream>

class Account {
public:
    explicit Account(double balance) : balance_(balance) {}
    double balance() const {
        ++access_count_;                 // ① allowed: access_count_ is mutable
        return balance_;
    }
    int access_count() const { return access_count_; }
private:
    double balance_;
    mutable int access_count_ = 0;       // ② not part of the account's observable value
};

int main() {
    const Account acc(100.0);            // ③ acc itself is const...
    acc.balance();
    acc.balance();
    std::cout << acc.access_count() << '\n';  // ④ ...yet this changed
}
// expect: 2
```
1. A `mutable` member is never `const`, even inside a `const` member function — `[basic.type.qualifier]` excludes it explicitly from what a "const object" covers.
2. It tracks bookkeeping (here, a call counter), not the account's balance.
3. `acc` is fully const; only its `mutable` member may still change.
4. Two calls to the read-only `balance()` bumped the counter — this is **logical constness**: the object's observable state didn't change, even though a byte inside it did.

## Pitfalls

> [!trap] `const` only protects the expression you used, not the object in general
> `const int &visible = stock;` gives you a read-only *view*. If some other, non-const name for the same object writes to it, `visible` reports the new value on the very next read — the window model above breaks exactly here. `const` never implies "frozen"; it implies "not writable through this name."

> [!trap] Calling a non-`const` member function through a const reference is ill-formed, not undefined
> GCC rejects this at compile time (`discards qualifiers`) — exactly the point of the design: the mistake never reaches a running program.

```cpp
// cc: ill-formed
class Account {
public:
    explicit Account(double balance) : balance_(balance) {}
    void deposit(double amt) { balance_ += amt; }
private:
    double balance_;
};

void print_balance(const Account &a) {
    a.deposit(10.0);   // error: passing 'const Account' as 'this' discards qualifiers
}

int main() {}
```

> [!ub] `const_cast` away from a genuinely const object, then writing
> `const_cast` can strip `const` from the *type* of an expression, but it cannot change whether the *object* is actually const. Writing through the result is undefined behavior precisely when the underlying object was declared `const`:

```cpp
// cc: ub
#include <iostream>

int main() {
    const int limit = 100;                     // ① a genuinely const object
    int &sneaky = const_cast<int&>(limit);
    sneaky = 200;                               // ② UB: limit is truly const
    std::cout << limit << '\n';                 // ③ not defined what prints here
}
```
1. `limit` is const all the way down — there is no non-const alias anywhere for this one.
2. The cast compiles; the *write* is what is undefined, per cppreference's own `const_cast` example distinguishing this from writing through a const-qualified alias to an originally non-const object (which is well-defined). See [[The Named Casts]].
3. Never write prose that predicts a UB program's output; say only that the Standard imposes no requirement here.

## Evolution

See [[Map — Evolution of C++]] for the language-wide timeline.

| Standard | Change | Why |
|---|---|---|
| C (ANSI, 1989) | `const` qualifier added to C, with weaker rules (e.g., file-scope `const` still has external linkage by default) | An early attempt at compiler-checked read-only objects, inherited and then tightened by C++ |
| **C++98** | `const` fully integrated: references and pointers to const, const member functions with a const-qualified `this`, `mutable` data members | Const-correctness needed to reach every layer — variables, indirection, and class interfaces — not just plain objects |
| C++11 | `auto` is defined to strip top-level const (and references) from its deduced type by default | A deduction rule had to say explicitly which kind of const survives, now that types were inferred rather than written |
| C++20 | `consteval` and `constinit` join `const`/`constexpr` as further compile-time specifiers, each fixing a narrower promise `const` alone couldn't state (respectively: must run at compile time; must be constant-*initialized*, mutable after) | `const`'s single promise — "not writable through this name" — needed siblings once code wanted to promise *more* than that, without overloading `const` itself to mean several things |

## Connections

- **Prerequisites:** [[Fundamental Types]] — `const` qualifies exactly the values/operations/representation triple that note establishes.
- **Enables:** [[Top-Level vs Low-Level const]] (the comparison this note's Mental Model previews) → [[constexpr Variables and Constant Expressions]] (asking the compiler to *prove* a value, not just freeze a name).
- **Siblings:** [[References]] and [[Pointers]] — const's rules are stated in terms of both; [[The Named Casts]] — `const_cast` is the only sanctioned way to remove a const qualifier, and only ever safe when the underlying object was never const to begin with.
- **Domain:** [[Map — Types & Values]].
- **Practice:** *Continuum #17 Bank Account Simulator*: mark every accessor `const` and watch which callers now fail to compile until they stop trying to mutate through a read-only reference. *Continuum #19 Complex Number & Vector Math Library*: operator overloads that only read their operands should take `const&` parameters and be `const` member functions themselves.

## Check Yourself

> [!quiz]- What's the difference between a "top-level" and a "low-level" const, and which one does copying an object ignore?
> Top-level const says the *name itself* can't be reassigned; low-level const says the *object reached through an indirection* can't be written to. Copying ignores top-level const (the source's constness doesn't affect the copy) but never ignores low-level const without an explicit conversion.

> [!quiz]- Why can a `mutable` member change inside a `const` member function, and why doesn't this violate const-correctness?
> `[basic.type.qualifier]` explicitly excludes `mutable` subobjects from what counts as part of a const object. Used correctly (bookkeeping like a cache or a call counter, never the type's logical value), changing it doesn't alter what the object *means* to its callers — only what it costs to compute that meaning again.

> [!quiz]- Predict: `int x = 1; const int &r = x; x = 2; std::cout << r;` — what prints, and why?
> `2`. `r` is a read-only *view* of `x`, not a frozen snapshot. Writing to `x` through its own, non-const name changes what `r` reports on the next read, because `r`'s constness only ever restricted what could be done *through r*.

> [!quiz]- Is `void f(const Widget w)` (by value, not by reference) meaningfully const-correct in the way `void f(const Widget &w)` is?
> Not for the caller: a by-value parameter is the callee's own copy, so its constness is a private implementation detail — the caller's object was never at risk either way. It only matters *inside* `f`, where it stops that local copy from being accidentally reassigned.

## Sources

- Primer §2.4 "const Qualifier" (p. 59): the initialization requirement and why const objects are file-local by default. §2.4.1 "References to const" (p. 61): binding rules, and the "const reference" abbreviation warning. §2.4.2 "Pointers and const" (p. 62): pointer-to-const versus const-pointer, stated side by side. §2.4.3 "Top-Level const" (p. 64): the exact top-level/low-level terminology and the copying rule for each.
- Primer §7.1 "Defining Abstract Data Types" (p. 258): the implicit `this` pointer, and how a trailing `const` changes its type.
- Primer §7.3 "Additional Class Features" (p. 274): `mutable` data members and why a const member function may still write to one.
- Tour §5.2 "Concrete Types" (p. 56): the overload-resolution rule — a const member function callable on both const and non-const objects, a non-const one only on non-const objects.
- Pikus, ch. "Data Structures for Concurrency," §"The thread-safe stack" (p. 249): the caution that a `mutable` member must stay outside an object's logical state, illustrated with a mutex that has to be mutable to let a read-only lookup be declared `const`.
- cppreference, *cv (const and volatile) type qualifiers*: definition of a const object, the `mutable` specifier and its "M&M rule" mutex example, and the ordering on cv-qualifiers: https://en.cppreference.com/w/cpp/language/cv
- cppreference, *const_cast*: the distinction between casting away const on an originally non-const object (defined) and writing through it on a genuinely const object (undefined): https://en.cppreference.com/w/cpp/language/const_cast
- Draft standard `[basic.type.qualifier]` — the four-way cv-qualification of a type, the definition of a const object (¶1.1, excluding mutable subobjects), and the precise definition of "top-level cv-qualifier" (¶6): https://eel.is/c++draft/basic.type.qualifier
- Draft standard `[expr.prim.this]` ¶4 — `this` as a prvalue of pointer-to-*cv*-X type: https://eel.is/c++draft/expr.prim.this
- C++ Core Guidelines Con.1 ("By default, make objects immutable"), Con.2 ("By default, make member functions const"), Con.3 ("By default, pass pointers and references to consts"): https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
