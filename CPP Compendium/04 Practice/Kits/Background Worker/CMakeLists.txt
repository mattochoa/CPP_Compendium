# Background Worker kit — header-only, C++14/17
cmake_minimum_required(VERSION 3.14)
project(cc_background_worker LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17 CACHE STRING "C++ standard (14 or 17)")
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(Threads REQUIRED)

add_library(cc_background INTERFACE)                  # use: target_link_libraries(app PRIVATE cc_background)
target_include_directories(cc_background INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_link_libraries(cc_background INTERFACE Threads::Threads)

add_executable(bg_example examples/example_main.cpp)
target_link_libraries(bg_example PRIVATE cc_background)

add_executable(bg_tests tests/tests.cpp)
target_link_libraries(bg_tests PRIVATE cc_background)

if(MSVC)
  target_compile_options(bg_example PRIVATE /W4 /EHsc)
  target_compile_options(bg_tests PRIVATE /W4 /EHsc)
else()
  target_compile_options(bg_example PRIVATE -Wall -Wextra -pedantic)
  target_compile_options(bg_tests PRIVATE -Wall -Wextra -pedantic)
endif()

enable_testing()
add_test(NAME bg_tests COMMAND bg_tests)
