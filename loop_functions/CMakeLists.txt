cmake_minimum_required(VERSION 3.5)
project(q_swarm_loop_functions)

# Set C++ standard
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find ARGoS
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} /usr/share/argos3/cmake)
find_package(ARGoS REQUIRED)

# Include directories
include_directories(${ARGOS_INCLUDE_DIRS})
link_directories(${ARGOS_LIBRARY_DIRS})

# Print ARGoS information
message(STATUS "Loop Functions: q_swarm_loop_functions")
message(STATUS "ARGoS include dirs: ${ARGOS_INCLUDE_DIRS}")

# Build the loop functions library
add_library(q_swarm_loop_functions SHARED
    q_swarm_loop_functions.h
    q_swarm_loop_functions.cpp
)

# Link ARGoS libraries
target_link_libraries(q_swarm_loop_functions 
    /usr/lib/argos3/libargos3core_simulator.so
    /usr/lib/argos3/libargos3plugin_simulator_footbot.so
    /usr/lib/argos3/libargos3plugin_simulator_entities.so
)

# Installation (optional)
install(TARGETS q_swarm_loop_functions
    LIBRARY DESTINATION lib/argos3
)
