#!/bin/bash

# Script de deploy para Google Cloud Run

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"seu-projeto-gcp"}
SERVICE_NAME="meli-etl-pipeline"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Iniciando deploy do pipeline ETL..."

# Build da imagem
echo "📦 Fazendo build da imagem Docker..."
docker build -t $IMAGE_NAME .

# Push para Google Container Registry
echo "⬆️ Fazendo push da imagem..."
docker push $IMAGE_NAME

# Deploy no Cloud Run
echo "🌐 Fazendo deploy no Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID \
  --memory 1Gi \
  --timeout 3600 \
  --concurrency 1

echo "✅ Deploy concluído com sucesso!"