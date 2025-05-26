import os
import cv2
import time
import gc
from util import ler_placas2, salvar_no_postgres  # Importa salvar_no_postgres

pasta_base = os.path.join(os.path.expanduser("~"), "Desktop", "placas_detectadas")
confianca_gravar_texto = 0.1

def processar_imagem(caminho_arquivo):
    nome = os.path.basename(caminho_arquivo)
    try:
        partes = nome.split('_')
        frame_nmr = int(partes[1])
        car_id_str = partes[3]
        if '.' in car_id_str:
            car_id = int(float(car_id_str))
        else:
            car_id = int(car_id_str)
    except Exception:
        frame_nmr = -1
        car_id = -1

    img = cv2.imread(caminho_arquivo, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return

    texto_detectado, confianca_texto_detectado = ler_placas2(img)

    # Libera a imagem da memória explicitamente
    del img

    if texto_detectado is not None and confianca_texto_detectado > confianca_gravar_texto:
        print(f"[INFO] Frame: {frame_nmr}, Carro ID: {car_id}, Texto: {texto_detectado}, Confiança: {confianca_texto_detectado:.2f}")
        # Salva no PostgreSQL
        salvar_no_postgres(frame_nmr, car_id, texto_detectado, confianca_texto_detectado)
    
    # Remove o arquivo após o processamento
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
