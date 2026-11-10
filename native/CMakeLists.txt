cmake_minimum_required(VERSION 3.16)
project(csvbench CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

set(CMAKE_CXX_FLAGS_RELEASE "-O2 -DNDEBUG")

find_package(Qt6 REQUIRED COMPONENTS Widgets)

add_executable(csvbench
    src/main.cpp
    src/proctime.cpp
    src/csvloader.cpp
    src/tablemodel.cpp
    src/mainwindow.cpp
)

target_link_libraries(csvbench PRIVATE Qt6::Widgets)

set_target_properties(csvbench PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}
)
