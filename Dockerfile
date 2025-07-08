# --- ESTÁGIO 1: O Construtor (Builder) ---
# Usamos a imagem "cheia" aqui, que tem ferramentas de compilação, se necessárias
FROM python:3.11-bookworm as builder

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# Cria um ambiente virtual dentro do builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instala as dependências Python no ambiente virtual
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# --- ESTÁGIO 2: A Imagem Final (Final) ---
# Começamos com uma imagem "slim", muito mais leve e segura
FROM python:3.11-slim-bookworm

# Cria um usuário não-root para rodar a aplicação (boa prática de segurança)
RUN useradd --create-home appuser
WORKDIR /home/appuser/app
USER appuser

# Copia apenas o ambiente virtual e o código da aplicação do estágio anterior
COPY --from=builder /opt/venv /opt/venv
COPY . .

# Aponta o PATH para o ambiente virtual
ENV PATH="/opt/venv/bin:$PATH"

# Expõe a porta onde a API vai rodar
EXPOSE 8000

# Comando para iniciar o servidor de API
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]