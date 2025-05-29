import string
import psycopg2
import cv2
import numpy as np
from paddleocr import PaddleOCR
from datetime import datetime

conexao = psycopg2.connect(
    dbname="pci_transito",
    user="postgres",
    password="123456",
    host="localhost",
    port="5432"
)
cursor = conexao.cursor()

ocr = PaddleOCR(
    lang='pt',
    use_angle_cls=False,
    use_gpu=False,
    det_limit_side_len=640
)
char_to_int = {'O': '0', 'I': '1', 'J': '3', 'A': '4', 'G': '6', 'S': '5', 'B': '8'} # Added B:8
int_to_char = {'0': 'O', '1': 'I', '3': 'J', '4': 'A', '6': 'G', '5': 'S', '8': 'B'} # Added 8:B

PALAVRAS_IGNORAR = {
    'BRASIL', 'MERCOSUL', 'BRAZIL', # País e bloco
    # Estados (siglas e nomes comuns, já limpos e em maiúsculas)
    'SP', 'SAOPAULO', 'RJ', 'RIODEJANEIRO', 'MG', 'MINASGERAIS',
    'ES', 'ESPIRITOSANTO', 'PR', 'PARANA', 'SC', 'SANTACATARINA', 'RS', 'RIOGRANDEDOSUL',
    'MS', 'MATOGROSSODOSUL', 'MT', 'MATOGROSSO', 'GO', 'GOIAS', 'DF', 'DISTRITOFEDERAL',
    'BA', 'BAHIA', 'SE', 'SERGIPE', 'AL', 'ALAGOAS', 'PE', 'PERNAMBUCO', 'PB', 'PARAIBA',
    'RN', 'RIOGRANDEDONORTE', 'CE', 'CEARA', 'PI', 'PIAUI', 'MA', 'MARANHAO', 'TO', 'TOCANTINS',
    'PA', 'PARA', 'AP', 'AMAPA', 'RR', 'RORAIMA', 'AM', 'AMAZONAS', 'AC', 'ACRE', 'RO', 'RONDONIA',
    # Cidades (limpas, sem acentos e em maiúsculas)
    # Mantendo as fornecidas e adicionando mais da região (Sul de Minas) e outras importantes
    'GUAXUPE', 'MUZAMBINHO', 'NOVAREZENDE', 'SAOPEDRODAUNIAO', 'JURUAIA', # Fornecidas pelo usuário (normalizadas)
    'PASSOS', 'POCOSDECALDAS', 'VARGINHA', 'ALFENAS', 'LAVRAS', 'UBERLANDIA', 'UBERABA', # Minas Gerais
    'BELOHORIZONTE', 'JUIZDEFORA', 'MONTESCLAROS', 'DIVINOPOLIS', 'GOVERNADORVALADARES',
    'CAMPINAS', 'RIBEIRAOPRETO', 'FRANCA', 'SAOJOSEDORIOPRETO', 'BAURU', # São Paulo (próximo a MG)
    # Outros termos comuns
    'MUNICIPIO', 'ESTADO', 'UF', 'BR',
    # Termos que podem ser confundidos com partes da placa mas são contextuais
    'FRENTE', 'TRAS', 'LATERAL', 'AUTO', 'MOTO', 'CAMINHAO', 'CARRO',
 
}

def is_letter_candidate(char_val):
    return char_val in string.ascii_uppercase or char_val in int_to_char

def is_digit_candidate(char_val):
    # Check if it's a digit '0'-'9' or a character that can be mapped to a digit
    return char_val.isdigit() or char_val in char_to_int

def license_complies_format(text):
    if not text or len(text) != 7:
        return None

    # Pattern 1: LLLNNNN (Classic Brazilian)
    if (is_letter_candidate(text[0]) and
        is_letter_candidate(text[1]) and
        is_letter_candidate(text[2]) and
        is_digit_candidate(text[3]) and
        is_digit_candidate(text[4]) and
        is_digit_candidate(text[5]) and
        is_digit_candidate(text[6])):
        return "LLLNNNN"

    # Pattern 2: LLLNLNN (Mercosul Standard - Cars, Motorcycles, etc.)
    if (is_letter_candidate(text[0]) and
        is_letter_candidate(text[1]) and
        is_letter_candidate(text[2]) and
        is_digit_candidate(text[3]) and
        is_letter_candidate(text[4]) and # Letter at index 4
        is_digit_candidate(text[5]) and
        is_digit_candidate(text[6])):
        return "LLLNLNN"
        
    return None

def format_char(char_val, target_type):
    """Corrects a single character to be a letter or digit based on target_type ('L' or 'N')."""
    if target_type == 'L':  # Target is Letter
        if char_val in int_to_char: return int_to_char[char_val]
        if char_val.isalpha() and char_val.upper() in string.ascii_uppercase: return char_val.upper()
        # If it's a digit but should be a letter, and not in int_to_char, it's problematic.
        # For now, return original if no direct mapping.
        return char_val.upper() if char_val.isalpha() else char_val
    elif target_type == 'N':  # Target is Number
        if char_val in char_to_int: return char_to_int[char_val]
        if char_val.isdigit(): return char_val
        # If it's a letter but should be a digit, and not in char_to_int, it's problematic.
        return char_val
    return char_val # Fallback

def corrigir_placa(text, pattern_code):
    if not pattern_code or len(text) != 7:
        return text.upper() # Return uppercase original if no pattern or wrong length

    corrected_plate = list(text) # Start with the original text

    char_type_pattern = ""
    if pattern_code == "LLLNNNN":
        char_type_pattern = "LLLNNNN"
    elif pattern_code == "LLLNLNN":
        char_type_pattern = "LLLNLNN"
    else:
        return text.upper() # Unknown pattern

    for i in range(7):
        corrected_plate[i] = format_char(text[i], char_type_pattern[i])
    
    return "".join(corrected_plate)

buffer_leituras = []
BUFFER_SIZE = 10  # Increased buffer size

def salvar_no_postgres(frame_nmr, car_id, license_number, license_number_score):
    global buffer_leituras, conexao, cursor
    data_hora_atual = datetime.now()
    buffer_leituras.append((int(frame_nmr), int(car_id), license_number, float(license_number_score), data_hora_atual))
    
    if len(buffer_leituras) >= BUFFER_SIZE:
        try:
            comando_sql = """
            INSERT INTO transito_leitura_placa (frame_nmr,car_id,license_number,license_number_score,data_hora)
            VALUES (%s, %s, %s, %s, %s);
            """
            cursor.executemany(comando_sql, buffer_leituras)
            conexao.commit()
            print(f"[DB_INFO] Lote de {len(buffer_leituras)} leituras salvo no banco de dados.")
            buffer_leituras = []
        except psycopg2.Error as e:
            print(f"[DB_ERROR] Erro ao salvar lote no PostgreSQL: {e}")
            conexao.rollback()
            buffer_leituras = [] # Clear buffer on error to avoid retrying bad data or use a dead-letter queue
        except Exception as ex:
            print(f"[DB_ERROR] Erro inesperado ao salvar lote: {ex}")
            conexao.rollback()
            buffer_leituras = []

def flush_buffer_leituras():
    global buffer_leituras, conexao, cursor
    if buffer_leituras:
        try:
            comando_sql = """
            INSERT INTO transito_leitura_placa (frame_nmr,car_id,license_number,license_number_score,data_hora)
            VALUES (%s, %s, %s, %s, %s);
            """
            cursor.executemany(comando_sql, buffer_leituras)
            conexao.commit()
            print(f"[DB_INFO] Buffer final de {len(buffer_leituras)} leituras salvo no banco de dados.")
        except psycopg2.Error as e:
            print(f"[DB_ERROR] Erro ao fazer flush do buffer para o PostgreSQL: {e}")
            conexao.rollback()
        except Exception as ex:
            print(f"[DB_ERROR] Erro inesperado ao fazer flush do buffer: {ex}")
            conexao.rollback()
        buffer_leituras = [] # Always clear after attempting flush

def close_db_connection():
    global conexao, cursor
    print("[INFO] Tentando descarregar buffer e fechar conexão com DB...")
    flush_buffer_leituras()
    if cursor:
        cursor.close()
    if conexao:
        conexao.close()
    print("[DB_INFO] Conexão com PostgreSQL fechada.")

def limpar_texto_placa(texto):
    caracteres_remover = "-.!@#$%^&*()[]{};:,<>?/\\|`~'\""
    return ''.join(c for c in texto if c not in caracteres_remover).strip().upper()

def ler_placas2(placa_carro_crop): # PaddleOCR based
    if len(placa_carro_crop.shape) == 2:
        img_rgb = cv2.cvtColor(placa_carro_crop, cv2.COLOR_GRAY2RGB)
    else:
        img_rgb = cv2.cvtColor(placa_carro_crop, cv2.COLOR_BGR2RGB)

    results = ocr.ocr(img_rgb, cls=False)
    
    if not results or not results[0]:
        # print("[INFO] Nenhum texto detectado pelo OCR (PaddleOCR) ou resultado vazio.")
        return None, None

    all_detections_for_image = results[0]
    
    # Debug: Imprimir resultados brutos do OCR
    # print("Resultados brutos do PaddleOCR:")
    # if all_detections_for_image:
    #     for idx, detection_item in enumerate(all_detections_for_image):
    #         print(f"  Detecção {idx}: Box={detection_item[0]}, Texto='{detection_item[1][0]}', Confiança={detection_item[1][1]:.4f}")

    # Tenta combinar múltiplas detecções
    if all_detections_for_image and len(all_detections_for_image) > 1:
        texts_to_combine = []
        scores_to_combine = []
        
        # Ordenar por posição X (da esquerda para direita) e depois Y (de cima para baixo)
        # Box é [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        # Usar o canto superior esquerdo (x1, y1) para ordenação.
        try:
            sorted_detections = sorted(all_detections_for_image, key=lambda det: (det[0][0][0], det[0][0][1]))
        except TypeError: # Fallback if box structure is unexpected
            print("[WARN] Não foi possível ordenar as detecções do OCR. Usando ordem original.")
            sorted_detections = all_detections_for_image


        for detection_item in sorted_detections:
            text_ocr = detection_item[1][0]
            score_ocr = detection_item[1][1]
            
            processed_text = limpar_texto_placa(text_ocr)

            if processed_text and processed_text not in PALAVRAS_IGNORAR and len(processed_text) > 0: # Adicionado len > 0
                texts_to_combine.append(processed_text)
                scores_to_combine.append(score_ocr)
        
        if texts_to_combine:
            combined_text = "".join(texts_to_combine)
            pattern = license_complies_format(combined_text)
            if pattern:
                avg_score = sum(scores_to_combine) / len(scores_to_combine) if scores_to_combine else 0.0
                corrected_plate = corrigir_placa(combined_text, pattern)
                print(f"[INFO] Placa combinada: {corrected_plate} (de '{combined_text}'), Confiança Média: {avg_score:.2f} de {len(texts_to_combine)} partes.")
                return corrected_plate, avg_score

    # Lógica para detecção única ou fallback
    if all_detections_for_image:
        for detection_item in all_detections_for_image:
            text_ocr = detection_item[1][0]
            score_ocr = detection_item[1][1]

            processed_text = limpar_texto_placa(text_ocr)
            
            pattern = license_complies_format(processed_text)
            if pattern:
                corrected_plate = corrigir_placa(processed_text, pattern)
                print(f"[INFO] Placa individual: {corrected_plate} (de '{processed_text}'), Confiança: {score_ocr:.2f}")
                return corrected_plate, score_ocr

    return None, None
