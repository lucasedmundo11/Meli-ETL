import logging
from typing import List, Dict
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import json

class BigQueryLoader:
    """Carregador de dados para o BigQuery."""
    
    def __init__(self, project_id: str, dataset_id: str, table_id: str):
        """
        Inicializa o loader do BigQuery.
        
        Args:
            project_id: ID do projeto GCP
            dataset_id: ID do dataset
            table_id: ID da tabela
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.client = bigquery.Client(project=project_id)
        self.logger = logging.getLogger(__name__)
        
    def create_table_if_not_exists(self):
        """Cria a tabela se ela não existir."""
        table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
        
        try:
            self.client.get_table(table_ref)
            self.logger.info(f"Tabela {self.table_id} já existe")
        except NotFound:
            schema = self._get_table_schema()
            table = bigquery.Table(table_ref, schema=schema)
            
            # Configurar particionamento por JOB_RUN
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="JOB_RUN"
            )
            
            # Configurar clustering
            table.clustering_fields = ["brand", "condition", "seller_power_seller_status"]
            
            table = self.client.create_table(table)
            self.logger.info(f"Tabela {self.table_id} criada com sucesso")
    
    def load_data(self, products: List[Dict]) -> int:
        """
        Carrega dados no BigQuery.
        
        Args:
            products: Lista de produtos transformados
            
        Returns:
            Número de linhas inseridas
        """
        if not products:
            self.logger.info("Nenhum produto para carregar")
            return 0
        
        table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
        
        # Configuração do job de carga
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            autodetect=False,
            schema=self._get_table_schema()
        )
        
        try:
            job = self.client.load_table_from_json(
                products, table_ref, job_config=job_config
            )
            job.result()  # Aguarda conclusão
            
            self.logger.info(f"Carregados {len(products)} produtos no BigQuery")
            self.logger.info(f"JOB_RUN timestamp: {products[0]['JOB_RUN']}")
            return len(products)
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados no BigQuery: {e}")
            raise
    
    def _get_table_schema(self) -> List[bigquery.SchemaField]:
        """Define o schema da tabela."""
        return [
            bigquery.SchemaField("product_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("title", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("price", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("currency_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("condition", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("category_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("thumbnail_url", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("permalink", "STRING", mode="NULLABLE"),
            
            # Seller fields
            bigquery.SchemaField("seller_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("seller_nickname", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("seller_reputation", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("seller_power_seller_status", "STRING", mode="NULLABLE"),
            
            # Location fields
            bigquery.SchemaField("city", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("state", "STRING", mode="NULLABLE"),
            
            # Product details
            bigquery.SchemaField("attributes", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("pictures", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("warranty", "STRING", mode="NULLABLE"),
            
            # Technical specs
            bigquery.SchemaField("brand", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("model", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("memory", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("color", "STRING", mode="NULLABLE"),
            
            # Metadata
            bigquery.SchemaField("extraction_date", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("JOB_RUN", "TIMESTAMP", mode="REQUIRED"),  # Campo renomeado
        ]