import logging
import os
import sys
from typing import Dict, Any
import yaml
from datetime import datetime

from extractors.meli_extractor import MeliExtractor
from transformers.product_transformer import ProductTransformer
from loaders.bigquery_loader import BigQueryLoader

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('etl_pipeline.log')
    ]
)

class MeliETLPipeline:
    """Pipeline principal ETL do Mercado Libre."""
    
    def __init__(self, config_path: str = 'config/config.yaml'):
        """Inicializa o pipeline com configurações."""
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        
        # Timestamp único para toda a execução do job
        self.job_run_timestamp = datetime.utcnow()
        
        # Inicializar componentes
        self.extractor = MeliExtractor(
            site_id=self.config['meli']['site_id']
        )
        self.transformer = ProductTransformer()
        self.loader = BigQueryLoader(
            project_id=self.config['bigquery']['project_id'],
            dataset_id=self.config['bigquery']['dataset_id'],
            table_id=self.config['bigquery']['table_id']
        )
    
    def run(self) -> Dict[str, Any]:
        """
        Executa o pipeline completo.
        
        Returns:
            Dicionário com métricas de execução
        """
        start_time = datetime.now()
        metrics = {
            'JOB_RUN': self.job_run_timestamp,  # Adicionar JOB_RUN às métricas
            'start_time': start_time,
            'products_extracted': 0,
            'products_transformed': 0,
            'products_loaded': 0,
            'success': False,
            'errors': []
        }
        
        try:
            self.logger.info(f"Iniciando pipeline ETL do Mercado Libre - JOB_RUN: {self.job_run_timestamp}")
            
            # 1. Extração
            self.logger.info("Iniciando extração de dados")
            raw_products = self.extractor.search_products(
                query=self.config['meli']['search_query'],
                limit=self.config['meli']['limit_per_page']
            )
            metrics['products_extracted'] = len(raw_products)
            self.logger.info(f"Extraídos {len(raw_products)} produtos")
            
            if not raw_products:
                self.logger.warning("Nenhum produto encontrado")
                return metrics
            
            # 2. Transformação
            self.logger.info("Iniciando transformação de dados")
            transformed_products = self.transformer.transform_products(raw_products)
            metrics['products_transformed'] = len(transformed_products)
            self.logger.info(f"Transformados {len(transformed_products)} produtos")
            
            # 3. Carga
            self.logger.info("Iniciando carga no BigQuery")
            self.loader.create_table_if_not_exists()
            loaded_count = self.loader.load_data(transformed_products)
            metrics['products_loaded'] = loaded_count
            
            metrics['success'] = True
            self.logger.info(f"Pipeline executado com sucesso - JOB_RUN: {self.job_run_timestamp}")
            
        except Exception as e:
            error_msg = f"Erro no pipeline: {e}"
            self.logger.error(error_msg)
            metrics['errors'].append(error_msg)
            
        finally:
            metrics['end_time'] = datetime.now()
            metrics['duration_seconds'] = (
                metrics['end_time'] - metrics['start_time']
            ).total_seconds()
            
            self._log_metrics(metrics)
            
        return metrics
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Carrega configurações do arquivo YAML."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                
            # Sobrescrever com variáveis de ambiente se existirem
            config['bigquery']['project_id'] = os.getenv(
                'GCP_PROJECT_ID', 
                config['bigquery']['project_id']
            )
            config['bigquery']['dataset_id'] = os.getenv(
                'BQ_DATASET_ID',
                config['bigquery']['dataset_id']
            )
            config['bigquery']['table_id'] = os.getenv(
                'BQ_TABLE_ID',
                config['bigquery']['table_id']
            )
            
            return config
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar configurações: {e}")
            raise
    
    def _log_metrics(self, metrics: Dict[str, Any]):
        """Loga métricas de execução."""
        self.logger.info("=== MÉTRICAS DE EXECUÇÃO ===")
        self.logger.info(f"JOB_RUN: {metrics['JOB_RUN']}")
        self.logger.info(f"Duração: {metrics['duration_seconds']:.2f} segundos")
        self.logger.info(f"Produtos extraídos: {metrics['products_extracted']}")
        self.logger.info(f"Produtos transformados: {metrics['products_transformed']}")
        self.logger.info(f"Produtos carregados: {metrics['products_loaded']}")
        self.logger.info(f"Sucesso: {metrics['success']}")
        
        if metrics['errors']:
            self.logger.error("Erros encontrados:")
            for error in metrics['errors']:
                self.logger.error(f"- {error}")

def main():
    """Função principal."""
    pipeline = MeliETLPipeline()
    results = pipeline.run()
    
    # Exit code baseado no sucesso
    exit_code = 0 if results['success'] else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()