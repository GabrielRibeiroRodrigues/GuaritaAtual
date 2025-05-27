import string
import re # Importar regex
# import psycopg2 # Comentado pois não estamos usando agora
import cv2
import numpy as np
from paddleocr import PaddleOCR
from datetime import datetime

# ... (conexao e cursor comentados) ...

# Configuração do PaddleOCR
ocr = PaddleOCR(
    lang='pt',
    use_angle_cls=False, 
    use_gpu=False,
    det_limit_side_len=960, # Lado maior da imagem de entrada para detecção será redimensionado para este valor se maior.
    # rec_image_shape="3, 48, 320", # Formato da imagem para o reconhecedor (default é "3, 32, 320")
                                  # Aumentar a altura (e.g. 48) pode ajudar com caracteres mais altos.
    # det_db_thresh=0.3,
    # det_db_box_thresh=0.5, # Reduzir pode ajudar a detectar texto mais difícil, mas aumenta falsos positivos.
    # det_db_unclip_ratio=1.6 # Quanto expandir a caixa detectada.
)

# Dicionários para correção de caracteres
char_to_int = {'O': '0', 'I': '1', 'J': '3', 'A': '4', 'G': '6', 'S': '5', 'B': '8', 'Z': '2', 'Q': '0', 'E': '3', 'T': '7', 'L': '1'}
int_to_char = {'0': 'O', '1': 'I', '3': 'J', '4': 'A', '6': 'G', '5': 'S', '8': 'B', '2': 'Z', '7': 'T'}


def limpar_texto_placa(texto):
    # Remove caracteres não alfanuméricos e converte para maiúsculas
    return ''.join(c for c in texto if c.isalnum()).upper()

def preprocess_for_paddleocr(image_bgr):
    """
    Pré-processa a imagem da placa (BGR) para melhorar o desempenho do PaddleOCR.
    """
    if image_bgr is None or image_bgr.size == 0:
        print("[ERRO] Imagem de entrada para preprocess_for_paddleocr é inválida.")
        return None

    processed_image = image_bgr.copy()
    height, width = processed_image.shape[:2]

    # 1. Redimensionamento (Upscaling) se a imagem for pequena
    min_char_height_approx = 10 # Altura mínima aproximada de um caractere para bom OCR
    # Se a altura da placa for menor que ~3x isso, pode ser útil aumentar.
    # Ex: se placa tem altura 20px, caracteres podem ter ~6px. Aumentar para 60px -> caracteres ~18px.
    target_plate_height = 48 # Altura desejada para a imagem da placa
    
    if height < target_plate_height and height > 0: # Evitar divisão por zero
        scale_factor = target_plate_height / height
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        # INTER_CUBIC é melhor para aumentar, mas mais lento. INTER_LINEAR é um bom compromisso.
        processed_image = cv2.resize(processed_image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

    # 2. Remoção de Ruído
    processed_image = cv2.fastNlMeansDenoisingColored(processed_image, None, h=8, hColor=8, templateWindowSize=7, searchWindowSize=21)

    # 3. Melhoria de Contraste (CLAHE no canal L do espaço de cor LAB)
    try:
        # Verificar se a imagem tem canais suficientes e não é excessivamente pequena para CLAHE
        if len(processed_image.shape) == 3 and processed_image.shape[0] > 1 and processed_image.shape[1] > 1:
            lab = cv2.cvtColor(processed_image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            # tileGridSize menor para imagens menores pode ser melhor.
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4) if min(l.shape) < 50 else (8,8) )
            cl = clahe.apply(l)
            limg = cv2.merge((cl, a, b))
            processed_image = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        # else:
            # print("[AVISO] Imagem pequena ou monocromática, pulando CLAHE.")
    except cv2.error as e:
        print(f"[AVISO] Erro ao aplicar CLAHE: {e}. Usando imagem após denoising.")
        # Continua com a imagem que tinha antes do CLAHE.

    return processed_image


def validar_e_formatar_placa(texto_ocr):
    """
    Valida e formata o texto da placa OCR para os padrões brasileiros (antigo e Mercosul).
    Aplica correções de caracteres comuns.
    Retorna a placa formatada e validada, ou None.
    """
    texto_limpo = limpar_texto_placa(texto_ocr) 

    if len(texto_limpo) != 7:
        return None

    regex_antigo_final = r"^[A-Z]{3}[0-9]{4}$"
    regex_mercosul_final = r"^[A-Z]{3}[0-9][A-Z][0-9]{2}$"

    def aplicar_correcoes_posicionais(texto_entrada, posicoes_letras, posicoes_numeros):
        corrigido_lista = list(texto_entrada)
        valido = True
        for i in range(7):
            char_atual = corrigido_lista[i]
            if i in posicoes_letras:
                if char_atual in int_to_char:
                    corrigido_lista[i] = int_to_char[char_atual]
                elif not corrigido_lista[i].isalpha(): # Após tentativa de correção, deve ser letra
                    valido = False; break
            elif i in posicoes_numeros:
                if char_atual in char_to_int:
                    corrigido_lista[i] = char_to_int[char_atual]
                elif not corrigido_lista[i].isdigit(): # Após tentativa de correção, deve ser dígito
                    valido = False; break
            else: # Posição não coberta (não deve acontecer para len 7)
                valido = False; break
        
        return "".join(corrigido_lista) if valido else None

    # Tentativa 1: Formato Antigo (LLLNNNN)
    pos_letras_antigo = [0, 1, 2]
    pos_numeros_antigo = [3, 4, 5, 6]
    texto_corrigido_antigo = aplicar_correcoes_posicionais(texto_limpo, pos_letras_antigo, pos_numeros_antigo)
    if texto_corrigido_antigo and re.fullmatch(regex_antigo_final, texto_corrigido_antigo):
        return texto_corrigido_antigo

    # Tentativa 2: Formato Mercosul (LLLNLNN)
    pos_letras_mercosul = [0, 1, 2, 4]
    pos_numeros_mercosul = [3, 5, 6]
    texto_corrigido_mercosul = aplicar_correcoes_posicionais(texto_limpo, pos_letras_mercosul, pos_numeros_mercosul)
    if texto_corrigido_mercosul and re.fullmatch(regex_mercosul_final, texto_corrigido_mercosul):
        return texto_corrigido_mercosul
        
    return None


def ler_placas2(placa_carro_crop_bgr):
    """
    Recebe um recorte de placa (imagem BGR), pré-processa, e usa PaddleOCR para ler o texto.
    Valida e formata o texto da placa.
    """
    if placa_carro_crop_bgr is None or placa_carro_crop_bgr.size == 0:
        # print("[ERRO] Imagem de entrada para ler_placas2 é inválida.")
        return None, None

    img_para_ocr_bgr = preprocess_for_paddleocr(placa_carro_crop_bgr)
    
    if img_para_ocr_bgr is None:
        # print("[AVISO] Pré-processamento retornou None, tentando OCR na imagem original.")
        img_para_ocr_bgr = placa_carro_crop_bgr

    try:
        img_rgb = cv2.cvtColor(img_para_ocr_bgr, cv2.COLOR_BGR2RGB)
    except cv2.error as e:
        # print(f"[ERRO] Falha ao converter imagem para RGB: {e}. Abortando OCR.")
        return None, None

    results = ocr.ocr(img_rgb) 
    
    if not results or not results[0]:
        return None, None

    best_score = 0.0
    best_plate = None

    # results[0] contém a lista de [box, (text, score)] para a imagem
    for detection_info in results[0]: 
        # detection_info é [box, (text, score)]
        text_ocr = detection_info[1][0]
        score_ocr = detection_info[1][1]
        
        placa_formatada = validar_e_formatar_placa(text_ocr)
        
        if placa_formatada:
            if score_ocr > best_score:
                best_score = score_ocr
                best_plate = placa_formatada
    
    if best_plate:
        return best_plate, best_score

    return None, None

