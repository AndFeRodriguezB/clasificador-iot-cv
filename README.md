# 🚀 Clasificador de Objetos IoT con Computer Vision

![Status](https://img.shields.io/badge/Status-Desarrollado-success)
![Architecture](https://img.shields.io/badge/Architecture-Hybrid--Distributed-orange)
![OpenCV](https://img.shields.io/badge/Computer--Vision-OpenCV-green)

Este proyecto es un sistema de automatización industrial a escala que combina visión artificial y hardware embebido. Utiliza una **Raspberry Pi** para el procesamiento de imágenes en tiempo real y una **ESP32** para el control de actuadores, comunicados mediante un protocolo de red TCP/IP.

## 📸 Visualización del Proyecto

<p align="center">
  <img src="docs/montaje.png" alt="Montaje del Clasificador IoT" width="800">
</p>

---

## 🧠 Lógica de Visión y Robustez
A diferencia de sistemas de detección básicos, este software implementa una **condición de umbral de área ($Area > 5000px^2$)**:

* **Propósito:** Filtrar "ruido" visual y elementos pequeños del entorno que no pertenecen al flujo de la banda transportadora, asegurando que solo los objetos deseados activen el sistema.
* **Procesamiento:** Se utiliza el espacio de color **HSV** para una detección precisa bajo diferentes condiciones de iluminación y operaciones morfológicas (Erosión/Dilatación) para limpiar la máscara de detección.

## 🏗️ Arquitectura Híbrida y Flujo de Datos
El sistema opera bajo un modelo distribuido con responsabilidades separadas:

1.  **Módulo de Percepción (Raspberry Pi 4):** * Captura y procesa el stream de video.
    * Evalúa condiciones de color y dimensiones en tiempo real.
    * Al validar un objeto, actúa como cliente enviando un trigger JSON vía **Socket TCP**.
    * Registra eventos en un `datalog.json` y sirve un Dashboard web en Flask.

2.  **Módulo de Actuación (ESP32 con MicroPython):**
    * Gestiona un hilo independiente para el movimiento constante de la **banda transportadora**.
    * Escucha peticiones en el puerto `5001`.
    * Controla un **servomotor** para desviar el objeto hacia su compartimento correspondiente (Rojo o Azul).

## 🛠️ Tecnologías Utilizadas
* **Visión Artificial:** OpenCV (Filtros HSV, Contornos).
* **Backend & Dashboard:** Python 3, Flask, Jinja2.
* **Hardware Embebido:** MicroPython, ESP32, L298N (Puente H), Servomotores.
* **Comunicación:** Sockets TCP/IP, JSON, Multithreading.
* **DevOps:** Variables de entorno (`.env`), Git.

## 🚀 Instalación y Configuración

### 1. Preparación de la Raspberry Pi
```bash
# Clonar el repositorio
git clone [https://github.com/AndFeRodriguezB/clasificador-iot-cv.git](https://github.com/AndFeRodriguezB/clasificador-iot-cv.git)

# Ir a la carpeta del backend
cd Backend_rasp

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Edita el archivo .env con la IP de tu ESP32
2. Preparación de la ESP32
Asegúrate de tener instalado el firmware de MicroPython.

Carga los archivos de la carpeta firmware_esp en la placa.

Renombra secrets.py.example a secrets.py y coloca tus credenciales de WiFi.

📊 Dashboard de Monitoreo
Accede al panel de control desde cualquier dispositivo en la red local a través del puerto 5000. Permite visualizar el conteo de objetos procesados y el histórico de eventos con marca de tiempo.

🛡️ Seguridad
Las credenciales de red e IPs están protegidas mediante variables de entorno.

El archivo .gitignore está configurado para evitar la carga de datos sensibles y registros locales.

👤 Autor
Andres Felipe Rodriguez

LinkedIn: www.linkedin.com/in/andrés-felipe-rodríguez-balaguera-076b121b0

GitHub: @AndFeRodriguezB