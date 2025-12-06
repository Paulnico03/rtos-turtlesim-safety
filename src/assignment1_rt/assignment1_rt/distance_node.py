#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32


class TurtleState:
    """Internal state for each turtle, mirroring your friend's C++ struct."""

    def __init__(self, name: str):
        self.name = name

        # Pose info
        self.pose: Pose | None = None
        self.have_pose: bool = False

        # Last desired command from UI
        self.desired_cmd: Twist = Twist()
        self.got_cmd: bool = False

        # Border handling
        self.was_outside: bool = False            # went outside at least once
        self.border_turning: bool = False         # currently spinning 180°
        self.border_ticks_left: int = 0           # ticks remaining in spin
        self.blocked_until_new_cmd: bool = False  # stop until NEW UI cmd after spin


class SafetyNode(Node):

    def __init__(self):
        super().__init__('safety_node')
        print(">>> USING SAFETY LOGIC distance_node.py <<<")

        # Parameters: same semantics as C++ version
        self.declare_parameter('distance_threshold', 2.0)
        self.declare_parameter('min_limit', 1.0)
        self.declare_parameter('max_limit', 10.0)
        self.declare_parameter('border_margin', 0.5)

        self.distance_threshold = self.get_parameter(
            'distance_threshold').value
        self.min_limit = self.get_parameter('min_limit').value
        self.max_limit = self.get_parameter('max_limit').value
        self.border_margin = self.get_parameter('border_margin').value

        # Turtle states
        self.t1 = TurtleState("turtle1")
        self.t2 = TurtleState("turtle2")

        # Collision separation state
        self.separating = False
        self.separation_ticks_left = 0

        # Pose subscribers
        self.create_subscription(
            Pose, '/turtle1/pose', self.pose1_cb, 10)
        self.create_subscription(
            Pose, '/turtle2/pose', self.pose2_cb, 10)

        
        self.create_subscription(
            Twist, '/turtle1/cmd_vel_input', self.cmd1_in_cb, 10)
        self.create_subscription(
            Twist, '/turtle2/cmd_vel_input', self.cmd2_in_cb, 10)

        
        self.cmd1_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.cmd2_pub = self.create_publisher(Twist, '/turtle2/cmd_vel', 10)

    
        self.dist_pub = self.create_publisher(Float32, '/distance', 10)

       
        self.timer = self.create_timer(0.02, self.timer_callback)

        self.get_logger().info(
            f"Safety node started (distance_threshold={self.distance_threshold:.2f}, "
            f"limits=[{self.min_limit:.2f}, {self.max_limit:.2f}], "
            f"margin={self.border_margin:.2f})"
        )

    

    def pose1_cb(self, msg: Pose):
        self.t1.pose = msg
        self.t1.have_pose = True

    def pose2_cb(self, msg: Pose):
        self.t2.pose = msg
        self.t2.have_pose = True

    def cmd1_in_cb(self, msg: Twist):
        self.t1.desired_cmd = msg
        self.t1.got_cmd = True

        # If we were blocked after border spin and not spinning now → unblock
        if self.t1.blocked_until_new_cmd and not self.t1.border_turning:
            self.t1.blocked_until_new_cmd = False
            self.get_logger().info(
                "New command for turtle1 received, unblocking after border.")

    def cmd2_in_cb(self, msg: Twist):
        self.t2.desired_cmd = msg
        self.t2.got_cmd = True

        if self.t2.blocked_until_new_cmd and not self.t2.border_turning:
            self.t2.blocked_until_new_cmd = False
            self.get_logger().info(
                "New command for turtle2 received, unblocking after border.")

   

    def timer_callback(self):
        # Start with zero commands
        safe_cmd1 = Twist()
        safe_cmd2 = Twist()

        # If we’re currently separating the turtles, override everything
        if self.separating:
            self.apply_separation(safe_cmd1, safe_cmd2)
            self.cmd1_pub.publish(safe_cmd1)
            self.cmd2_pub.publish(safe_cmd2)
            return

        # Start from desired commands 
        if self.t1.got_cmd:
            safe_cmd1 = self.t1.desired_cmd
        if self.t2.got_cmd:
            safe_cmd2 = self.t2.desired_cmd

        # Collision handling + distance publishing
        have_both = self.t1.have_pose and self.t2.have_pose
        dist = 0.0

        if have_both:
            dx = self.t1.pose.x - self.t2.pose.x
            dy = self.t1.pose.y - self.t2.pose.y
            dist = math.sqrt(dx * dx + dy * dy)

            dist_msg = Float32()
            dist_msg.data = float(dist)
            self.dist_pub.publish(dist_msg)

        # 1) Collision avoidance
        if have_both and dist < self.distance_threshold:
            self.start_separation(dist)
            safe_cmd1 = Twist()
            safe_cmd2 = Twist()
        else:
            # 2) Border handling per turtle
            self.handle_border(self.t1, safe_cmd1)
            self.handle_border(self.t2, safe_cmd2)

        # Publish final filtered commands
        self.cmd1_pub.publish(safe_cmd1)
        self.cmd2_pub.publish(safe_cmd2)

    

    def start_separation(self, dist: float):
        self.separating = True
        self.separation_ticks_left = 30 
        self.get_logger().warn(
            f"Turtles too close ({dist:.2f} < {self.distance_threshold:.2f}). "
            "Starting separation."
        )

    def apply_separation(self, cmd1: Twist, cmd2: Twist):
        cmd1.linear.x = 1.0
        cmd1.angular.z = -1.0
        cmd2.linear.x = -1.0
        cmd2.angular.z = 1.0

        self.separation_ticks_left -= 1
        if self.separation_ticks_left <= 0:
            # Stop and finish separation
            cmd1.linear.x = cmd1.angular.z = 0.0
            cmd2.linear.x = cmd2.angular.z = 0.0
            self.separating = False
            self.get_logger().info(
                "Separation done. Turtles can move again.")

   

    def handle_border(self, t: TurtleState, cmd: Twist):
        if not t.have_pose:
            return

        x = t.pose.x
        y = t.pose.y

        # outside = touching/over the turtlesim box
        outside = (
            x <= self.min_limit or x >= self.max_limit or
            y <= self.min_limit or y >= self.max_limit
        )

        # well_inside = safely away from borders by a margin
        well_inside = (
            x > (self.min_limit + self.border_margin) and
            x < (self.max_limit - self.border_margin) and
            y > (self.min_limit + self.border_margin) and
            y < (self.max_limit - self.border_margin)
        )

        # First hit: inside → outside
        if outside and not t.was_outside:
            t.was_outside = True
            t.border_turning = True
            t.blocked_until_new_cmd = True

            # Number of timer ticks for ~180°
            # omega = 1.5 rad/s, dt = 0.02 s → ticks ≈ pi / (1.5*0.02) ≈ 105
            t.border_ticks_left = 105

            self.get_logger().warn(
                f"{t.name} hit border (x={x:.2f}, y={y:.2f}). "
                "Stopping and spinning 180 degrees."
            )

        # Re-enter safe interior → re-arm logic
        if well_inside and t.was_outside:
            t.was_outside = False
            self.get_logger().info(
                f"{t.name} back well inside safe area."
            )

        # While performing the 180° spin, override command
        if t.border_turning and t.border_ticks_left > 0:
            cmd.linear.x = 0.0
            cmd.linear.y = 0.0
            cmd.angular.z = 1.5  # turn in place

            t.border_ticks_left -= 1
            if t.border_ticks_left == 0:
                t.border_turning = False
                # After finishing spin, keep turtle stopped
                cmd.linear.x = cmd.linear.y = cmd.angular.z = 0.0
                self.get_logger().info(
                    f"{t.name} finished 180-degree turn; waiting for new command."
                )
            return

        # After spin is done, if still blocked, we keep full stop
        if t.blocked_until_new_cmd:
            cmd.linear.x = cmd.linear.y = cmd.angular.z = 0.0
            return


def main(args=None):
    rclpy.init(args=args)
    node = SafetyNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
