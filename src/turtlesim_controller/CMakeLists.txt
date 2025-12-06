cmake_minimum_required(VERSION 3.8)
project(turtlesim_controller)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(turtlesim REQUIRED)
find_package(geometry_msgs REQUIRED)

add_executable(turtle src/turtle_controller.cpp)
ament_target_dependencies(turtle rclcpp turtlesim geometry_msgs)

install(TARGETS
  turtle
  DESTINATION lib/${PROJECT_NAME})

ament_package()
