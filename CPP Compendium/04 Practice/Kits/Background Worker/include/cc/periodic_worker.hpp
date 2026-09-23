// cc/periodic_worker.hpp — run a task every N milliseconds on a background thread (C++14/17)
//
//   cc::PeriodicWorker heartbeat(std::chrono::seconds(1), [] { ping_server(); });
//   ... main thread keeps working ...
//   heartbeat.stop();                 // or just let it go out of scope
//   heartbeat.rethrow_if_failed();    // surface an exception thrown by the task
//
// - Fixed-rate schedule (no drift); if a tick overruns, the next one starts immediately
//   (no burst of catch-up ticks).
// - stop() wakes the worker at once, even in the middle of a long interval.
// - An exception thrown by the task stops the worker and is kept for the owner,
//   instead of calling std::terminate.
// Compendium: [[Threads — thread and jthread]], [[Exceptions]], [[chrono — Durations, Clocks, Time Points]]
#pragma once

#include <atomic>
#include <chrono>
#include <cstdint>
#include <exception>
#include <functional>
#include <mutex>
#include <utility>

#include "joining_thread.hpp"
#include "stop_token.hpp"

namespace cc {

class PeriodicWorker {
public:
    using Clock = std::chrono::steady_clock;          // monotonic: immune to wall-clock changes

    template <class Rep, class Period>
    PeriodicWorker(std::chrono::duration<Rep, Period> interval, std::function<void()> task)
        : interval_(std::chrono::duration_cast<Clock::duration>(interval)),
          task_(std::move(task)),
          thread_([this](StopToken st) { run(st); }) {}   // last member: everything above exists

    PeriodicWorker(const PeriodicWorker&) = delete;       // the thread holds `this`:
    PeriodicWorker& operator=(const PeriodicWorker&) = delete;   // copying or moving would dangle
    PeriodicWorker(PeriodicWorker&&) = delete;
    PeriodicWorker& operator=(PeriodicWorker&&) = delete;

    ~PeriodicWorker() = default;                          // thread_ requests stop + joins first

    void stop() noexcept { thread_.request_stop(); }
    bool running() const noexcept { return !finished_.load(std::memory_order_acquire); }
    std::uint64_t ticks() const noexcept { return ticks_.load(std::memory_order_relaxed); }
    bool failed() const noexcept { return failed_.load(std::memory_order_acquire); }

    void rethrow_if_failed() const {
        std::exception_ptr e;
        {
            std::lock_guard<std::mutex> lock(error_mutex_);
            e = error_;
        }
        if (e) std::rethrow_exception(e);
    }

private:
    void run(StopToken st) {
        struct MarkFinished {
            std::atomic<bool>& flag;
            ~MarkFinished() { flag.store(true, std::memory_order_release); }
        } mark{finished_};

        auto next = Clock::now();
        while (!st.stop_requested()) {
            try {
                task_();
                ticks_.fetch_add(1, std::memory_order_relaxed);
            } catch (...) {
                {
                    std::lock_guard<std::mutex> lock(error_mutex_);
                    error_ = std::current_exception();
                }
                failed_.store(true, std::memory_order_release);
                return;
            }
            next += interval_;
            const auto now = Clock::now();
            if (next < now) next = now;                   // overran: don't burst to catch up
            if (!st.sleep_for(next - now)) return;         // stop requested while sleeping
        }
    }

    const Clock::duration interval_;
    std::function<void()> task_;
    std::atomic<std::uint64_t> ticks_{0};
    std::atomic<bool> finished_{false};
    std::atomic<bool> failed_{false};
    mutable std::mutex error_mutex_;
    std::exception_ptr error_;
    StoppableThread thread_;                              // MUST stay the last member
};

}  // namespace cc
