// cc/synchronized.hpp — a value that can only be touched under its own mutex (C++14/17)
//
//   cc::Synchronized<std::vector<int>> log;
//   log.with([](auto& v) { v.push_back(42); });        // locked for exactly this lambda
//   auto copy = log.snapshot();                          // locked copy-out
//
// The lock is impossible to forget because the data is unreachable without it.
// Rule: never let a reference/pointer to the protected value escape the lambda.
// Compendium: [[Mutexes and Lock Guards]], [[Data Races and Race Conditions]], [[Deadlock]]
#pragma once

#include <mutex>
#include <utility>

namespace cc {

template <class T>
class Synchronized {
public:
    Synchronized() = default;
    explicit Synchronized(T value) : value_(std::move(value)) {}

    Synchronized(const Synchronized&) = delete;
    Synchronized& operator=(const Synchronized&) = delete;

    // Run f(T&) while holding the lock; returns whatever f returns (by value!).
    template <class F>
    auto with(F&& f) -> decltype(std::forward<F>(f)(std::declval<T&>())) {
        std::lock_guard<std::mutex> lock(mutex_);
        return std::forward<F>(f)(value_);
    }
    template <class F>
    auto with(F&& f) const -> decltype(std::forward<F>(f)(std::declval<const T&>())) {
        std::lock_guard<std::mutex> lock(mutex_);
        return std::forward<F>(f)(value_);
    }

    T snapshot() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return value_;
    }
    void set(T value) {
        std::lock_guard<std::mutex> lock(mutex_);
        value_ = std::move(value);
    }

private:
    mutable std::mutex mutex_;
    T value_{};
};

}  // namespace cc
