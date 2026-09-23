// cc/stop_token.hpp — cooperative cancellation for C++14/17
// A small stand-in for C++20's std::stop_source / std::stop_token.
//
//   StopSource src;                 // owner: can request a stop
//   StopToken  tok = src.token();   // observers: can ask "should I stop?"
//   tok.sleep_for(500ms);           // sleeps, but wakes IMMEDIATELY on request_stop()
//
// Thread-safe: any thread may call request_stop() / stop_requested() / sleep_for().
// Compendium: [[Cooperative Cancellation with stop_token]], [[Condition Variables]], [[Atomics]]
#pragma once

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <memory>
#include <mutex>
#include <thread>
#include <utility>

namespace cc {

namespace detail {
// Shared by one StopSource and all of its StopTokens (lifetime = longest holder).
struct StopState {
    std::atomic<bool> stopped{false};
    std::mutex mutex;                 // only protects the condition-variable handshake
    std::condition_variable wake;     // lets sleepers wake early when a stop is requested
};
}  // namespace detail

class StopToken {
public:
    StopToken() = default;            // a default token never reports a stop

    bool stop_requested() const noexcept {
        return state_ && state_->stopped.load(std::memory_order_acquire);
    }
    bool stop_possible() const noexcept { return static_cast<bool>(state_); }

    // Sleep for up to `d`. Returns true if the whole duration elapsed,
    // false if a stop was requested (in which case it returns right away).
    template <class Rep, class Period>
    bool sleep_for(const std::chrono::duration<Rep, Period>& d) const {
        if (!state_) {
            std::this_thread::sleep_for(d);
            return true;
        }
        std::unique_lock<std::mutex> lock(state_->mutex);
        const bool stopped = state_->wake.wait_for(lock, d, [this] {
            return state_->stopped.load(std::memory_order_acquire);
        });
        return !stopped;
    }

private:
    friend class StopSource;
    explicit StopToken(std::shared_ptr<detail::StopState> s) noexcept : state_(std::move(s)) {}
    std::shared_ptr<detail::StopState> state_;
};

class StopSource {
public:
    StopSource() : state_(std::make_shared<detail::StopState>()) {}

    StopToken token() const noexcept { return StopToken(state_); }

    // Returns true only for the call that actually made the request.
    bool request_stop() noexcept {
        if (!state_) return false;                        // moved-from source
        bool expected = false;
        if (!state_->stopped.compare_exchange_strong(expected, true, std::memory_order_acq_rel))
            return false;
        { std::lock_guard<std::mutex> handshake(state_->mutex); }   // no lost wake-ups
        state_->wake.notify_all();
        return true;
    }

    bool stop_requested() const noexcept {
        return state_ && state_->stopped.load(std::memory_order_acquire);
    }

private:
    std::shared_ptr<detail::StopState> state_;
};

}  // namespace cc
