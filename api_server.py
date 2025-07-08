# api_server.py (versão final de teste, sem logger customizado e sem DB)

import sys
import os

# Adiciona o diretório atual ao path do Python para encontrar o 'util_debian'
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
import cv2
import numpy as np
import io

# Importamos apenas a função de OCR do nosso utilitário
from util_debian import ler_placas2


# --- Criação da Aplicação FastAPI ---
app = FastAPI(
    title="API de OCR de Placas (Modo Teste)",
    version="1.4.0",
    description="Serviço para reconhecimento de placas, sem dependências externas.",
)

# --- Nossa função de processamento pesado ---
def tarefa_de_ocr(imagem_bytes: bytes, nome_arquivo: str):
    """Esta função será executada em segundo plano."""
    try:
        print(f"[INFO] Iniciando processamento em background para: {nome_arquivo}")
        nparr = np.frombuffer(imagem_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

        if img is None:
            print(f"[ERRO] Falha ao decodificar imagem na tarefa de fundo: {nome_arquivo}")
            return

        texto, confianca = ler_placas2(img)
        if texto and confianca:
            # Imprimimos o resultado diretamente no log do contêiner
            print("--- RESULTADO DO OCR ---")
            print(f"Placa Lida: {texto}")
            print(f"Confiança: {confianca:.4f}")
            print("------------------------")
        else:
            print(f"[INFO] OCR não encontrou placa com confiança suficiente para o arquivo: {nome_arquivo}")

    except Exception as e:
        print(f"[ERRO] Erro inesperado na tarefa de background para {nome_arquivo}: {e}")


# --- Endpoint Principal da API ---
@app.post("/processar_imagem/")
async def processar_imagem_endpoint(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Recebe uma imagem, responde imediatamente e agenda o processamento de OCR.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo inválido. Apenas imagens são aceitas.")

    contents = await file.read()
    background_tasks.add_task(tarefa_de_ocr, contents, file.filename)

    return {"message": "Imagem recebida e agendada para processamento."}

# --- Endpoint de verificação de saúde (Health Check) ---
@app.get("/health")
def health_check():
    return {"status": "ok"}