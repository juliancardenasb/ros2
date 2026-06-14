import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class Controlador(Node):
    def __init__(self):
        super().__init__('controlador')
        self.publisher = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.timer = self.create_timer(0.5, self.mover)
        self.get_logger().info('Nodo iniciado')

    def mover(self):
        msg = Twist()
        msg.linear.x = 2.0
        msg.angular.z = 1.0
        self.publisher.publish(msg)


def main():
    rclpy.init()
    nodo = Controlador()
    rclpy.spin(nodo)


if __name__ == '__main__':
    main()
