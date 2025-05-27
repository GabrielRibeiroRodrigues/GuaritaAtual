from ultralytics import YOLO
import cv2
import numpy as np 
from datetime import datetime
import gc
import os
import threading
import queue

results = {}

detector_placa = YOLO("C:\\Users\\12265587630\\Desktop\\bestn.pt")
cap = cv2.VideoCapture("C:\\Users\\12265587630\\Desktop\\g.mp4")
# cap = cv2.VideoCapture("rtsp://admin:123456789abc@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0")
# cap = cv2.VideoCapture("rtsp://admin:123456789abc@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0")

# cap = cv2.VideoCapture("rtsp://admin:123456789abc@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0")

veiculos = [2, 3, 5, 7]  
confianca_detectar_carro = 0.1
frame_nmr = -1
ret = True
intervalo_frames = 1
frame_anterior = -8

# Fila para salvar imagens das placas em thread separada
placa_queue = queue.Queue()

def salvar_placas_worker():
    while True:
        item = placa_queue.get()
        if item is None:
            break  # Sinal para encerrar a thread
        placa_carro_crop, car_id, frame_nmr, timestamp, angulos, data_hoje = item
        (h, w) = placa_carro_crop.shape[:2]
        center = (w // 2, h // 2)
        pasta_base = os.path.join(os.path.expanduser("~"), "Desktop", "placas_detectadas", data_hoje)
        if not os.path.exists(pasta_base):
            os.makedirs(pasta_base)
        for angulo in angulos:
            if angulo == 0:
                placa_rot = placa_carro_crop.copy()
            else:
                M = cv2.getRotationMatrix2D(center, -angulo, 1.0)
                placa_rot = cv2.warpAffine(placa_carro_crop, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            # FILTROS APLICADOS
            placa_carro_crop_gray = cv2.cvtColor(placa_rot, cv2.COLOR_BGR2GRAY)
            _, placa_carro_crop_thresh = cv2.threshold(placa_carro_crop_gray, 64, 255, cv2.THRESH_BINARY_INV)
            nome_arquivo = f"frame_{frame_nmr}_car_{car_id}_{timestamp}_ang{angulo}.png"
            caminho_arquivo = os.path.join(pasta_base, nome_arquivo)
            cv2.imwrite(caminho_arquivo, placa_rot)
        placa_queue.task_done()

# Inicia a thread de salvamento
thread_salvar = threading.Thread(target=salvar_placas_worker, daemon=True)
thread_salvar.start()

while ret:
    data_e_hora_atuais = datetime.now()
    data_e_hora_em_texto = data_e_hora_atuais.strftime('%Y-%m-%d %H:%M:%S')
    data_atual = data_e_hora_atuais.strftime("%Y-%m-%d")

    for i in range(intervalo_frames):
        frame_nmr += 1
        ret, frame = cap.read()
        if not ret or frame is None:
            print(f"Não foi possível ler o frame {frame_nmr}.")
            break
    if frame is None:
        continue

    # Detecção de placas usando apenas o modelo de placas
    detections_placas = detector_placa(frame)[0]
    placas_detectadas = []
    for detection in detections_placas.boxes.data.tolist():
        x1, y1, x2, y2, confianca_atual, class_id = detection
        if confianca_atual >= confianca_detectar_carro:
            placas_detectadas.append([x1, y1, x2, y2, confianca_atual])

    # Salvar diretamente as placas detectadas
    for placa in placas_detectadas:
        x1, y1, x2, y2, confianca_atual = placa
        if (0 <= x1 < frame.shape[1] and 0 <= x2 < frame.shape[1] and 0 <= y1 < frame.shape[0] and 0 <= y2 < frame.shape[0]):
            placa_carro_crop = frame[int(y1):int(y2), int(x1):int(x2)]
            angulos = [0, 15]
            if placa_carro_crop.size != 0:
                data_hoje = datetime.now().strftime("%Y-%m-%d")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                car_id = "placa"
                placa_queue.put((placa_carro_crop.copy(), car_id, frame_nmr, timestamp, angulos, data_hoje))
        else:
            print(f"Coordenadas da placa fora dos limites da imagemse")
    del frame
    gc.collect()  # Força o coletor de lixo a liberar memória

# Finaliza a thread de salvamento
placa_queue.put(None)
thread_salvar.join()

cap.release()