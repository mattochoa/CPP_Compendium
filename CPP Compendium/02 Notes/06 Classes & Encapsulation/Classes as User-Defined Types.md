---
id: classes-as-types
title: Classes as User-Defined Types
type: concept
domain: D06
tier: 1
status: reviewed
standard: C++98
prereqs:
- "[[What a Type Is]]"
related:
- "[[Encapsulation and Class Invariants]]"
- "[[struct vs class]]"
- "[[Constructors]]"
- "[[The this Pointer and Member Function Calls]]"
- "[[Aggregates and Designated Initializers]]"
practice:
- 17
tags:
- type/concept
- domain/d06
- tier/1
- tension/abstraction-vs-control
created: 2026-09-25
updated: 2026-09-26
reviewed: 2026-09-27
score: 20
rubric:
  accuracy: 3
  first_principles: 3
  clarity: 3
  depth: 2
  visual: 3
  code: 3
  integration: 3
---

# Classes as User-Defined Types

> [!essence]
> [[What a Type Is|A type]] is a fixed answer to three questions: which values, which operations, which representation. A `class` definition is where a programmer supplies that answer instead of the language — and the instant it compiles, the class's name is a type in exactly the sense `int` is: usable in a variable, a parameter, an array, a `std::vector`, with no different rules for the compiler to apply.

## The Problem

C++'s built-in types are a short, fixed list, settled once by the language and the hardware it targets: a handful of integer and floating-point widths, `bool`, `char`, and pointers. A real program is rarely about integers and doubles for their own sake — it is about an `Account`, a `Date`, a `Token`. None of those concepts exists in the language until a programmer puts it there.

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint.** The compiler already knows the representation and legal operations of a built-in type without being told — `int` needs no declaration to teach the compiler what it means (PPP §8.1). A domain concept like an account balance has no such built-in entry.
> 2. **Consequence.** Without a way to add one, a programmer fakes the concept with loose built-in variables and a naming convention — an account as a separate `long accountNumber` and `double balance`, passed around together by agreement. The compiler enforces nothing about that agreement: nothing stops the two from drifting apart, being passed in the wrong order, or being combined with a third pair that belongs to a different account entirely.
> 3. **Requirement.** The language needs a construct that bundles the representation into one unit and lets the programmer declare, once, exactly which operations are legal on it — supplying the same values × operations × representation triple that already fixes a built-in type's meaning ([[What a Type Is]]) — so the compiler checks the new concept exactly as strictly as it checks `int`.
> 4. **Design.** The `class` is that construct. Its data members fix the representation; its member functions (and any declared `friend`s) fix the operations. Tour §5.1.1 (p. 54) is direct about the purpose: a class stands in the program for some entity the design cares about, as a genuine type rather than a comment or a convention — and the defining trait of an ordinary ("concrete") class is that its representation is truly part of its definition, which is exactly what lets objects of it live on the stack, inside other objects, and be initialized immediately, the same privileges a built-in type already has (Tour §5.2, p. 54).
> 5. **Price.** The compiler does not invent sensible behavior for a new concept the way it already has one for `int`. Left undeclared, an operation on a class simply does not exist — Example 4 below shows the compiler refusing a comparison nobody asked for. And declaring the representation and the operations is only two-thirds of the triple: which *values* are actually reachable is still wide open. A class as this note leaves it can still be built from any combination of member values, however nonsensical — that problem belongs to [[Encapsulation and Class Invariants]], next.

> [!tension] abstraction ⟷ control
> Defining `Account` as a class lets the rest of the program stop thinking in terms of a loose `long` and a loose `double` and start thinking in terms of one account — real abstraction, not a comment promising the two variables belong together. But nothing about that abstraction is free at compile time: every operation the class offers had to be written by a programmer, member by member, function by function. And nothing about it costs anything at run time either — see *Under the Hood*. The abstraction is bought with declarations, not with a slower program.

## Mental Model

> [!model] A class declaration is a factory's specification sheet, not an inspector
> A spec sheet lists exactly which raw materials go into a unit (its data members) and exactly which operations the factory line is tooled to perform on it (its member functions). Two units built to the same sheet are interchangeable in every way the sheet describes.
> **Where it breaks:** a spec sheet trusts that anything matching its shape is a sensible unit. It has no inspector standing at the end of the line rejecting a car with a valid-looking chassis but no engine bolted where the engine is supposed to be. A class, as this note leaves it, is the same: it fixes *shape*, not *sense*. Posting an inspector at the door — a constructor that refuses bad combinations, representation nothing outside can reach — is what [[Encapsulation and Class Invariants]] adds next.

The same triple `class` supplies for `Account`, drawn next to the general shape from [[What a Type Is]]:

```text
  class Account {                              TYPE = Account
    private:                                  ┌─────────────────────────────┐
      long number_;         ───────┐          │ VALUES                      │
      double balance_;      ──────┐│          │  any (long, double) pair —  │
    public:                       ││          │  this class enforces none   │
      Account(long, double);──┐   ││   ┌─────▶│  yet (see Encapsulation)    │
      void deposit(double); ──┤   ││   │      ├─────────────────────────────┤
      double balance() const;─┘   ││   │      │ OPERATIONS                  │
  };                              ││   │ ┌───▶│  Account(long,double),      │
                                  ││   │ │    │  deposit(double), balance() │
   member functions ──────────────┼┼───┘─┘    │  — nothing else declared    │
   data members ────────────────────┘──────┐  ├─────────────────────────────┤
                                             └─▶│ REPRESENTATION              │
                                                │  16 bytes: long + double   │
                                                │  (sizeof(Account) == 16)   │
                                                └─────────────────────────────┘
```

Nothing here is a new kind of thing. It is the same triple, filled in by a class body instead of by the language's own definition of `int`.

## Mechanics

> [!standard] A class name is a type name, grammatically
> A class is introduced by a *class-specifier* — the construct `class Account { ... }` or `struct Account { ... }` — which the Standard places among the things a declaration's type can be written as, and which it calls a *class definition* once its closing brace is reached (`[class.pre]`). Because a class-specifier occupies the same grammatical slot a built-in type name does, nothing downstream in the language needs a special case for "the type is a class" versus "the type is `int`": a class name is simply accepted wherever a type name is.

| Situation | Rule | Example |
|---|---|---|
| Declaring the type | `class Name { members };` or `struct Name { members };` introduces `Name` as a type; the two keywords differ only in default member access, not in kind (full comparison in [[struct vs class]]) | `class Account { ... };` |
| Data members | Fix the representation leg: `sizeof(T)` is at least the sum of the non-static data members' sizes, plus any alignment padding between them | `long number_; double balance_;` → `sizeof(Account) == 16` |
| Member functions | Fix the operations leg: only a declared member (or `friend`) may follow `.` on an object of the type; anything else is rejected, whatever the hardware could physically do. "Declared" here means what it means for any function — a name plus a fixed type ([[Anatomy of a Function]]) | `a.deposit(50.0);` compiles; `a.frobnicate();` does not, if undeclared |
| No user-declared constructor, no private data, no virtual functions | The class is an **aggregate**: it declares no operations beyond what the compiler always supplies, and can be initialized member by member with `{}` | `struct Point { double x, y; }; Point p{1.0, 2.0};` — full rule in [[Aggregates and Designated Initializers]] |
| Using the finished type | `Name` is now usable everywhere a type name is: as a variable, a parameter or return type, an array element type, a template argument | `std::vector<Account> ledger;` |

The dot in `a.deposit(50.0)` is the language's *object.member* notation: it reaches a named member of a specific object, whether that member is data or a function (PPP §8.2). A class can mix any number of each; this note's `Account` has two of the first and three of the second.

## Under the Hood

> [!machine] A member call is an ordinary call with one address smuggled in
> `a.deposit(25.0)` and calling a free function with `a`'s address look like different notations for different things. The compiler disagrees. Compiled with GCC 11.4, `-O2`, x86-64, `via_member` (which calls `a.deposit(25.0)` through the member function) and `via_free` (which calls a free function taking `Account*` explicitly) emit **identical instructions**:
> ```nasm
> via_member(Account&):
>     movsd xmm0, QWORD PTR .LC0[rip]   ; load the literal 25.0
>     addsd xmm0, QWORD PTR [rdi+8]     ; add balance_ (offset 8 in *this)
>     movsd QWORD PTR [rdi+8], xmm0     ; store it back
>     ret
> via_free(Account&):
>     movsd xmm0, QWORD PTR .LC0[rip]
>     addsd xmm0, QWORD PTR [rdi+8]
>     movsd QWORD PTR [rdi+8], xmm0
>     ret
> ```
> `deposit` was small enough to inline either way, so both functions collapse to the same three instructions operating on the address the caller passed in `rdi`. The `.` notation cost nothing beyond what writing the free function by hand would have — it only changed who supplies that first address automatically. [[The this Pointer and Member Function Calls]] names that hidden argument and works out its type; this is only the proof that it is, in fact, an ordinary argument.

The representation leg is equally literal. `Account` lays its two members out in declaration order with no compiler invention:

```text
 Account a{1001, 250.0};                sizeof(Account) == 16
┌──────────────────────────┐
│ number_   long,  8 bytes │  offset 0
├──────────────────────────┤
│ balance_  double,8 bytes │  offset 8
└──────────────────────────┘
 no padding needed: both members are already 8-byte aligned
```
That picture is the LP64 layout (Linux, macOS). On 64-bit Windows (LLP64) `long` is only 4 bytes, so the compiler inserts 4 bytes of padding after `number_` to keep `balance_` 8-byte aligned: the offsets are the same and `sizeof(Account)` is still 16, but a quarter of the object is now padding (see [[Fundamental Types]] for why `long`'s width varies).

## In Code

**1 · `Account` used exactly like a built-in type**

```cpp
#include <iostream>
#include <vector>

class Account {
public:
    Account(long number, double balance) : number_{number}, balance_{balance} {}
    void deposit(double amt) { balance_ += amt; }
    double balance() const { return balance_; }
private:
    long number_;
    double balance_;
};

int main() {
    Account a{1001, 250.0};               // ①
    a.deposit(75.0);                      // ②
    std::vector<Account> ledger;          // ③
    ledger.push_back(a);
    ledger.emplace_back(1002, 0.0);
    std::cout << ledger[0].balance() << ' ' << ledger[1].balance() << '\n';
    std::cout << sizeof(Account) << '\n'; // ④
}
// expect: 325 0
// expect: 16
```
1. `Account` is declared exactly the way an `int` would be: a named variable, brace-initialized.
2. `.deposit` reaches a declared operation — the operations leg of the triple, exercised.
3. `std::vector<Account>` needs no special permission from the language: any complete type is a legal element type.
4. `sizeof` reports the representation leg fixed by the two data members.

**2 · The `.` notation versus writing the object out by hand**

```cpp
#include <iostream>

struct Account {
    long number_;
    double balance_;
    void deposit(double amt) { balance_ += amt; }   // ①
};

void deposit_free(Account* a, double amt) { a->balance_ += amt; }  // ②

double via_member(Account& a) { a.deposit(25.0); return a.balance_; }
double via_free(Account& a)   { deposit_free(&a, 25.0); return a.balance_; }

int main() {
    Account a{1001, 100.0};
    Account b{1002, 100.0};
    std::cout << via_member(a) << ' ' << via_free(b) << '\n';  // ③
}
// expect: 125 125
```
1. A member function's body names `balance_` directly, with no object written out — there is an implicit one.
2. The free-function version needs that same object passed explicitly, by address.
3. Both reach the same result; *Under the Hood* shows the compiler treats them as the same computation.

**3 · An aggregate: a class with no operations at all**

```cpp
#include <iostream>

struct Point {         // ① no user-declared constructor, no private data
    double x, y;
};

int main() {
    Point p{1.0, 2.0}; // ② member-by-member, no function ever called
    std::cout << p.x + p.y << '\n';
}
// expect: 3
```
1. `Point` declares no operations whatsoever — not even a constructor — so nothing here supplies more than the aggregate default.
2. The braces place `1.0` into `x` and `2.0` into `y` positionally. Contrast with Example 1's `Account{1001, 250.0}`, where the identical-looking syntax instead called a constructor, because `Account` declared one.

**4 · The operations leg has no entry unless someone writes one**

```cpp
// cc: ill-formed
struct Account {
    long number_;
    double balance_;
};

int main() {
    Account a{1001, 250.0};
    Account b{1001, 250.0};
    if (a == b) { }   // error: no match for 'operator=='
}
```
`a` and `b` hold identical bits, and the hardware can certainly compare two 8-byte words — but `Account` never declared `operator==`, so the compiler rejects the comparison exactly as it would reject a call to an undeclared function. See [[Comparisons and the Spaceship Operator]] for how a class supplies this, sometimes for free with `= default`.

## Pitfalls

> [!trap] "It compiles" is not "it makes sense"
> `Account{-1, -999999.99}` compiles without complaint under everything this note has built: a negative account number and a wildly negative balance are just another `(long, double)` pair, and nothing here says such a pair is wrong. A class this note has finished with fixes *shape* — which members exist, which functions may run — not *sense* — which combinations of values a caller may actually construct. Confusing the two is the single most common misreading of what a class buys you before [[Encapsulation and Class Invariants]] is added on top.

> [!trap] `struct` and `class` are the same construct wearing different defaults
> Swapping `struct Account` for `class Account` above changes nothing about the triple: both introduce a class type, both give `Account` a representation and an operation set. The only difference — default member access — doesn't even show up in this note's examples, because `Account`'s members were labeled explicitly. See [[struct vs class]] for the one case where the default actually matters.

## Evolution

See [[Map — Evolution of C++]] for the language-wide timeline.

| Standard | Change | Why |
|---|---|---|
| C / C++98 | `struct` (data-only in C) is joined by an equivalent `class` keyword, differing only in default access; either way, the result is a full type — copyable, `sizeof`-able, usable in arrays, like any built-in one | C already grouped data with `struct`; C++ needed the same construct to also carry the operations leg, not a second, incompatible mechanism |
| C++11 | Brace-`{}` initialization and in-class default member initializers extend to both aggregates and classes with constructors | One initialization syntax for user-defined and built-in types alike, rather than one convention per kind of type |
| C++17 | An aggregate may have public base classes (P0017R1) | Removes an arbitrary restriction that made simple inheritance hierarchies stop qualifying as aggregates |
| C++20 | Designated initializers: `Point p{.x = 1.0, .y = 2.0}` names which member each value goes to | Aggregate initialization gains the readability built-in-type initialization never needed |

## Connections

- **Prerequisites:** [[What a Type Is]] — the values × operations × representation triple this note shows a class supplying.
- **Enables:** [[Encapsulation and Class Invariants]] (restricting *which* values are reachable, not just which shape) · [[Constructors]] · [[The this Pointer and Member Function Calls]] (names the hidden argument *Under the Hood* proved is real) · [[Static Members]] · [[Operator Overloading]] · [[Inheritance]] (a second class reuses and extends this one's interface instead of declaring its own from scratch).
- **Siblings:** [[struct vs class]] (the one mechanical difference between the two keywords) · [[Aggregates and Designated Initializers]] (the class that declares no operations at all).
- **Domain:** [[Map — Classes & Encapsulation]].
- **Practice:** *Continuum #17 Bank Account Simulator* — build `Account` past this note's version: it should refuse the invalid states Pitfalls calls out, which means adding the invariant this note deliberately leaves open.

## Check Yourself

> [!quiz]- What three things does defining a class actually fix, and which one does a bare class (no constructor, no privacy) leave completely open?
> Representation (from data members) and operations (from member and friend functions) are fixed by the class body. Which *values* are reachable — the third leg — is left open until something (typically a constructor plus encapsulation) restricts it.

> [!quiz]- Why does `a.frobnicate()` fail to compile on an `Account` with no such member, even though the compiler could trivially generate code to call *some* function named `frobnicate` elsewhere in the program?
> Because member-function calls are resolved against the class's own declared operation set, not against every function with a matching name anywhere in the program. `Account` never declared `frobnicate` as a member, so the operations leg of its type has no such entry, and the call is ill-formed — the same rule Example 4 shows for `operator==`.

> [!quiz]- `struct Point { double x, y; };` has no constructor at all. Predict what `Point p{1.0, 2.0};` does, and name the property of `Point` that makes it legal.
> It aggregate-initializes `p`, placing `1.0` into `x` and `2.0` into `y` in declaration order, with no function ever called. This works because `Point` is an aggregate: no user-declared constructor, no private or protected non-static data members, no virtual functions.

> [!quiz]- `Account{-1, -999999.99}` compiles under this note's definition of `Account`. Is that a bug in the class? Why or why not, given what this note has (and hasn't) built?
> Not yet a bug in scope: this note's `Account` only fixes representation and operations, not which values make sense. Nothing here has claimed to reject invalid states — that guarantee doesn't exist until a constructor and encapsulation are added, which is exactly the subject of [[Encapsulation and Class Invariants]].

## Sources

- Tour §5.1.1 "Classes" (p. 54): frames a class as a user-defined type whose job is to stand for some entity the program's design cares about. §5.2 "Concrete Types" (p. 54): a concrete class's representation is part of its definition, which is what lets objects of it behave like built-in ones.
- Tour §2.1 "Introduction" (p. 21): classes and enumerations, built from the fundamental types via C++'s abstraction mechanisms, are what the language calls user-defined types.
- Primer §2.6 "Defining Our Own Data Structures" (p. 72): introduces the class as the language's mechanism for defining a new data type, worked through a `Sales_data` aggregate before operators are introduced in a later chapter.
- PPP §8.1 "User-defined types" (ch. 8): the built-in-vs-user-defined distinction turns on who supplies the representation/operations answer, not on any difference in what a type fundamentally is; standard-library types like `string` count as user-defined for the same reason.
- PPP §8.2 "Classes and members" (ch. 8): the `object.member` access notation, and that a class's members may be data or functions in any mixture.
- cppreference, *Classes*: "A class is a user-defined type" and the enumeration of what may be a class member: https://en.cppreference.com/w/cpp/language/classes
- cppreference, *Aggregate initialization*: the exact conditions for a class to be an aggregate, and the C++17 base-class relaxation: https://en.cppreference.com/w/cpp/language/aggregate_initialization
- Draft standard `[class.pre]`: a class-specifier is a class definition, given in the same declaration grammar a built-in type-specifier occupies: https://eel.is/c++draft/class.pre
- WG21 P0017R1, *Extension to aggregate initialization*: https://wg21.link/p0017r1
