# winmiddle cursor — KWin effect that hides the real pointer while winmiddle pins it.
# Must be built against the exact KWin it runs in (no binary compatibility).
cmake_minimum_required(VERSION 3.20)
project(winmiddlecursor LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(Qt6 REQUIRED COMPONENTS Core Gui DBus Quick Widgets)
find_package(KWin QUIET)

add_library(winmiddlecursor MODULE main.cpp winmiddlecursor.cpp)
set_target_properties(winmiddlecursor PROPERTIES PREFIX "")

if(TARGET KWin::kwin)
    target_link_libraries(winmiddlecursor PRIVATE KWin::kwin Qt6::DBus)
else()
    # No extra-cmake-modules: wire up KWin's public headers by hand.
    message(STATUS "KWin CMake package unavailable (missing ECM?) — using manual include/link paths")
    find_package(KF6Config REQUIRED)
    find_package(KF6CoreAddons REQUIRED)
    find_package(KF6WindowSystem REQUIRED)
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(KWIN_DEPS REQUIRED IMPORTED_TARGET wayland-server epoxy libdrm)
    find_library(KWIN_LIBRARY NAMES kwin REQUIRED)
    find_path(KWIN_INCLUDE_DIR NAMES effect/effect.h PATH_SUFFIXES kwin REQUIRED)
    target_include_directories(winmiddlecursor PRIVATE ${KWIN_INCLUDE_DIR})
    target_compile_definitions(winmiddlecursor PRIVATE
        VULKAN_HPP_NO_EXCEPTIONS=1 VULKAN_HPP_ASSERT_ON_RESULT=void
        VULKAN_HPP_NO_SPACESHIP_OPERATOR=1 VULKAN_HPP_TYPESAFE_CONVERSION=1
        VULKAN_HPP_HANDLES_MOVE_EXCHANGE=1)
    target_link_libraries(winmiddlecursor PRIVATE
        ${KWIN_LIBRARY} Qt6::DBus Qt6::Quick Qt6::Widgets
        KF6::ConfigCore KF6::CoreAddons KF6::WindowSystem PkgConfig::KWIN_DEPS)
endif()

# KWin refuses effects whose metadata Version differs from its own
# (KWIN_PLUGIN_VERSION_STRING) — so a stale build is skipped, never loaded.
get_target_property(_kwinIncludes winmiddlecursor INCLUDE_DIRECTORIES)
if(TARGET KWin::kwin)
    get_target_property(_kwinIncludes KWin::kwin INTERFACE_INCLUDE_DIRECTORIES)
endif()
find_file(KWIN_CONFIG_HEADER config-kwin.h PATHS ${_kwinIncludes} PATH_SUFFIXES kwin REQUIRED)
file(STRINGS "${KWIN_CONFIG_HEADER}" _kwinVersionLine REGEX "KWIN_PLUGIN_VERSION_STRING")
string(REGEX MATCH "\"([^\"]+)\"" _ "${_kwinVersionLine}")
set(KWIN_PLUGIN_VERSION "${CMAKE_MATCH_1}")
message(STATUS "Building winmiddlecursor for KWin ${KWIN_PLUGIN_VERSION}")
configure_file(metadata.json.in "${CMAKE_CURRENT_BINARY_DIR}/metadata.json" @ONLY)
target_include_directories(winmiddlecursor PRIVATE "${CMAKE_CURRENT_BINARY_DIR}")

set(KWIN_EFFECT_INSTALL_DIR "lib/qt6/plugins/kwin/effects/plugins" CACHE STRING "Relative to CMAKE_INSTALL_PREFIX")
install(TARGETS winmiddlecursor DESTINATION ${KWIN_EFFECT_INSTALL_DIR})
