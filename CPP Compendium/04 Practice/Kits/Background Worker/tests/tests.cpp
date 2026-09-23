// tests.cpp — self-checks for the Background Worker kit. Exit code 0 = all passed.
// Build:  g++ -std=c++14 -Wall -Wextra -pthread -fsanitize=thread -I include tests/tests.cpp -o tests && ./tests
#include <cassert>
#include <chrono>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

#include "cc/background.hpp"

using namespace std::chrono_literals;
using Clock = std::chrono::steady_clock;

static int failures = 0;
#define CHECK(cond) do { if (!(cond)) { std::cerr << "FAIL line " << __LINE__ << ": " #cond "\n"; ++failures; } } while (0)

void stop_wakes_sleeper_immediately() {
    cc::StopSource src;
    auto t0 = Clock::now();
    bool completed = true;
    cc::JoiningThread t([&] { completed = src.token().sleep_for(10s); });
    std::this_thread::sleep_for(50ms);
    src.request_stop();
    t.join();
    CHECK(!completed);
    CHECK(Clock::now() - t0 < 2s);                   // did not sleep the full 10 s
    CHECK(!src.request_stop());                      // second request reports "already stopped"
}

void default_token_never_stops() {
    cc::StopToken tok;
    CHECK(!tok.stop_possible());
    CHECK(!tok.stop_requested());
    CHECK(tok.sleep_for(1ms));
}

void joining_thread_joins_on_scope_exit() {
    bool ran = false;
    { cc::JoiningThread t([&] { std::this_thread::sleep_for(20ms); ran = true; }); }
    CHECK(ran);                                      // destructor waited for the thread
}

void stoppable_thread_stops_and_joins_in_destructor() {
    std::atomic<int> loops{0};
    auto t0 = Clock::now();
    {
        cc::StoppableThread t([&](cc::StopToken st) {
            while (st.sleep_for(1h)) ++loops;        // would block for an hour without a stop
        });
        std::this_thread::sleep_for(20ms);
    }
    CHECK(loops == 0);
    CHECK(Clock::now() - t0 < 2s);
}

void stoppable_thread_move_assignment_stops_old_thread() {
    std::atomic<bool> first_done{false};
    cc::StoppableThread t([&](cc::StopToken st) { while (st.sleep_for(1h)) {} first_done = true; });
    t = cc::StoppableThread([](cc::StopToken st) { while (st.sleep_for(1h)) {} });
    CHECK(first_done);                               // old thread was stopped + joined before replacement
}

void periodic_worker_ticks_and_stops() {
    std::atomic<int> calls{0};
    cc::PeriodicWorker w(10ms, [&] { ++calls; });
    std::this_thread::sleep_for(120ms);
    w.stop();
    std::this_thread::sleep_for(30ms);
    CHECK(!w.running());
    CHECK(w.ticks() >= 5);
    CHECK(static_cast<int>(w.ticks()) == calls.load());
    CHECK(!w.failed());
}

void periodic_worker_captures_exceptions() {
    cc::PeriodicWorker w(1ms, [] { throw std::runtime_error("sensor offline"); });
    std::this_thread::sleep_for(50ms);
    CHECK(w.failed());
    CHECK(!w.running());
    bool rethrown = false;
    try { w.rethrow_if_failed(); } catch (const std::runtime_error& e) { rethrown = std::string(e.what()) == "sensor offline"; }
    CHECK(rethrown);
}

void synchronized_is_race_free() {
    cc::Synchronized<long> counter(0);
    {
        std::vector<cc::JoiningThread> pool;
        for (int i = 0; i < 4; ++i)
            pool.emplace_back([&] { for (int k = 0; k < 10000; ++k) counter.with([](long& c) { ++c; }); });
    }                                                // all four joined here
    CHECK(counter.snapshot() == 40000);
    CHECK(counter.with([](const long& c) { return c * 2; }) == 80000);
}

int main() {
    stop_wakes_sleeper_immediately();
    default_token_never_stops();
    joining_thread_joins_on_scope_exit();
    stoppable_thread_stops_and_joins_in_destructor();
    stoppable_thread_move_assignment_stops_old_thread();
    periodic_worker_ticks_and_stops();
    periodic_worker_captures_exceptions();
    synchronized_is_race_free();
    std::cout << (failures ? "FAILED: " : "all tests passed") << (failures ? std::to_string(failures) : "") << '\n';
    return failures ? 1 : 0;
}
