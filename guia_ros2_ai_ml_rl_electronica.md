# Guía completa: ROS2 + AI/ML + RL + Electrónica

---

## 1. Arquitectura general

```
┌─────────────────────────────────────────────────────┐
│                    PC / Laptop                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  Nav2    │  │ ML Model │  │  Agente RL        │  │
│  │ (planif.)│  │(detección│  │ (StableBaselines) │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│       └─────────────┴─────────────────┘             │
│                    ROS2 (topics/services)            │
└───────────────────────┬─────────────────────────────┘
                        │ WiFi / Serial
┌───────────────────────┴─────────────────────────────┐
│               Raspberry Pi                           │
│         ROS2 (nodos de bajo nivel)                  │
└───────────────────────┬─────────────────────────────┘
                        │ Serial / I2C / PWM
┌───────────────────────┴─────────────────────────────┐
│          Arduino / ESP32 (micro-ROS)                │
│     Motores │ Sensores │ Encoders │ IMU             │
└─────────────────────────────────────────────────────┘
```

---

## 2. AI / Computer Vision con ROS2

### Cómo funciona

Un nodo recibe imágenes de una cámara, las procesa con un modelo y publica el resultado.

```
/camera/image_raw → [Nodo detección] → /detecciones
```

### Instalación

```bash
pip install torch torchvision opencv-python
sudo apt install ros-jazzy-vision-msgs -y
sudo apt install ros-jazzy-usb-cam -y
```

### Nodo de detección con YOLOv8

```python
# ros2/vision/src/detector/detector/nodo_detector.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray, Detection2D, BoundingBox2D
from cv_bridge import CvBridge
from ultralytics import YOLO

class Detector(Node):
    def __init__(self):
        super().__init__('detector')
        self.modelo = YOLO('yolov8n.pt')  # descarga automático
        self.bridge = CvBridge()
        self.sub = self.create_subscription(Image, '/camera/image_raw', self.callback, 10)
        self.pub = self.create_publisher(Detection2DArray, '/detecciones', 10)

    def callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        resultados = self.modelo(frame)

        detecciones = Detection2DArray()
        for r in resultados[0].boxes:
            d = Detection2D()
            d.bbox.center.position.x = float(r.xywh[0][0])
            d.bbox.center.position.y = float(r.xywh[0][1])
            d.bbox.size_x = float(r.xywh[0][2])
            d.bbox.size_y = float(r.xywh[0][3])
            detecciones.detections.append(d)

        self.pub.publish(detecciones)

def main():
    rclpy.init()
    rclpy.spin(Detector())
```

```bash
pip install ultralytics cv_bridge
```

---

## 3. Reinforcement Learning con Gazebo

### Cómo funciona

```
Gazebo simula el mundo
    ↓ estado (posición, sensores)
Agente RL decide acción
    ↓ acción (velocidad)
Gazebo ejecuta y da recompensa
    ↓ repite miles de veces
Robot aprende a navegar/evitar obstáculos
```

### Instalación

```bash
sudo apt install ros-jazzy-gazebo-ros-pkgs -y
pip install stable-baselines3 gymnasium numpy
```

### Entorno Gym para ROS2

```python
# ros2/rl_navegacion/entorno.py
import gymnasium as gym
import numpy as np
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan

class EntornoRobot(gym.Env):
    def __init__(self):
        super().__init__()
        rclpy.init()
        self.nodo = Node('entorno_rl')

        self.action_space = gym.spaces.Box(
            low=np.array([-1.0, -1.0]),
            high=np.array([1.0, 1.0]),
            dtype=np.float32
        )

        self.observation_space = gym.spaces.Box(
            low=0.0, high=10.0, shape=(360,), dtype=np.float32
        )

        self.pub_vel = self.nodo.create_publisher(Twist, '/cmd_vel', 10)
        self.lidar_data = np.zeros(360)
        self.nodo.create_subscription(LaserScan, '/scan', self.cb_lidar, 10)

    def cb_lidar(self, msg):
        self.lidar_data = np.array(msg.ranges)

    def step(self, accion):
        cmd = Twist()
        cmd.linear.x = float(accion[0])
        cmd.angular.z = float(accion[1])
        self.pub_vel.publish(cmd)

        rclpy.spin_once(self.nodo, timeout_sec=0.1)

        obs = self.lidar_data
        min_distancia = np.min(obs)
        colision = min_distancia < 0.3
        recompensa = -100.0 if colision else accion[0]
        terminado = colision

        return obs, recompensa, terminado, False, {}

    def reset(self, **kwargs):
        return self.lidar_data, {}
```

### Entrenar el agente

```python
# ros2/rl_navegacion/entrenar.py
from stable_baselines3 import PPO
from entorno import EntornoRobot

entorno = EntornoRobot()
modelo = PPO('MlpPolicy', entorno, verbose=1)
modelo.learn(total_timesteps=100_000)
modelo.save('robot_navegacion')
```

```bash
python3 entrenar.py
```

---

## 4. Electrónica: micro-ROS en Arduino/ESP32

### Arquitectura

```
PC (ROS2) ←—— WiFi/Serial ——→ ESP32 (micro-ROS) → Motores / Sensores
```

### Instalación micro-ROS

```bash
sudo apt install ros-jazzy-micro-ros-agent -y
```

En Arduino IDE instalar la librería: **micro_ros_arduino**

### Código ESP32 (Arduino)

```cpp
#include <micro_ros_arduino.h>
#include <rcl/rcl.h>
#include <rclc/rclc.h>
#include <geometry_msgs/msg/twist.h>

#define MOTOR_IZQ_A 18
#define MOTOR_IZQ_B 19
#define MOTOR_DER_A 21
#define MOTOR_DER_B 22

rcl_subscription_t suscriptor;
geometry_msgs__msg__Twist msg;
rclc_executor_t executor;
rcl_allocator_t allocator;
rclc_support_t support;
rcl_node_t nodo;

void mover_motores(float linear, float angular) {
    int izq = (linear + angular) * 255;
    int der = (linear - angular) * 255;
    izq = constrain(izq, -255, 255);
    der = constrain(der, -255, 255);

    digitalWrite(MOTOR_IZQ_A, izq > 0);
    digitalWrite(MOTOR_IZQ_B, izq < 0);
    analogWrite(MOTOR_DER_A, abs(der));

    digitalWrite(MOTOR_DER_A, der > 0);
    digitalWrite(MOTOR_DER_B, der < 0);
    analogWrite(MOTOR_DER_A, abs(izq));
}

void callback(const void* msg_in) {
    const geometry_msgs__msg__Twist* cmd = (geometry_msgs__msg__Twist*)msg_in;
    mover_motores(cmd->linear.x, cmd->angular.z);
}

void setup() {
    set_microros_wifi_transports("TU_WIFI", "TU_PASSWORD", "IP_DEL_PC", 8888);

    pinMode(MOTOR_IZQ_A, OUTPUT);
    pinMode(MOTOR_IZQ_B, OUTPUT);
    pinMode(MOTOR_DER_A, OUTPUT);
    pinMode(MOTOR_DER_B, OUTPUT);

    allocator = rcl_get_default_allocator();
    rclc_support_init(&support, 0, NULL, &allocator);
    rclc_node_init_default(&nodo, "esp32_motores", "", &support);
    rclc_subscription_init_default(&suscriptor, &nodo,
        ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist), "/cmd_vel");
    rclc_executor_init(&executor, &support.context, 1, &allocator);
    rclc_executor_add_subscription(&executor, &suscriptor, &msg, &callback, ON_NEW_DATA);
}

void loop() {
    rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10));
}
```

### Correr el agente en el PC

```bash
ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888
```

---

## 5. Proyecto completo: Robot que aprende a seguir personas

### Flujo del sistema

```
Cámara → [Detector YOLO] → /persona_detectada
                                    ↓
                          [Nodo de control RL]
                                    ↓
                              /cmd_vel
                                    ↓
                    ESP32 → Motores (robot físico)
```

### Estructura del proyecto

```
ros2/
  tortuga/          ← ejemplo 1: control automático
  teclado/          ← ejemplo 2: control por teclado
  vision/           ← ejemplo 3: detección YOLO
  rl_navegacion/    ← ejemplo 4: entrenamiento RL en Gazebo
  robot_completo/   ← ejemplo 5: todo integrado + hardware
```

### Hardware necesario

| Componente | Precio aprox. |
|---|---|
| Raspberry Pi 4 (2GB) | $35-50 USD |
| ESP32 | $5-10 USD |
| Puente H L298N | $3-5 USD |
| Motores DC + ruedas | $10-15 USD |
| Cámara USB o Pi Camera | $10-25 USD |
| Chasis robot 2WD | $10-15 USD |
| Batería LiPo 7.4V | $15-20 USD |
| **Total** | **~$90-140 USD** |

---

## 6. Ruta de aprendizaje recomendada

```
1. Tortuga (hecho) ✓
2. Control por teclado
3. Nodo con cámara USB + OpenCV
4. Detección YOLO
5. Simulación en Gazebo
6. RL básico en Gazebo
7. Hardware: ESP32 + motores
8. Robot completo
```
