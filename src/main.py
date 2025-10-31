import logging
import os
import sys
from typing import Dict, Any
import yaml
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from extractors.apify_extractor import ApifyExtractor
from transformers.product_transformer import ProductTransformer
from loaders.bigquery_loader import BigQueryLoader

# Logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler('etl_pipeline.log')]
)

class MeliETLPipeline:
    def __init__(self, config_path: str = 'config/config.yaml'):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.job_run_ts = datetime.utcnow()

        # Extrator Apify
        self.extractor = ApifyExtractor(
            actor_id=self.config.get("apify", {}).get("actor_id", "q0PB9Xd1hjynYAEhi"),
            apify_token=os.getenv("APIFY_TOKEN"),
            domain_code=self.config.get("apify", {}).get("domain_code", "AR")
        )

        self.transformer = ProductTransformer()
        self.loader = BigQueryLoader(
            project_id=self.config['bigquery']['project_id'],
            dataset_id=self.config['bigquery']['dataset_id'],
            table_id=self.config['bigquery']['table_id']
        )

    def run(self) -> Dict[str, Any]:
        metrics = {
            "JOB_RUN": self.job_run_ts,
            "products_extracted": 0,
            "products_transformed": 0,
            "products_loaded": 0,
            "success": False,
            "errors": []
        }

        try:
            search_query = self.config['apify'].get('search_query', 'Samsung Galaxy S25')
            self.logger.info(f"Iniciando execução JOB_RUN={self.job_run_ts} - busca: {search_query}")

            # Extract
            raw_items = self.extractor.run_search(
                search=search_query,
                search_category=self.config['apify'].get('search_category', 'all'),
                sort_by=self.config['apify'].get('sort_by', 'relevance'),
                fast_mode=self.config['apify'].get('fast_mode', False),
                use_proxy=self.config['apify'].get('use_proxy', True),
            )
            metrics['products_extracted'] = len(raw_items)

            if not raw_items:
                self.logger.warning("Nenhum item extraído; finalizando")
                return metrics

            # Transform
            transformed = self.transformer.transform_products(raw_items, self.job_run_ts)
            metrics['products_transformed'] = len(transformed)

            # Load
            self.loader.create_table_if_not_exists()
            loaded = self.loader.load_data(transformed)
            metrics['products_loaded'] = loaded

            metrics['success'] = True
            self.logger.info(f"JOB_RUN {self.job_run_ts} finalizado com sucesso")

        except Exception as e:
            self.logger.exception(f"Erro no pipeline: {e}")
            metrics['errors'].append(str(e))

        return metrics

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, 'r', encoding='utf-8') as fh:
                cfg = yaml.safe_load(fh)
        except Exception as e:
            self.logger.error(f"Erro ao ler config {config_path}: {e}")
            raise

        # Defaults minimal
        cfg.setdefault('apify', {})
        cfg.setdefault('bigquery', {})
        return cfg

def main():
    pipeline = MeliETLPipeline()
    results = pipeline.run()
    if results.get("success"):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()