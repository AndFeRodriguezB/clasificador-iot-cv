import network
import socket
from machine import Pin, PWM
import json
import _thread
import utime as time
import secrets

SSID = secrets.WIFI_SSID
PASSWORD = secrets.WIFI_PASS

servo = PWM(Pin(27), freq=50)
ena = PWM(Pin(14), freq=1000)
in1 = Pin(12, Pin.OUT)
in2 = Pin(13, Pin.OUT)

def mover_servo(grados):
    duty_calculado = int(20 + (grados / 180) * 100)
    servo.duty(duty_calculado)

def hilo_motor():
    try:
        in1.value(0)
        in2.value(1)
        ena.freq(50)
        vel = 575
        ena.duty(vel)
        while True:
            time.sleep(1)
    except:
        pass

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # Intento de limpieza profunda
    wlan.disconnect()
    time.sleep(2)
    
    wlan.connect(SSID, PASSWORD)
    print("Conectando a WiFi", end="")
    
    timeout = 20 # 20 segundos máximo
    while not wlan.isconnected() and timeout > 0:
        print(".", end="") # Esto te confirmará que el código corre
        time.sleep(1)
        timeout -= 1
        
    if wlan.isconnected():
        print("\nConectado! IP:", wlan.ifconfig()[0])
        return wlan.ifconfig()[0]
    else:
        print("\nERROR: Tiempo de espera agotado. Revisa el Hotspot.")
        return None

def iniciar_servidor(ip):
    if not ip: return
    addr = socket.getaddrinfo(ip, 5001)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print("Servidor listo en puerto 5001")
    while True:
        cl, addr_cli = s.accept()
        try:
            raw_data = cl.recv(1024).decode('utf-8')
            if not raw_data: continue
            mensaje = json.loads(raw_data.strip())
            color = mensaje.get("color")
            if color == "ROJO":
                mover_servo(180) #45
                time.sleep(1)
                mover_servo(90)
            elif color == "AZUL":
                mover_servo(0) #135
                time.sleep(1)
                mover_servo(90)
        except:
            pass
        finally:
            cl.close()

ip_esp = conectar_wifi()
if ip_esp:
    time.sleep(1)
    mover_servo(90)
    _thread.start_new_thread(hilo_motor, ())
    iniciar_servidor(ip_esp)