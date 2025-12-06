#!/usr/bin/env python3

import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


def clamp(value, vmin, vmax):
    return max(vmin, min(vmax, value))


class UINode(Node):

    def __init__(self):
        super().__init__('ui_node')
        self.get_logger().info("UI node started.")

        # Publishers: send to *input* topics, not directly to turtlesim
        self.pub1 = self.create_publisher(Twist, '/turtle1/cmd_vel_input', 10)
        self.pub2 = self.create_publisher(Twist, '/turtle2/cmd_vel_input', 10)

        # State for interactive loop
        self.waiting_input = True
        self.pending_command = None
        self.last_send_time = None

        # Timer driving the "UI loop"
        self.timer = self.create_timer(0.1, self.user_loop)

    def user_loop(self):
        # Ask user for a new command
        if self.waiting_input:
            try:
                turtle = input("Choose turtle (1 or 2): ").strip()
                if turtle not in ["1", "2"]:
                    print("Invalid choice, write 1 or 2.")
                    return

            
                lin = float(input("Linear velocity x [-10,10]: "))
                lin = clamp(lin, -10.0, 10.0)

                ang = float(input("Angular velocity [-10,10]: "))
                ang = clamp(ang, -10.0, 10.0)

                msg = Twist()
                msg.linear.x = lin
                msg.angular.z = ang

                self.pending_command = (turtle, msg)
                self.last_send_time = time.time()
                self.waiting_input = False

                self.get_logger().info(
                    f"Command: turtle{turtle}, lin={lin:.2f}, ang={ang:.2f}"
                )

            except Exception as e:
                print("Error:", e)
                return

        # Send that command for 1 second
        else:
            turtle, msg = self.pending_command
            pub = self.pub1 if turtle == "1" else self.pub2
            pub.publish(msg)

            if time.time() - self.last_send_time >= 1.0:
                stop = Twist()
                pub.publish(stop)
                print("Command finished. Turtle stopped.")
                self.waiting_input = True


def main(args=None):
    rclpy.init(args=args)
    node = UINode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
