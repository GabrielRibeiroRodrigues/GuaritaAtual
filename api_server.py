# api_server.py (versão de teste, sem banco de dados)

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
# from contextlib import asynccontextmanager # Não precisamos mais disso por enquanto
import cv2
import numpy as np
import io

# Importamos apenas a função de OCR do nosso utilitário
from util_debian import ler_placas2
from logger_utils import logger

# --- Lógica de Ciclo de Vida foi REMOVIDA, pois era para o DB ---
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     ...

# --- Criação da Aplicação FastAPI (sem o lifespan) ---
app = FastAPI(
    title="API de OCR de Placas (Modo Teste)",
    version="1.2.0",
    description="Serviço para reconhecimento de placas, sem conexão com DB.",
)

# --- Nossa função de processamento pesado ---
def tarefa_de_ocr(imagem_bytes: bytes, nome_arquivo: str):
    """Esta função será executada em segundo plano."""
    try:
        logger.info(f"Iniciando processamento em background para: {nome_arquivo}")
        nparr = np.frombuffer(imagem_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

        if img is None:
            logger.error(f"Falha ao decodificar imagem na tarefa de fundo: {nome_arquivo}")
            return

        texto, confianca = ler_placas2(img)
        if texto and confianca:
            # Em vez de salvar no banco, vamos apenas imprimir no log!
            print("--- RESULTADO DO OCR ---")
            print(f"Placa Lida: {texto}")
            print(f"Confiança: {confianca:.4f}")
            print("------------------------")
            logger.info(f"Processamento em background concluído para: {nome_arquivo}, Placa: {texto}")
        else:
            logger.info("OCR em segundo plano não encontrou placa com confiança suficiente.")

    except Exception as e:
        logger.error(f"Erro na tarefa de background para {nome_arquivo}", error=str(e), exc_info=True)


# --- Endpoint Principal da API Modificado ---
@app.post("/processar_imagem/")
async def processar_imagem_endpoint(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Recebe uma imagem, responde imediatamente e agenda o processamento de OCR.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo inválido. Apenas imagens são aceitas.")

    contents = await file.read()
    background_tasks.add_task(tarefa_ocr, contents, file.filename)

    return {"message": "Imagem recebida e agendada para processamento (sem gravação no DB)."}

# --- Endpoint de verificação de saúde (Health Check) ---
@app.get("/health")
def health_check():
    return {"status": "ok"}