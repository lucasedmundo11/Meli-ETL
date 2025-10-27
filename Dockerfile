FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (para cache de layers)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fonte
COPY src/ ./src/
COPY config/ ./config/

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Variáveis de ambiente
ENV PYTHONPATH=/app/src
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/config/service-account.json

# Comando padrão
CMD ["python", "src/main.py"]

# Labels para metadata
LABEL maintainer="seu-email@exemplo.com"
LABEL version="1.0.0"
LABEL description="Pipeline ETL Mercado Libre - Samsung Galaxy S25"