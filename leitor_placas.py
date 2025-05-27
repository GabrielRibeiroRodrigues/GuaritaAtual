import os
import cv2
import time
import gc
from util import ler_placas2
 # ,salvar_no_postgres  # Importa salvar_no_postgres

pasta_base = os.path.join(os.path.expanduser("~"), "Desktop", "placas_detectadas")
confianca_gravar_texto = 0.1

def processar_imagem(caminho_arquivo):
    nome = os.path.basename(caminho_arquivo)
    frame_nmr = -1
    car_id_display = "unknown"
    try:
        partes = nome.split('_')
        if len(partes) >= 4: # Ex: frame_0_car_placa_timestamp_ang0.png
            frame_nmr_str = partes[1]
            car_id_part = partes[3]
            
            frame_nmr = int(frame_nmr_str)
            
            try:
                car_id_int = int(car_id_part) 
                car_id_display = str(car_id_int)
            except ValueError:
                car_id_display = car_id_part # Mantém como string (ex: "placa")
        else:
            # print(f"[AVISO] Nome do arquivo {nome} não está no formato esperado.")
            pass # Mantém frame_nmr e car_id_display com valores padrão
            
    except Exception as e:
        # print(f"[DEBUG] Erro ao analisar o nome do arquivo {nome}: {e}") # Comentado para reduzir logs
        frame_nmr = -1 # Redefine em caso de erro parcial
        car_id_display = "unknown" # Redefine em caso de erro parcial

    # Ler a imagem em cores (BGR)
    img = cv2.imread(caminho_arquivo, cv2.IMREAD_COLOR)
    if img is None:
        print(f"[ERRO] Não foi possível ler a imagem {caminho_arquivo}")
        try:
            os.remove(caminho_arquivo)
            # print(f"[INFO] Arquivo {caminho_arquivo} removido após falha na leitura.")
        except Exception as e_rem:
            print(f"[ERRO] Não foi possível remover o arquivo {caminho_arquivo} após falha na leitura: {e_rem}")
        return

    texto_detectado, confianca_texto_detectado = ler_placas2(img)

    del img

    if texto_detectado is not None and confianca_texto_detectado is not None and confianca_texto_detectada > confianca_gravar_texto:
        print(f"[INFO] Arquivo: {nome}, Frame: {frame_nmr}, ID: {car_id_display}, Texto: {texto_detectado}, Confiança: {confianca_texto_detectado:.4f}")
        # Salva no PostgreSQL
        # salvar_no_postgres(frame_nmr, car_id_display, texto_detectado, confianca_texto_detectado) # car_id_display pode ser string
    # else:
        # print(f"[DEBUG] Placa não reconhecida ou confiança baixa para {nome}. Texto: {texto_detectado}, Confiança: {confianca_texto_detectado}")


    try:
        os.remove(caminho_arquivo)
    except Exception as e:
        print(f"[ERRO] Não foi possível remover o arquivo {caminho_arquivo}: {e}")

    gc.collect()

def main():
    arquivos_ignorados = {'.tmp', '.part'}
    while True:
        encontrou = False
        for data_dir in sorted(os.listdir(pasta_base)):
            pasta_data = os.path.join(pasta_base, data_dir)
            if not os.path.isdir(pasta_data):
                continue
            arquivos = sorted(os.listdir(pasta_data), key=lambda x: os.path.getmtime(os.path.join(pasta_data, x)))
            for nome_arquivo in arquivos:
                if any(nome_arquivo.endswith(ext) for ext in arquivos_ignorados) or nome_arquivo.startswith('~'):
                    continue
                caminho_arquivo = os.path.join(pasta_data, nome_arquivo)
                processar_imagem(caminho_arquivo)
                encontrou = True
        if not encontrou:
            time.sleep(10)

if __name__ == "__main__":
    main()
