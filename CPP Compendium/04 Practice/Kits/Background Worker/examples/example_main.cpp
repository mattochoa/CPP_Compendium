// example_main.cpp — the main thread keeps working while background workers run.
// Build:  g++ -std=c++17 -Wall -Wextra -pthread -I include examples/example_main.cpp -o example
//   (or -std=c++14; MSVC: cl /std:c++17 /EHsc /I include examples\example_main.cpp)
#include <chrono>
#include <iostream>
#include <string>
#include <vector>

#include "cc/background.hpp"

int main() {
    using namespace std::chrono_literals;

    cc::Synchronized<std::vector<std::string>> events;       // shared by all threads

    // 1) A periodic background job: runs every 300 ms until stopped.
    cc::PeriodicWorker heartbeat(300ms, [&events] {
        events.with([](std::vector<std::string>& v) { v.push_back("heartbeat"); });
    });

    // 2) A long-running background loop that exits promptly when asked.
    cc::StoppableThread watcher([&events](cc::StopToken st) {
        int polls = 0;
        while (st.sleep_for(200ms))                            // false as soon as a stop is requested
            ++polls;
        events.with([polls](std::vector<std::string>& v) {
            v.push_back("watcher stopped after " + std::to_string(polls) + " polls");
        });
    });

    // 3) Meanwhile, the main thread does its own tasks.
    for (int task = 1; task <= 3; ++task) {
        std::cout << "main: task " << task << '\n';
        std::this_thread::sleep_for(400ms);
    }

    // 4) Shut down in a defined order (destructors would do the same automatically).
    heartbeat.stop();
    watcher.request_stop();
    watcher.join();

    std::cout << "heartbeat ticks: " << heartbeat.ticks() << '\n';
    for (const auto& e : events.snapshot()) std::cout << "  event: " << e << '\n';
    heartbeat.rethrow_if_failed();                             // no-op unless the task threw
}
