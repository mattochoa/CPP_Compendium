// cc/joining_thread.hpp — threads that clean up after themselves (C++14/17)
//
// JoiningThread   : std::thread that JOINS in its destructor (never std::terminate on scope exit)
// StoppableThread : JoiningThread + StopSource; the callable receives a StopToken,
//                   and the destructor requests a stop, then joins. (C++20 std::jthread, in miniature.)
//
//   cc::StoppableThread worker([](cc::StopToken st) {
//       while (!st.stop_requested()) { do_work(); st.sleep_for(100ms); }
//   });                                   // leaving scope: request_stop() + join()
//
// Compendium: [[RAII]], [[Threads — thread and jthread]], [[Cooperative Cancellation with stop_token]]
#pragma once

#include <thread>
#include <type_traits>
#include <utility>

#include "stop_token.hpp"

namespace cc {

class JoiningThread {
public:
    JoiningThread() noexcept = default;

    template <class F, class... Args,
              class = std::enable_if_t<!std::is_same<std::decay_t<F>, JoiningThread>::value>>
    explicit JoiningThread(F&& f, Args&&... args)
        : thread_(std::forward<F>(f), std::forward<Args>(args)...) {}

    JoiningThread(JoiningThread&&) noexcept = default;
    JoiningThread& operator=(JoiningThread&& other) noexcept {
        if (this != &other) {
            join_if_joinable();                 // finish the thread we own before taking another
            thread_ = std::move(other.thread_);
        }
        return *this;
    }
    JoiningThread(const JoiningThread&) = delete;
    JoiningThread& operator=(const JoiningThread&) = delete;

    ~JoiningThread() { join_if_joinable(); }

    bool joinable() const noexcept { return thread_.joinable(); }
    void join() { thread_.join(); }
    std::thread::id get_id() const noexcept { return thread_.get_id(); }

private:
    void join_if_joinable() noexcept {
        if (thread_.joinable()) thread_.join();
    }
    std::thread thread_;
};

class StoppableThread {
public:
    StoppableThread() = default;

    // `f` must be callable as f(cc::StopToken).
    template <class F,
              class = std::enable_if_t<!std::is_same<std::decay_t<F>, StoppableThread>::value>>
    explicit StoppableThread(F&& f)
        : source_(),                                                  // declared first: exists before the thread starts
          thread_([fn = std::forward<F>(f), token = source_.token()]() mutable { fn(token); }) {}

    StoppableThread(StoppableThread&&) noexcept = default;
    StoppableThread& operator=(StoppableThread&& other) noexcept {
        if (this != &other) {
            stop_and_join();
            source_ = std::move(other.source_);
            thread_ = std::move(other.thread_);
        }
        return *this;
    }
    StoppableThread(const StoppableThread&) = delete;
    StoppableThread& operator=(const StoppableThread&) = delete;

    ~StoppableThread() { stop_and_join(); }

    bool request_stop() noexcept { return source_.request_stop(); }
    StopToken get_token() const noexcept { return source_.token(); }
    bool joinable() const noexcept { return thread_.joinable(); }
    void join() { thread_.join(); }

private:
    void stop_and_join() noexcept {
        if (thread_.joinable()) {
            source_.request_stop();
            thread_ = JoiningThread{};               // move-assign joins the running thread
        }
    }
    StopSource source_;       // order matters: constructed before, destroyed after, thread_
    JoiningThread thread_;
};

}  // namespace cc
