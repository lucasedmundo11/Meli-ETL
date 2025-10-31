#!/bin/bash

# ================================
# DESENVOLVIMENTO E MANUTENÇÃO
# Pipeline ETL Mercado Libre
# ================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Setup development environment
setup_dev() {
    log_info "Configurando ambiente de desenvolvimento..."
    
    # Check Python version
    if ! command_exists python3; then
        log_error "Python 3 não encontrado. Instale Python 3.11+"
        exit 1
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "env" ]; then
        log_info "Criando ambiente virtual..."
        python3 -m venv env
    fi
    
    # Activate virtual environment
    log_info "Ativando ambiente virtual..."
    source env/bin/activate
    
    # Upgrade pip
    log_info "Atualizando pip..."
    pip install --upgrade pip
    
    # Install dependencies
    log_info "Instalando dependências..."
    pip install -r requirements.txt
    
    # Install development dependencies
    log_info "Instalando dependências de desenvolvimento..."
    pip install black flake8 pytest pytest-cov mypy
    
    # Copy environment template
    if [ ! -f ".env" ]; then
        log_info "Criando arquivo .env a partir do template..."
        cp .env.example .env
        log_warning "Configure as variáveis de ambiente no arquivo .env"
    fi
    
    log_success "Ambiente de desenvolvimento configurado!"
}

# Format code
format_code() {
    log_info "Formatando código com Black..."
    black src/ --line-length 88
    log_success "Código formatado!"
}

# Lint code
lint_code() {
    log_info "Verificando estilo do código com Flake8..."
    flake8 src/ --max-line-length=88 --ignore=E203,W503
    log_success "Verificação de estilo concluída!"
}

# Type check
type_check() {
    log_info "Verificando tipos com MyPy..."
    mypy src/ --ignore-missing-imports
    log_success "Verificação de tipos concluída!"
}

# Run tests
run_tests() {
    log_info "Executando testes..."
    if [ -d "tests" ]; then
        pytest tests/ -v --cov=src/ --cov-report=html --cov-report=term
        log_success "Testes executados!"
    else
        log_warning "Diretório 'tests' não encontrado. Criando estrutura básica..."
        mkdir -p tests
        touch tests/__init__.py
        touch tests/test_pipeline.py
        log_info "Estrutura de testes criada. Adicione seus testes em tests/"
    fi
}

# Check all (format, lint, type check, test)
check_all() {
    log_info "Executando todas as verificações..."
    format_code
    lint_code
    type_check
    run_tests
    log_success "Todas as verificações concluídas!"
}

# Build Docker image
build_docker() {
    log_info "Construindo imagem Docker..."
    docker build -t meli-etl-pipeline:latest .
    log_success "Imagem Docker construída!"
}

# Run with Docker Compose
run_docker() {
    log_info "Executando com Docker Compose..."
    if [ ! -f ".env" ]; then
        log_error "Arquivo .env não encontrado. Execute 'setup_dev' primeiro."
        exit 1
    fi
    docker-compose up --build
}

# Clean up
cleanup() {
    log_info "Limpando arquivos temporários..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    find . -type f -name "*.log" -delete 2>/dev/null || true
    rm -rf .pytest_cache/ .coverage htmlcov/ .mypy_cache/ 2>/dev/null || true
    log_success "Limpeza concluída!"
}

# Check BigQuery connection
check_bigquery() {
    log_info "Verificando conexão com BigQuery..."
    
    if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        log_error "GOOGLE_APPLICATION_CREDENTIALS não definido"
        exit 1
    fi
    
    if [ -z "$GCP_PROJECT_ID" ]; then
        log_error "GCP_PROJECT_ID não definido"
        exit 1
    fi
    
    # Test BigQuery connection
    python3 -c "
from google.cloud import bigquery
import os

try:
    client = bigquery.Client(project=os.getenv('GCP_PROJECT_ID'))
    datasets = list(client.list_datasets())
    print(f'✅ Conexão com BigQuery estabelecida. Encontrados {len(datasets)} datasets.')
except Exception as e:
    print(f'❌ Erro na conexão com BigQuery: {e}')
    exit(1)
"
    log_success "Conexão com BigQuery verificada!"
}

# Deploy to production (placeholder)
deploy() {
    log_warning "Deploy para produção ainda não implementado."
    log_info "Considere usar Google Cloud Run, Kubernetes ou similar."
}

# Show help
show_help() {
    echo "Pipeline ETL Mercado Libre - Scripts de Desenvolvimento"
    echo ""
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandos disponíveis:"
    echo "  setup_dev     - Configura ambiente de desenvolvimento"
    echo "  format        - Formata código com Black"
    echo "  lint          - Verifica estilo com Flake8"
    echo "  typecheck     - Verifica tipos com MyPy"
    echo "  test          - Executa testes"
    echo "  check         - Executa todas as verificações"
    echo "  build         - Constrói imagem Docker"
    echo "  run           - Executa com Docker Compose"
    echo "  cleanup       - Remove arquivos temporários"
    echo "  check-bq      - Verifica conexão com BigQuery"
    echo "  deploy        - Deploy para produção (TODO)"
    echo "  help          - Mostra esta ajuda"
    echo ""
}

# Main script logic
case "$1" in
    setup_dev|setup)
        setup_dev
        ;;
    format)
        format_code
        ;;
    lint)
        lint_code
        ;;
    typecheck|type)
        type_check
        ;;
    test)
        run_tests
        ;;
    check|check_all)
        check_all
        ;;
    build)
        build_docker
        ;;
    run)
        run_docker
        ;;
    cleanup|clean)
        cleanup
        ;;
    check-bq|bigquery)
        check_bigquery
        ;;
    deploy)
        deploy
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Comando inválido: '$1'"
        echo ""
        show_help
        exit 1
        ;;
esac