#include "rclcpp/rclcpp.hpp"
#include "turtlesim/msg/pose.hpp"
#include "geometry_msgs/msg/twist.hpp"

using std::placeholders::_1;

class MinimalController : public rclcpp::Node
{
public:
  MinimalController() : Node("minimal_controller"), x_(0.0)
  {
    // Subscriber: read turtle pose
    sub_ = this->create_subscription<turtlesim::msg::Pose>(
      "turtle1/pose", 10, std::bind(&MinimalController::pose_callback, this, _1));

    // Publisher: send velocity commands
    pub_ = this->create_publisher<geometry_msgs::msg::Twist>(
      "turtle1/cmd_vel", 10);

    // Timer: send command every 100 ms
    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(100),
      std::bind(&MinimalController::timer_callback, this));
  }

private:
  void pose_callback(const turtlesim::msg::Pose::SharedPtr msg)
  {
    x_ = msg->x;
    RCLCPP_INFO(this->get_logger(), "Pose: x=%.2f y=%.2f theta=%.2f",
                msg->x, msg->y, msg->theta);
  }

  void timer_callback()
  {
    geometry_msgs::msg::Twist cmd;

    if (x_ < 9.0) {
      cmd.linear.x = 2.0;   // move forward
      cmd.angular.z = 0.0;  // no rotation
    } else {
      cmd.linear.x = 0.0;   // stop
      cmd.angular.z = 0.0;
    }

    pub_->publish(cmd);
  }

  rclcpp::Subscription<turtlesim::msg::Pose>::SharedPtr sub_;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr pub_;
  rclcpp::TimerBase::SharedPtr timer_;
  float x_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<MinimalController>());
  rclcpp::shutdown();
  return 0;
}
