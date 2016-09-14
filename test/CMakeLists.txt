project(tst_libxml2)
cmake_minimum_required(VERSION 2.8.12)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_executable(tst_libxml2 libxml2.cpp)

include_directories(tst_libxml2 ${CONAN_INCLUDE_DIRS})
target_link_libraries(tst_libxml2 ${CONAN_LIBS})
