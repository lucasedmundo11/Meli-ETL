# Pipeline ETL Mercado Libre - Samsung Galaxy S25

Este projeto implementa um pipeline ETL completo para extrair dados do produto Samsung Galaxy S25 do Mercado Libre Argentina e carregar no Google BigQuery.

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Mercado Libre  │───▶│   ETL Pipeline   │───▶│   BigQuery      │
│     API         │    │                 │    │   Analytics     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Funcionalidades

- ✅ Extração de dados da API do Mercado Libre Argentina
- ✅ Transformação e limpeza de dados
- ✅ Carga otimizada no BigQuery
- ✅ Logs estruturados e monitoramento
- ✅ Containerização com Docker
- ✅ Configuração via variáveis de ambiente
- ✅ Tratamento robusto de erros
- ✅ Schema otimizado com particionamento

## 📋 Pré-requisitos

- Python 3.11+
- Conta Google Cloud Platform
- Projeto GCP com BigQuery habilitado
- Service Account com permissões no BigQuery
- Docker (opcional)

## 🛠️ Configuração

### 1. Clone o repositório
```bash
git clone <repository-url>
cd meli-etl-pipeline
```

### 2. Instale dependências
```bash
pip install -r requirements.txt
```

### 3. Configure credenciais GCP
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
export GCP_PROJECT_ID="seu-projeto-gcp"
export BQ_DATASET_ID="mercado_libre"
export BQ_TABLE_ID="products_samsung_s25"
```

### 4. Execute o pipeline
```bash
python src/main.py
```

## 🐳 Execução com Docker

### Build da imagem
```bash
docker build -t meli-etl-pipeline .
```

### Execução
```bash
docker run \
  -e GCP_PROJECT_ID="seu-projeto-gcp" \
  -e BQ_DATASET_ID="mercado_libre" \
  -e BQ_TABLE_ID="products_samsung_s25" \
  -v /path/to/service-account.json:/app/config/service-account.json \
  meli-etl-pipeline
```

## 📊 Schema de Dados

A tabela do BigQuery contém os seguintes campos:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| product_id | STRING | ID único do produto |
| title | STRING | Título do produto |
| price | FLOAT64 | Preço do produto |
| currency_id | STRING | Moeda (ARS) |
| condition | STRING | Condição (new, used) |
| seller_id | STRING | ID do vendedor |
| brand | STRING | Marca do produto |
| model | STRING | Modelo do produto |
| extraction_date | TIMESTAMP | Data de extração |

## 📈 Consultas de Exemplo

### Preço médio por condição
```sql
SELECT 
  condition,
  AVG(price) as avg_price,
  COUNT(*) as product_count
FROM `seu-projeto-gcp.mercado_libre.products_samsung_s25`
GROUP BY condition
ORDER BY avg_price DESC;
```

### Top vendedores
```sql
SELECT 
  seller_nickname,
  COUNT(*) as product_count,
  AVG(price) as avg_price
FROM `seu-projeto-gcp.mercado_libre.products_samsung_s25`
WHERE seller_nickname IS NOT NULL
GROUP BY seller_nickname
ORDER BY product_count DESC
LIMIT 10;
```

## 🔧 Desenvolvimento

### Estrutura do projeto
```
├── src/
│   ├── extractors/          # Módulos de extração
│   ├── transformers/        # Módulos de transformação
│   ├── loaders/            # Módulos de carga
│   └── main.py             # Pipeline principal
├── config/
│   ├── config.yaml         # Configurações
│   └── bigquery_schema.sql # Schema do BigQuery
├── requirements.txt        # Dependências
├── Dockerfile             # Container
└── README.md              # Documentação
```

### Executar testes
```bash
pytest tests/ -v --cov=src/
```

### Formatação de código
```bash
black src/
flake8 src/
```

## 📝 Logs

Os logs são salvos em `etl_pipeline.log` e incluem:
- Timestamps de execução
- Métricas de performance
- Erros e exceções
- Contadores de registros processados

## 🚨 Monitoramento

### Métricas coletadas:
- Produtos extraídos
- Produtos transformados
- Produtos carregados
- Tempo de execução
- Taxa de sucesso

## 🔐 Segurança

- Service Account com permissões mínimas necessárias
- Credenciais não commitadas no código
- Logs sem informações sensíveis
- Validação de entrada de dados

## 🐛 Troubleshooting

### Erro de autenticação
```bash
# Verificar credenciais
gcloud auth application-default login
```

### Erro de quota BigQuery
- Verificar limites de quota no GCP Console
- Implementar retry com backoff exponencial

### Timeout na API MeLi
- Ajustar timeouts no código
- Implementar rate limiting

## 🤝 Contribuição

1. Fork do projeto
2. Criar branch para feature (`git checkout -b feature/nova-feature`)
3. Commit das mudanças (`git commit -am 'Add nova feature'`)
4. Push para branch (`git push origin feature/nova-feature`)
5. Criar Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👥 Autores

- Seu Nome - [seu-email@exemplo.com](mailto:seu-email@exemplo.com)

## 📚 Referências

- [API Mercado Libre](https://developers.mercadolibre.com/)
- [Google Cloud BigQuery](https://cloud.google.com/bigquery/docs)
- [Docker Best Practices](https://docs.docker.com/develop/best-practices/)