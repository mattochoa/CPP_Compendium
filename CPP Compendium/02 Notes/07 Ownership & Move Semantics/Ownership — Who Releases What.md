---
id: ownership-model
title: Ownership — Who Releases What
type: concept
domain: D07
tier: 1
status: draft
standard: C++98
prereqs:
- "[[RAII]]"
related:
- "[[Copy Semantics — Deep vs Shallow Copy]]"
- "[[unique_ptr]]"
- "[[shared_ptr and Reference Counting]]"
- "[[Owning vs Observing Pointers]]"
practice:
- 25
- 26
tags:
- type/concept
- domain/d07
- tier/1
- tension/value-vs-identity
- std/c++11
created: 2026-09-26
updated: 2026-09-26
---

# Ownership — Who Releases What

> [!essence]
> An object's **owner** is whichever piece of code is responsible for releasing its resource, exactly once, when it is no longer needed. C++ tracks nothing about this by default — a raw pointer carries no bit marking it "must be deleted" — so ownership starts as a convention the design must state, and becomes a property the compiler enforces only once it is built into a type such as [[unique_ptr]].

## The Problem

> [!principle] Constraint → Consequence → Requirement → Design → Price
> 1. **Constraint.** [[RAII]] ties a resource's release to a destructor call, but a destructor only runs because *some* object's lifetime ends. Many different variables, parameters, and members can all hold a pointer, a reference, or a copy of a handle to the very same resource at the same time.
> 2. **Consequence.** If every one of those holders independently decides "releasing this is my job," the resource is released once per believer. The second `delete` of an already-deleted pointer is not a no-op — the operand no longer "resulted from a previous new-expression" in the sense the delete-expression requires, so the second call is undefined behavior (`[expr.delete]` ¶2), typically corrupting the allocator's own bookkeeping. If nobody believes it is their job, the resource is never released: a leak. Both failures have the same root cause — nobody agreed on the headcount.
> 3. **Requirement.** Every piece of code that touches a resource must be answerable to one question: exactly how many parties, and which ones, are responsible for releasing it? Everyone else may look at the resource, or use it, but must never call the release operation.
> 4. **Design.** C++ recognizes exactly two headcounts that work, and treats every other arrangement as a bug waiting to happen. **Exclusive ownership**: precisely one party is ever responsible, and handing the resource to someone else *transfers* that responsibility rather than duplicating it — [[unique_ptr]] enforces this by deleting its own copy constructor, so the only legal handoff is a move. **Shared ownership**: an agreed-upon, dynamically tracked set of parties are jointly responsible, and the resource is released only once that count returns to zero ([[shared_ptr and Reference Counting]]). Anything that is neither of these — a raw pointer, a reference, an iterator — is by convention an **observer**: never responsible, and never entitled to release what it refers to (C++ Core Guidelines I.11).
> 5. **Price.** A raw pointer's type gives no hint which of these three roles it plays in a given program; you learn it only from documentation, a naming convention, or a static-analysis annotation. Only once ownership is written into a type's own interface — as `unique_ptr` and `shared_ptr` do — does "who releases this" stop being a question you answer by reading the rest of the program.

> [!tension] value ⟷ identity
> Primer's own `vector` is the uncomplicated case: each `vector` "owns" its elements, so copying a `vector` copies its contents, and the two are afterward strangers to each other's storage — a `vector` behaves purely as a **value**. Ownership becomes a live design question only once an object's copy is *meant* to stay entangled with the same underlying resource — the way two `shared_ptr`s to one open file are meant to refer to one **identity**. Deciding whether a copy of your type should be an independent value or a second reference to the same identity is exactly the decision this domain forces on every resource-holding class.

## Mental Model

```text
  STACK (automatic)                              HEAP (dynamic)
 ┌─────────────────────────────┐                ┌────────────────────┐
 │ open_log()                  │                │ Logger  0x5a3c…10  │
 │  owner : unique_ptr<Logger> │──●─────────────▶│ [ fd = 7 ]         │
 │  view  : Logger*            │──●─────────────▶│                    │
 └─────────────────────────────┘                └────────────────────┘
```
Both `owner` and `view` are ordinary pointers holding the identical address — nothing in their bits distinguishes them. `owner`'s destructor is the one that will call `delete`; `view` merely observes and must never call it, and must not be dereferenced once `owner` has released the object.

> [!model] A key you're given to keep, and a key you borrow
> **Owning** a resource is like being handed the one key you are expected, eventually, to turn back in: when you do (or when you are destroyed), the lock changes, and that key stops working for anyone. **Observing** is like being lent a copy of the key for the afternoon: you can open the door, but handing your copy back does nothing to the lock — and if the owner has already turned theirs in, your copy now opens a door that no longer exists.
> **Where it breaks:** a physical key is a distinct object you can point to; an owning pointer and an observing pointer are the *same bits* — an address and nothing more. Nothing about the type `Logger*` announces which role a given `Logger*` plays. That gap is exactly what [[unique_ptr]] and [[shared_ptr and Reference Counting]] close by folding the role into the type itself, and exactly the gap a bare pointer leaves open, which is why it takes a documented convention — not the compiler — to say that a raw pointer parameter is presumed non-owning.

## Mechanics

| Situation | Rule | Example |
|---|---|---|
| Raw pointer or reference parameter | Non-owning by convention, not by compiler check: the caller keeps responsibility for release (Core Guidelines I.11) | `void render(const Widget&)` |
| Object held by value as a member | The containing object owns it implicitly; the member's destructor runs when the container's does | a `vector`'s elements live and die with the `vector` |
| `unique_ptr<T>` | Exactly one owner, enforced by a deleted copy constructor — the only legal handoff is a move | `unique_ptr<T> b = std::move(a);` |
| `shared_ptr<T>` | Ownership shared among however many copies currently exist; released only when the last is destroyed | `auto b = a; // now two owners` |
| `weak_ptr<T>` | Observes an object owned by some `shared_ptr`, without counting toward ownership | see [[weak_ptr and Reference Cycles]] |
| Returning an object by value | The caller becomes its sole owner; nothing owned it in between | `Widget make();` |

> [!standard] The Standard doesn't define "ownership"
> *Owner*, *observer*, and *resource* are design vocabulary, not Standard terms. What the Standard actually guarantees is narrower: an object's destructor runs at most once, at the end of its lifetime (`[basic.life]`), and a `delete`-expression whose operand isn't (still) a pointer from a matching, not-yet-deleted `new`-expression is undefined behavior (`[expr.delete]` ¶2). Everything about *which* code is entitled to trigger that one destructor call — the entire idea of ownership — is a convention your design layers on top, or, for `unique_ptr`/`shared_ptr`, a guarantee encoded directly into a type's copy and destructor semantics.

## Under the Hood

> [!machine] Making ownership explicit costs nothing on the path that succeeds
> A hand-written owning raw pointer and a `unique_ptr` doing the identical job compile to the same instructions on the path where nothing throws (GCC 11.4, `-O2`, x86-64; `sink` is an external opaque function so the allocation can't be optimized away):
> ```nasm
> use_raw(int):                       use_unique(int):
>   call operator new(unsigned long)    call operator new(unsigned long)
>   mov  DWORD PTR [rax], ebp            mov  DWORD PTR [rax], ebp
>   call sink(Widget*)                   call sink(Widget*)
>   call operator delete(void*, ...)     call operator delete(void*, ...)
> ```
> The two hot paths are the same call sequence, register for register. `use_unique` additionally emits a landing pad in a cold, out-of-line section that also calls `operator delete` — inserted so that if `sink` throws, the `unique_ptr`'s destructor still runs during unwinding. `use_raw`'s hand-written version has no such path: if `sink` throws, its `delete owner;` is skipped and the object leaks. Writing ownership into the type didn't just document who releases the resource — it bought correctness on the exception path the raw-pointer version silently lacks, for zero extra cost on the path that doesn't throw.

## In Code

**1 · Exclusive ownership can be transferred, never duplicated**

```cpp
// cc: ill-formed
#include <memory>

struct Sensor { int id; };

int main() {
    std::unique_ptr<Sensor> a = std::make_unique<Sensor>(1);
    std::unique_ptr<Sensor> b = a;   // ①
}
```
1. `unique_ptr`'s copy constructor is deleted, so this fails to compile. "Exactly one owner" is enforced before the program ever runs.

```cpp
#include <memory>
#include <iostream>

struct Sensor { int id; };

int main() {
    std::unique_ptr<Sensor> a = std::make_unique<Sensor>(1);
    std::unique_ptr<Sensor> b = std::move(a);   // ①
    std::cout << (a == nullptr) << ' ' << b->id << '\n';
}
// expect: 1 1
```
1. `std::move` doesn't copy; it lets `b`'s move constructor steal `a`'s pointer and leave `a` null. There was only ever one `Sensor`, and only ever one owner of it — the identity of *which* variable holds that role simply changed.

**2 · Observing a resource is not the same as being responsible for it**

```cpp
#include <memory>
#include <iostream>

struct Account { double balance; };

void print_balance(const Account& a) {     // ① observer: no say in a's fate
    std::cout << a.balance << '\n';
}

void close_account(std::unique_ptr<Account> a) {  // ② owner: decides a's fate
    std::cout << "closing, final balance " << a->balance << '\n';
}   // a's destructor runs here; the Account is gone after this line

int main() {
    auto acc = std::make_unique<Account>(Account{250.0});
    print_balance(*acc);              // ③ acc is still the owner
    close_account(std::move(acc));    // ④ ownership transferred
    std::cout << (acc == nullptr) << '\n';
}
// expect: 250
// expect: closing, final balance 250
// expect: 1
```
1. Taking a `const Account&` grants read access and nothing else; the function has no way to release what it was given.
2. Taking a `unique_ptr<Account>` by value is the type-level way of saying "I am now responsible for this."
3. `acc` is untouched by the call: an observer can't take ownership just by being handed a reference.
4. `std::move(acc)` transfers ownership into the parameter; `acc` becomes an empty (null) `unique_ptr`, confirmed by the final line.

**3 · Shared ownership: released only when the last owner goes**

```cpp
#include <memory>
#include <iostream>

struct Cache { int hits = 0; };

int main() {
    std::shared_ptr<Cache> a = std::make_shared<Cache>();
    std::cout << a.use_count() << '\n';       // ①
    {
        std::shared_ptr<Cache> b = a;         // ②
        std::cout << a.use_count() << '\n';
        b->hits = 7;
    }                                          // ③
    std::cout << a.use_count() << ' ' << a->hits << '\n';
}
// expect: 1
// expect: 2
// expect: 1 7
```
1. One owner so far: `a`.
2. Copying a `shared_ptr` adds an owner, not a second `Cache` — `a` and `b` refer to the same object, and the count rises to two.
3. `b` is destroyed at the closing brace, dropping the count back to one. Because `a` still owns the `Cache`, it is *not* released, and `a->hits` still reads the `7` that `b` wrote.

**4 · An observer that outlives its owner**

```cpp
// cc: ub
#include <memory>

struct Widget { int v; };

int main() {
    Widget* view;                               // ①
    {
        auto owner = std::make_unique<Widget>(9);
        view = owner.get();                     // ② view only watches
    }                                            // ③ owner destroyed here
    return view->v;                              // ④ UB: dangling observer
}
```
1. `view` is declared before it has anything to observe.
2. `view` copies the address `owner` manages; `view` gains no ownership.
3. `owner` goes out of scope, its destructor deletes the `Widget`, and `view` is left dangling — nothing about `view`'s bits changes to reflect this.
4. Dereferencing `view` reads through a pointer to an object whose lifetime has ended: undefined behavior. Neither `-Wall` nor `-Wextra` catches this at compile time.

## Pitfalls

> [!trap] A pointer's type never tells you which role it plays
> `void configure(Widget* w)` gives no clue, from the signature alone, whether `configure` takes ownership or merely observes. Core Guidelines I.11 makes the default convention explicit — raw pointers and references are presumed non-owning — precisely because the language itself enforces nothing here. When a function really must take ownership through a raw pointer (legacy APIs, ABI boundaries), say so in the type with `gsl::owner<T*>` or, better, change the signature to `unique_ptr<T>`.

> [!ub] An observer that outlives its owner
> Example 4 above shows the shape: a non-owning pointer copies an address, its owner is destroyed, and the pointer is now dangling with no change to its own bits to reveal this. See [[Dangling Pointers and References]] for the general hazard, its detection tools (ASan, `-fsanitize=address`), and how to avoid it structurally.

## Evolution

| Standard | Change | Why |
|---|---|---|
| C++98 | Manual `new`/`delete` only; `std::auto_ptr` attempts exclusive ownership by transferring on *copy* | An early, unsafe attempt: `auto_ptr`'s copy constructor and copy assignment both silently mutate their right-hand argument, so a "copy" is never equal to the original, and `auto_ptr` cannot be stored in standard containers |
| **C++11** | `unique_ptr` and `shared_ptr`/`weak_ptr` give exclusive and shared ownership their own move-aware types; `auto_ptr` deprecated | [[Rvalue References|Rvalue references]] finally let a "transfer, don't duplicate" pointer distinguish a move from a copy at the language level, something `auto_ptr` could only fake by copy |
| C++17 | `auto_ptr` removed from the standard | Its copy-that-secretly-moves semantics were retroactively recognized as a design mistake, fully superseded by `unique_ptr` |

## Connections

- **Prerequisites:** [[RAII]] — establishes that release happens at scope exit; this note names *whose* scope.
- **Enables:** [[Copy Semantics — Deep vs Shallow Copy]] (what a copy must do once ownership is exclusive) · [[unique_ptr]] · [[shared_ptr and Reference Counting]] · [[Owning vs Observing Pointers]].
- **Siblings:** [[Move Semantics]] (the mechanism that lets ownership transfer without a deep copy).
- **Domain:** [[Map — Ownership & Move Semantics]].
- **Practice:** *Continuum #25 Smart Pointer Refactor Lab* — replace every raw `new`/`delete` and decide, resource by resource, exclusive or shared. *#26 Custom Exception Hierarchy & Robust CSV Parser* — verify ownership survives an exception thrown mid-function.

## Check Yourself

> [!quiz]- What two things must be true of any valid ownership design for a resource?
> Exactly one *headcount policy* must be chosen — either precisely one owner at a time (exclusive) or a jointly-tracked set of owners (shared) — and everyone else touching the resource must be a non-owning observer that never calls the release operation.

> [!quiz]- Why does a `const Widget&` parameter never take ownership of the `Widget` it's given, no matter what the function does with it?
> A reference cannot outlive the call in a way that matters for ownership: it has no destructor of its own to run later, and nothing about receiving a reference gives the callee a say in when the referent is destroyed. Only a type whose own lifetime is tied to the resource — `unique_ptr<Widget>`, `Widget` by value — can hold ownership.

> [!quiz]- Predict: what happens if `close_account` in example 2's code is called with `close_account(*acc)` — i.e., a raw `Account&` is somehow bound to a parameter of type `unique_ptr<Account>`?
> It doesn't compile: there is no implicit conversion from `Account&` to `unique_ptr<Account>` (that would silently manufacture an owner for an object nothing allocated for that purpose). Transferring ownership through a `unique_ptr` parameter requires an actual `unique_ptr` argument, moved in explicitly — the type system refuses to guess who is responsible.

## Sources

- Primer §12.1 "Dynamic Memory and Smart Pointers" (p. 450): the leak-vs-premature-free framing that motivates smart pointers. §12.1 (pp. 454–455), "Classes with Resources That Have Dynamic Lifetime": the vector-vs-`Blob` contrast between a type whose copies are independent values and a type whose copies are meant to share one identity.
- Tour §15.2.1 "unique_ptr and shared_ptr" (p. 197): defines a resource as "something that must be acquired and later released," then states the split directly — "`unique_ptr` represents unique ownership… `shared_ptr` represents shared ownership."
- PPP §18.5 "Resource-management pointers": motivates `unique_ptr`/`shared_ptr` from a hand-written resource-owning class, pedagogically building up the same headcount problem.
- Pikus, "Interface design" (p. 417): ownership as a decision to make explicit at a component's interface, not an incidental detail of pointer choice. "Smart pointers for concurrent programming" (p. 233): the measured run-time cost of shared ownership's reference count versus a non-owning raw pointer.
- cppreference, *std::unique_ptr*: "owns (is responsible for) and manages another object" — the definitional phrase this note's title is built on: https://en.cppreference.com/w/cpp/memory/unique_ptr
- cppreference, *std::auto_ptr*: confirms deprecation in C++11 and removal in C++17, and states the copy-mutates-the-source semantics directly: https://en.cppreference.com/w/cpp/memory/auto_ptr
- C++ Core Guidelines I.11, "Never transfer ownership by a raw pointer (`T*`) or reference (`T&`)": states the non-owning-by-default convention for raw pointers and introduces `gsl::owner<T*>` for the rare case a raw pointer must own: https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#ri-raw
- Draft standard `[expr.delete]` ¶2 (double-delete is UB) and `[basic.life]` (a destructor ends an object's lifetime): https://eel.is/c++draft/expr.delete · https://eel.is/c++draft/basic.life
