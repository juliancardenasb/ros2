import sys
import tty
import termios
import threading
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

INSTRUCCIONES = """
Control de la tortuga por teclado
----------------------------------
   W
A  S  D

W - adelante
S - atras
A - girar izquierda
D - girar derecha
Q - salir
"""

VELOCIDAD_LINEAL = 2.0
VELOCIDAD_ANGULAR = 1.5

TECLAS = {
    'w': ( VELOCIDAD_LINEAL,  0.0),
    's': (-VELOCIDAD_LINEAL,  0.0),
    'a': ( 0.0,  VELOCIDAD_ANGULAR),
    'd': ( 0.0, -VELOCIDAD_ANGULAR),
}


def leer_tecla():
    fd = sys.stdin.fileno()
    config = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        tecla = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, config)
    return tecla


class ControlTeclado(Node):
    def __init__(self):
        super().__init__('control_teclado')
        self.pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.linear = 0.0
        self.angular = 0.0
        # Publica la velocidad actual 10 veces por segundo
        self.create_timer(0.1, self.publicar)

    def publicar(self):
        msg = Twist()
        msg.linear.x = self.linear
        msg.angular.z = self.angular
        self.pub.publish(msg)

    def set_velocidad(self, linear, angular):
        self.linear = linear
        self.angular = angular


def main():
    rclpy.init()
    nodo = ControlTeclado()

    # ROS2 corre en un hilo separado para no bloquear el teclado
    hilo = threading.Thread(target=rclpy.spin, args=(nodo,), daemon=True)
    hilo.start()

    print(INSTRUCCIONES)

    try:
        while True:
            tecla = leer_tecla().lower()
            if tecla == 'q':
                break
            elif tecla in TECLAS:
                nodo.set_velocidad(*TECLAS[tecla])
            else:
                nodo.set_velocidad(0.0, 0.0)
    except Exception as e:
        print(e)
    finally:
        nodo.set_velocidad(0.0, 0.0)
        rclpy.shutdown()


if __name__ == '__main__':
    main()
