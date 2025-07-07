# Passo 1: Imagem Base
# Começamos com uma imagem oficial do Python 3.11, baseada em Debian (bookworm).
# A tag "slim" significa que é uma versão mais leve, economizando espaço.
FROM python:3.11-slim-bookworm

# Passo 2: Diretório de Trabalho
# Criamos uma pasta /app dentro do contêiner e a definimos como nosso diretório padrão.
WORKDIR /app

# Passo 3: Instalar Dependências
# Copiamos apenas o requirements.txt primeiro. Isso otimiza o cache do Docker.
COPY requirements.txt .

# Executamos o pip para instalar tudo da lista.
# O --no-cache-dir ajuda a manter a imagem final um pouco menor.
RUN pip install --no-cache-dir -r requirements.txt

# Passo 4: Copiar o Código da Aplicação
# Agora, copiamos todos os outros arquivos do seu projeto para dentro da pasta /app no contêiner.
COPY . .

# Passo 5: Comando de Execução
# Definimos o comando que será executado automaticamente quando o contêiner iniciar.
CMD ["python", "leitor_placas_debian.py"]