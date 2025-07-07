import string
import psycopg2
import cv2
import numpy as np
from paddleocr import PaddleOCR
from datetime import datetime
import os
import sys

# Configuração específica para ambiente Debian/Linux
# Otimizações para melhor performance em servidores Linux
ocr = PaddleOCR(
    lang='pt',
    use_angle_cls=False,
    det_limit_side_len=640,
    # Configurações específicas para Linux
    use_gpu=False,  # Pode ser True se CUDA estiver disponível
    show_log=False,  # Reduz logs verbosos
    enable_mkldnn=True  # Otimização Intel MKL-DNN para CPU
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

# Configuração de banco de dados para ambiente Linux/Debian
def get_db_config():
    """
    Obtém configuração de banco de dados via variáveis de ambiente
    ou arquivo de configuração específico para Linux.
    """
    # Configuração via variáveis de ambiente (recomendado para produção)
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'guarita'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
    }
    
    # Arquivo de configuração alternativo (se não houver variáveis de ambiente)
    config_file = os.path.expanduser('~/.config/guarita/db_config')
    if not any(db_config.values()) and os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        if key.upper() in ['HOST', 'PORT', 'DATABASE', 'USER', 'PASSWORD']:
                            db_config[key.lower()] = value
        except Exception as e:
            print(f"[WARN] Erro ao ler arquivo de configuração {config_file}: {e}")
    
    return db_config

# Inicialização das variáveis globais
conexao = None
cursor = None
buffer_leituras = []
BUFFER_SIZE = 10  # Increased buffer size

def init_db_connection():
    """
    Inicializa a conexão com o banco de dados PostgreSQL.
    Adaptado para ambiente Linux com melhor tratamento de erro.
    """
    global conexao, cursor
    
    if conexao is not None:
        return True  # Já conectado
    
    try:
        db_config = get_db_config()
        print(f"[DB_INFO] Conectando ao PostgreSQL em {db_config['host']}:{db_config['port']}")
        
        conexao = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            # Configurações específicas para Linux
            connect_timeout=30,
            application_name='guarita_leitor_placas_debian'
        )
        
        cursor = conexao.cursor()
        
        # Teste de conectividade
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"[DB_INFO] Conectado ao PostgreSQL: {version[0]}")
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"[DB_ERROR] Erro de conectividade PostgreSQL: {e}")
        print("[DB_INFO] Verifique se o PostgreSQL está rodando e as credenciais estão corretas")
        return False
    except Exception as e:
        print(f"[DB_ERROR] Erro inesperado ao conectar ao PostgreSQL: {e}")
        return False

def salvar_no_postgres(frame_nmr, car_id, license_number, license_number_score):
    global buffer_leituras, conexao, cursor
    
    # Inicializa conexão se necessário
    if not conexao or conexao.closed:
        if not init_db_connection():
            print("[DB_ERROR] Não foi possível conectar ao banco. Dados não salvos.")
            return
    
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
            # Tenta reconectar em caso de erro de conexão
            if "connection" in str(e).lower():
                print("[DB_INFO] Tentando reconectar ao banco...")
                init_db_connection()
            conexao.rollback() if conexao and not conexao.closed else None
            buffer_leituras = [] # Clear buffer on error to avoid retrying bad data
        except Exception as ex:
            print(f"[DB_ERROR] Erro inesperado ao salvar lote: {ex}")
            conexao.rollback() if conexao and not conexao.closed else None
            buffer_leituras = []

def flush_buffer_leituras():
    global buffer_leituras, conexao, cursor
    
    if not buffer_leituras:
        return
    
    # Inicializa conexão se necessário
    if not conexao or conexao.closed:
        if not init_db_connection():
            print("[DB_ERROR] Não foi possível conectar ao banco para flush. Dados perdidos.")
            buffer_leituras = []
            return
    
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
        conexao.rollback() if conexao and not conexao.closed else None
    except Exception as ex:
        print(f"[DB_ERROR] Erro inesperado ao fazer flush do buffer: {ex}")
        conexao.rollback() if conexao and not conexao.closed else None
    finally:
        buffer_leituras = [] # Always clear after attempting flush

def close_db_connection():
    global conexao, cursor
    print("[INFO] Tentando descarregar buffer e fechar conexão com DB...")
    flush_buffer_leituras()
    
    try:
        if cursor:
            cursor.close()
        if conexao and not conexao.closed:
            conexao.close()
        print("[DB_INFO] Conexão com PostgreSQL fechada.")
    except Exception as e:
        print(f"[DB_WARN] Erro ao fechar conexão: {e}")

def limpar_texto_placa(texto):
    """
    Remove caracteres especiais e normaliza texto da placa.
    Versão otimizada para Linux.
    """
    caracteres_remover = "-.!@#$%^&*()[]{};:,<>?/\\|`~'\""
    return ''.join(c for c in texto if c not in caracteres_remover).strip().upper()

def ler_placas2(placa_carro_crop): # PaddleOCR based - Versão Debian
    """
    Função de leitura de placas otimizada para ambiente Linux/Debian.
    """
    try:
        if len(placa_carro_crop.shape) == 2:
            img_rgb = cv2.cvtColor(placa_carro_crop, cv2.COLOR_GRAY2RGB)
        else:
            img_rgb = cv2.cvtColor(placa_carro_crop, cv2.COLOR_BGR2RGB)

        # Preprocessamento adicional para melhor OCR em Linux
        # Normalização de contraste
        img_rgb = cv2.convertScaleAbs(img_rgb, alpha=1.2, beta=10)

        results = ocr.ocr(img_rgb, cls=False)
        
        if not results or not results[0]:
            # print("[INFO] Nenhum texto detectado pelo OCR (PaddleOCR) ou resultado vazio.")
            return None, None

        all_detections_for_image = results[0]
        
        # Tenta combinar múltiplas detecções
        if all_detections_for_image and len(all_detections_for_image) > 1:
            texts_to_combine = []
            scores_to_combine = []
            
            # Ordenar por posição X (da esquerda para direita) e depois Y (de cima para baixo)
            try:
                sorted_detections = sorted(all_detections_for_image, key=lambda det: (det[0][0][0], det[0][0][1]))
            except (TypeError, IndexError) as e: # Melhor tratamento de erro para Linux
                print(f"[WARN] Não foi possível ordenar as detecções do OCR: {e}. Usando ordem original.")
                sorted_detections = all_detections_for_image

            for detection_item in sorted_detections:
                text_ocr = detection_item[1][0]
                score_ocr = detection_item[1][1]
                
                processed_text = limpar_texto_placa(text_ocr)

                if processed_text and processed_text not in PALAVRAS_IGNORAR and len(processed_text) > 0:
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
        
    except Exception as e:
        print(f"[ERRO] Erro no processamento OCR: {e}")
        return None, None

# Inicialização automática da conexão ao importar o módulo (Linux style)
def __init_module():
    """
    Inicialização do módulo para ambiente Linux.
    """
    try:
        # Tenta inicializar a conexão com banco na importação
        if not init_db_connection():
            print("[DB_WARN] Banco de dados não disponível no momento da importação.")
            print("[DB_INFO] A conexão será tentada novamente durante o uso.")
    except Exception as e:
        print(f"[DB_WARN] Erro na inicialização do módulo: {e}")

# Chama inicialização quando módulo é importado
__init_module()
