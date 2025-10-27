-- Schema para a tabela de produtos do Mercado Libre
CREATE TABLE IF NOT EXISTS `seu-projeto-gcp.mercado_libre.products_samsung_s25` (
  product_id STRING NOT NULL,
  title STRING,
  price FLOAT64,
  currency_id STRING,
  condition STRING,
  category_id STRING,
  thumbnail_url STRING,
  permalink STRING,
  
  -- Seller information
  seller_id STRING,
  seller_nickname STRING,
  seller_reputation JSON,
  seller_power_seller_status STRING,
  
  -- Location
  city STRING,
  state STRING,
  
  -- Product details
  attributes JSON,
  pictures JSON,
  warranty STRING,
  
  -- Technical specifications
  brand STRING,
  model STRING,
  memory STRING,
  color STRING,
  
  -- Metadata
  extraction_date TIMESTAMP NOT NULL,
  JOB_RUN TIMESTAMP NOT NULL  
)
PARTITION BY DATE(JOB_RUN) 
CLUSTER BY brand, condition, seller_power_seller_status;

-- Índices para otimização de queries
CREATE INDEX idx_product_id ON `seu-projeto-gcp.mercado_libre.products_samsung_s25`(product_id);
CREATE INDEX idx_brand_model ON `seu-projeto-gcp.mercado_libre.products_samsung_s25`(brand, model);
CREATE INDEX idx_job_run ON `seu-projeto-gcp.mercado_libre.products_samsung_s25`(JOB_RUN); 