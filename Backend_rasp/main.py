import json
import os 
from datetime import datetime
from queue import Queue
import cv2
import socket
import numpy as np
from flask import Flask, render_template_string
import threading
import time

load_dotenv()

ESP_IP = os.getenv("ESP_IP")
PORT = int(os.getenv("PORT"))
DS_PORT = int(os.getenv("DS_PORT"))

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard Clasificador</title>
    <meta http-equiv="refresh" content="2"> 
    <style>
        body { font-family: Arial; text-align: center; background: #f4f4f4; }
        .card { background: white; padding: 20px; border-radius: 10px; display: inline-block; margin: 10px; box-shadow: 2px 2px 5px gray; min-width: 150px; }
        h1 { color: #333; }
        .rojo { color: red; font-size: 2em; font-weight: bold; }
        .azul { color: blue; font-size: 2em; font-weight: bold; }
        .btn-reset { background-color: #ff4444; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 1em; margin-top: 20px; }
        .btn-reset:hover { background-color: #cc0000; }
    </style>
</head>
<body>
    <h1>Panel de Control - Banda Clasificadora</h1>
    <div class="card">
        <h2>Objetos Rojos</h2>
        <p class="rojo">{{ rojos }}</p>
    </div>
    <div class="card">
        <h2>Objetos Azules</h2>
        <p class="azul">{{ azules }}</p>
    </div>
    <hr>
    <p>Ultimo evento: {{ ultimo }}</p>
    
    <form action="/reset" method="post">
        <button type="submit" class="btn-reset">Reiniciar Conteo Visual</button>
    </form>
</body>
</html>
"""

offset_rojos = 0
offset_azules = 0

@app.route('/')
def index():
    global offset_rojos, offset_azules
    rojos, azules = 0, 0
    ultimo_msg = "Esperando datos..."
    
    try:
        if os.path.exists(archivo_log):
            with open(archivo_log, "r") as f:
                for linea in f:
                    linea = linea.strip()
                    if not linea: continue 
                    
                    try:
                        dato = json.loads(linea)
                        if dato["evento"] == "ROJO": rojos += 1
                        elif dato["evento"] == "AZUL": azules += 1
                        ultimo_msg = f"{dato['ts']} - {dato['evento']}"
                    except json.JSONDecodeError:
                        continue 
    except Exception as e:
        print(f"Error en Dashboard: {e}")
    
    mostrar_rojos = max(0, rojos - offset_rojos)
    mostrar_azules = max(0, azules - offset_azules)
    
    return render_template_string(HTML_TEMPLATE, rojos=mostrar_rojos, azules=mostrar_azules, ultimo=ultimo_msg)
	
@app.route('/reset', methods=['POST'])
def reset():
    global offset_rojos, offset_azules
    total_rojos, total_azules = 0, 0
    try:
        if os.path.exists(archivo_log):
            with open(archivo_log, "r") as f:
                for linea in f:
                    linea = linea.strip()
                    if not linea: continue
                    try:
                        dato = json.loads(linea)
                        if dato["evento"] == "ROJO": total_rojos += 1
                        elif dato["evento"] == "AZUL": total_azules += 1
                    except:
                        continue
        
        offset_rojos = total_rojos
        offset_azules = total_azules
        print(f"Reset exitoso. Offsets: R={offset_rojos}, A={offset_azules}")
        
    except Exception as e:
        print(f"Error en Reset: {e}")

    from flask import redirect
    return redirect('/')

def hilo_web():
	app.run(host='0.0.0.0', port=DS_PORT, debug=False, use_reloader=False)
				 
		 
ruta_base = os.path.dirname(os.path.abspath(__file__))
archivo_log = os.path.join(ruta_base, "datalog.json")

cola_eventos = Queue()
file_log = archivo_log

threading.Thread(target=hilo_web, daemon=True).start()

def hilo_logger():
	print("Hilo Logger: Iniciado.")
	while True:
		evento = cola_eventos.get()
		if evento is None: break
		
		trama = {
			"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
			"evento": evento["evento"],
			"mensaje":f"Objeto{evento['evento']} clasificado"
		}
		
		with open(file_log, "a") as f:
			f.write(json.dumps(trama) + "\n")
		
		cola_eventos.task_done()

def enviar_esp(color_detectado):
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.settimeout(1)
		s.connect((ESP_IP, PORT))
		
		trama = json.dumps({"color": color_detectado}) + "\n"
		s.sendall(trama.encode('utf-8'))
		s.close()
	except Exception as e:
		print(f"No se pudo enviar a la esp: {e}")

class CameraStream:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src, cv2.CAP_V4L2)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()


azul_bajo = np.array([90, 100, 100])
azul_alto = np.array([130, 255, 255])

rojo_bajo1 = np.array([0, 150, 50])
rojo_alto1 = np.array([10, 255, 255])
rojo_bajo2 = np.array([170, 150, 50])
rojo_alto2 = np.array([180, 255, 255])

threading.Thread(target=hilo_logger, daemon=True).start()

vs = CameraStream(src=0).start()
time.sleep(2.0) 


ultimo_evento = ""
tiempo_bloqueo = 0

while True:
    frame = vs.read()
    if frame is None: break
    
    
    frame = cv2.resize(frame, (480, 360))
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    
    mask_azul = cv2.inRange(hsv, azul_bajo, azul_alto)
    m1 = cv2.inRange(hsv, rojo_bajo1, rojo_alto1)
    m2 = cv2.inRange(hsv, rojo_bajo2, rojo_alto2)
    mask_rojo = cv2.add(m1, m2)

    
    kernel = np.ones((5, 5), np.uint8)
    mask_azul = cv2.morphologyEx(mask_azul, cv2.MORPH_OPEN, kernel)
    mask_rojo = cv2.morphologyEx(mask_rojo, cv2.MORPH_OPEN, kernel)

    color_detectado = None

    
    for mask, nombre, color_bgr in [(mask_azul, "AZUL", (255, 0, 0)), (mask_rojo, "ROJO", (0, 0, 255))]:
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            area = cv2.contourArea(c)
            if area > 5000: 
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color_bgr, 2)
                color_detectado = nombre
    
    if color_detectado and color_detectado != ultimo_evento and time.time() > tiempo_bloqueo:
        print(f"EVENTO DETECTADO: {color_detectado}")
        print(f"Enviando a log: {color_detectado}")
        cola_eventos.put({"evento": color_detectado})
        
        threading.Thread(target=enviar_esp, args=(color_detectado,),daemon=True).start()
        
        ultimo_evento = color_detectado
        tiempo_bloqueo = time.time() + 3.0
    elif not color_detectado:
        ultimo_evento = ""

    cv2.imshow("Clasificador Robusto", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

vs.stop()
cv2.destroyAllWindows()
