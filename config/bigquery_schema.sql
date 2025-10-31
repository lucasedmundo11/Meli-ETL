-- Schema atualizado para a tabela products_samsung_s25 (Apify output)
CREATE TABLE IF NOT EXISTS `seu-projeto-gcp.mercado_libre.products_samsung_s25` (
  product_id STRING NOT NULL,
  title STRING,
  subtitle STRING,
  originalPrice STRING,
  price FLOAT64,
  price_string STRING,
  alternativePrice STRING,
  rating FLOAT64,
  reviews INT64,
  condition STRING,
  seller STRING,
  description STRING,
  images ARRAY<STRING>,
  sellCount INT64,
  url STRING,
  currency STRING,
  extraction_date TIMESTAMP NOT NULL,
  JOB_RUN TIMESTAMP NOT NULL
)
PARTITION BY DATE(JOB_RUN)
CLUSTER BY seller, condition, currency;