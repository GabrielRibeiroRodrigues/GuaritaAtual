# api_server.py
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
import cv2
import numpy as np
import io

# Assumindo que suas funções de utilitários e logging estão prontas
from util_debian import (
    ler_placas2, 
    salvar_no_postgres, 
    init_connection_pool, 
    close_db_connection
)
from logger_utils import logger

# --- Gerenciamento do Ciclo de Vida (Lifespan) ---
# Esta é a forma moderna de lidar com inicialização e finalização no FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API iniciando: Inicializando pool de conexões com o DB.")
    init_connection_pool()
    yield
    logger.info("API desligando: Fechando pool de conexões.")
    close_db_connection()

app = FastAPI(
    title="Serviço de OCR de Placas",
    version="1.1.0",
    description="Um serviço otimizado para reconhecimento de placas de veículos.",
    lifespan=lifespan
)

# --- Função da Tarefa em Segundo Plano ---
def tarefa_ocr_e_db(imagem_bytes: bytes, nome_arquivo: str):
    """
    Função robusta que executa o trabalho pesado em background para não bloquear a API.
    """
    try:
        logger.info(f"Iniciando processamento em background para: {nome_arquivo}")
        nparr = np.frombuffer(imagem_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

        if img is None:
            logger.error(f"Falha ao decodificar imagem na tarefa de fundo: {nome_arquivo}")
            return

        texto, confianca = ler_placas2(img)
        if texto and confianca:
            salvar_no_postgres(frame_nmr=-1, car_id=-1, plate=texto, confidence=confianca)
            logger.info(f"Processamento em background concluído para: {nome_arquivo}, Placa: {texto}")
    except Exception as e:
        logger.error(f"Erro na tarefa de background para {nome_arquivo}", error=str(e), exc_info=True)


# --- Endpoint Principal da API ---
@app.post("/processar_imagem/")
async def processar_imagem_endpoint(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Recebe uma imagem, responde imediatamente e agenda o processamento em background.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo inválido. Apenas imagens são aceitas.")

    contents = await file.read()
    
    # Adiciona a tarefa pesada para ser executada em segundo plano
    background_tasks.add_task(tarefa_ocr_e_db, contents, file.filename)

    # Retorna uma resposta imediata e leve
    return {"message": "Imagem recebida e agendada para processamento."}

# --- Endpoint de Verificação de Saúde (Health Check) ---
@app.get("/health")
def health_check():
    """Endpoint simples para monitoramento, verifica se a API está online."""
    return {"status": "ok"}