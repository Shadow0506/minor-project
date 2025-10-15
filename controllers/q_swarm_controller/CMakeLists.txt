cmake_minimum_required(VERSION 3.10)

# Project name
project(q_swarm_controller)

# Use C++11
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find ARGoS package
find_package(PkgConfig)
pkg_check_modules(ARGOS REQUIRED argos3_simulator)

# Set include directories
include_directories(
  ${CMAKE_SOURCE_DIR}
  ${ARGOS_INCLUDE_DIRS}
)

# Link directories
link_directories(
  ${ARGOS_LIBRARY_DIRS}
)

# Set compiler flags
add_definitions(${ARGOS_CFLAGS_OTHER})
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${ARGOS_CFLAGS_OTHER}")

# Source files
set(CONTROLLER_SOURCES
  q_swarm_controller.cpp
  q_swarm_controller.h
)

# Create shared library
add_library(q_swarm_controller SHARED ${CONTROLLER_SOURCES})

# Link ARGoS libraries
target_link_libraries(q_swarm_controller
  ${ARGOS_LIBRARIES}
  argos3plugin_simulator_footbot
  argos3plugin_simulator_genericrobot
)

# Windows-specific socket library
if(WIN32)
  target_link_libraries(q_swarm_controller ws2_32)
endif()

# Installation (optional)
install(TARGETS q_swarm_controller
  LIBRARY DESTINATION lib/argos3
  RUNTIME DESTINATION bin
)

# Print information
message(STATUS "Controller: q_swarm_controller")
message(STATUS "ARGoS libraries: ${ARGOS_LIBRARIES}")
message(STATUS "ARGoS include dirs: ${ARGOS_INCLUDE_DIRS}")
