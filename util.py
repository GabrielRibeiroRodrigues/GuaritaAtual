import string
import easyocr
import psycopg2
import cv2
import numpy as np
from paddleocr import PaddleOCR
from datetime import datetime  # Adicionado para data/hora

conexao = psycopg2.connect(
    dbname="pci_transito",
    user="postgres",
    password="123456",
    host="localhost",
    port="5432"
)
cursor = conexao.cursor()

reader = easyocr.Reader(['en'], gpu=False)
# Configuração aprimorada do PaddleOCR para placas brasileiras
ocr = PaddleOCR(
    lang='pt',                # Idioma português
    use_angle_cls=False,      # Desabilita classificador de ângulo
    use_gpu=False,            # GPU opcional
    det_limit_side_len=640    # Ajuste conforme o tamanho das suas imagens (320, 640, 960, etc)
)
char_to_int = {'O': '0', 'I': '1', 'J': '3', 'A': '4', 'G': '6', 'S': '5'}
int_to_char = {'0': 'O', '1': 'I', '3': 'J', '4': 'A', '6': 'G', '5': 'S'}

def license_complies_format(text):
    if len(text) != 7:
        return False
    if (text[0] in string.ascii_uppercase or text[0] in int_to_char.keys()) and \
       (text[1] in string.ascii_uppercase or text[1] in int_to_char.keys()) and \
       (text[2] in ['0','1','2','3','4','5','6','7','8','9'] or text[2] in char_to_int.keys()) and \
       (text[3] in ['0','1','2','3','4','5','6','7','8','9'] or text[3] in char_to_int.keys()) and \
       (text[4] in string.ascii_uppercase or text[4] in int_to_char.keys()) and \
       (text[5] in string.ascii_uppercase or text[5] in int_to_char.keys()) and \
       (text[6] in string.ascii_uppercase or text[6] in int_to_char.keys()):
        return True
    if (text[0] in string.ascii_uppercase or text[0] in int_to_char.keys()) and \
       (text[1] in string.ascii_uppercase or text[1] in int_to_char.keys()) and \
       (text[2] in string.ascii_uppercase or text[2] in int_to_char.keys()) and \
       (text[3] in ['0','1','2','3','4','5','6','7','8','9'] or text[3] in char_to_int.keys()) and \
       (text[4] in ['0','1','2','3','4','5','6','7','8','9'] or text[4] in char_to_int.keys()) and \
       (text[5] in ['0','1','2','3','4','5','6','7','8','9'] or text[5] in char_to_int.keys()) and \
       (text[6] in ['0','1','2','3','4','5','6','7','8','9'] or text[6] in char_to_int.keys()):
        return True
    if (text[0] in string.ascii_uppercase or text[0] in int_to_char.keys()) and \
       (text[1] in string.ascii_uppercase or text[1] in int_to_char.keys()) and \
       (text[2] in string.ascii_uppercase or text[2] in int_to_char.keys()) and \
       (text[3] in ['0','1','2','3','4','5','6','7','8','9'] or text[3] in char_to_int.keys()) and \
       (text[4] in string.ascii_uppercase or text[4] in int_to_char.keys()) and \
       (text[5] in ['0','1','2','3','4','5','6','7','8','9'] or text[5] in char_to_int.keys()) and \
       (text[6] in ['0','1','2','3','4','5','6','7','8','9'] or text[6] in char_to_int.keys()):
        return True
    return False

def formato_placa(text):
    license_plate_ = ''
    for j in range(7):
        if j in [0, 1, 2]:
            if text[j] in int_to_char:
                license_plate_ += int_to_char[text[j]]
            else:
                license_plate_ += text[j]
        elif j == 3:
            if text[j] in char_to_int:
                license_plate_ += char_to_int[text[j]]
            else:
                license_plate_ += text[j]
        elif j == 4:
            if text[j] in string.ascii_uppercase or text[j] in int_to_char:
                if text[j] in int_to_char:
                    license_plate_ += int_to_char[text[j]]
                else:
                    license_plate_ += text[j]
            elif text[j] in char_to_int:
                license_plate_ += char_to_int[text[j]]
            else:
                license_plate_ += text[j]
        elif j in [5, 6]:
            if text[j] in char_to_int:
                license_plate_ += char_to_int[text[j]]
            else:
                license_plate_ += text[j]
    return license_plate_

def preprocess_for_tesseract(plate_crop):
    if len(plate_crop.shape) == 3:
        gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
    else:
        gray = plate_crop.copy()
    scale_percent = 150
    width = int(gray.shape[1] * scale_percent / 100)
    height = int(gray.shape[0] * scale_percent / 100)
    gray = cv2.resize(gray, (width, height), interpolation=cv2.INTER_LINEAR)
    blur = cv2.medianBlur(gray, 3)
    _, thresh = cv2.threshold(blur, 120, 255, cv2.THRESH_BINARY)
    coords = np.column_stack(np.where(thresh > 0))
    angle = -(15)
    (h, w) = thresh.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    deskewed = cv2.warpAffine(thresh, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return deskewed

def ler_placas(placa_carro_crop):
    thresh = preprocess_for_tesseract(placa_carro_crop)
    detections = reader.readtext(thresh)
    for detection in detections:
        bbox, text, score = detection
        text = text.upper().replace(' ', '')
        if license_complies_format(text):
            return formato_placa(text), score
    return None, None



# Buffer para batch insert
buffer_leituras = []
BUFFER_SIZE = 1  # ajuste conforme necessário

def salvar_no_postgres(frame_nmr, car_id, license_number, license_number_score):
    global buffer_leituras
    data_hora_atual = datetime.now()  # Data/hora atual
    buffer_leituras.append((int(frame_nmr), int(car_id), license_number, float(license_number_score), data_hora_atual))
    if len(buffer_leituras) >= BUFFER_SIZE:
        try:
            comando_sql = """
            INSERT INTO transito_leitura_placa (frame_nmr,car_id,license_number,license_number_score,data_hora)
            VALUES (%s, %s, %s, %s, %s);
            """
            cursor.executemany(comando_sql, buffer_leituras)
            conexao.commit()
            buffer_leituras = []
        except Exception:
            conexao.rollback()
            buffer_leituras = []

def flush_buffer_leituras():
    global buffer_leituras
    if buffer_leituras:
        try:
            comando_sql = """
            INSERT INTO transito_leitura_placa (frame_nmr,car_id,license_number,license_number_score,data_hora)
            VALUES (%s, %s, %s, %s, %s);
            """
            cursor.executemany(comando_sql, buffer_leituras)
            conexao.commit()
        except Exception:
            conexao.rollback()
        buffer_leituras = []

def limpar_texto_placa(texto):
    # Remove caracteres indesejados comuns em OCR de placas
    caracteres_remover = "-.!@#$%^&*()[]{};:,<>?/\\|`~'\""
    return ''.join(c for c in texto if c not in caracteres_remover)

def ler_placas2(placa_carro_crop):
    # paddleocr espera imagens em RGB
    img_rgb = cv2.cvtColor(placa_carro_crop, cv2.COLOR_BGR2RGB)

    # Faz OCR
    results = ocr.ocr(img_rgb, cls=True)
    
    # Verificar se o resultado do OCR é None
    if not results:
        print("Nenhum texto detectado.")
        return None, None

    # Imprimir resultados do OCR para depuração
    print("Resultados do OCR:")
    for line in results:
        if line:  # Verifica se a linha não é None ou vazia
            for detection in line:
                print(f"Texto: {detection[1][0]} - Confiança: {detection[1][1]}")
    
    # Processar resultados e retornar se encontrar uma placa válida
    for line in results:
        if line:  # Verifica se a linha não é None ou vazia
            for detection in line:
                text = detection[1][0]
                score = detection[1][1]
                text = text.upper().replace(' ', '')
                text = limpar_texto_placa(text)  # Remove caracteres indesejados
                if license_complies_format(text):
                    return formato_placa(text), score

    return None, None

