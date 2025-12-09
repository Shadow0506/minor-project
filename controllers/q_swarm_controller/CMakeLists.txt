cmake_minimum_required(VERSION 3.10)

# Project name
project(q_swarm_controller)

# Use C++11
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find ARGoS manually (for systems without pkg-config files)
set(ARGOS_INCLUDE_DIRS /usr/include/argos3)
set(ARGOS_LIBRARY_DIRS /usr/lib/argos3)

# Add Lua include directory
set(LUA_INCLUDE_DIR /usr/include/lua5.3)

# Set include directories
include_directories(
  ${CMAKE_SOURCE_DIR}
  ${ARGOS_INCLUDE_DIRS}
  ${LUA_INCLUDE_DIR}
)

# Link directories
link_directories(
  ${ARGOS_LIBRARY_DIRS}
)

# Set compiler flags (removed ARGOS_CFLAGS_OTHER since we're not using pkg-config)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall")

# Source files
set(CONTROLLER_SOURCES
  q_swarm_controller.cpp
  q_swarm_controller.h
)

# Create shared library
add_library(q_swarm_controller SHARED ${CONTROLLER_SOURCES})

# Link ARGoS libraries
target_link_libraries(q_swarm_controller
  argos3core_simulator
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
