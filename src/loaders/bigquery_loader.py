import logging
from typing import List, Dict, Any
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from datetime import datetime, date, time
import decimal

class BigQueryLoader:
    """Carregador de dados para o BigQuery (schema atualizado para o output do Apify)."""

    def __init__(self, project_id: str, dataset_id: str, table_id: str):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.client = bigquery.Client(project=project_id)
        self.logger = logging.getLogger(__name__)

    def create_table_if_not_exists(self):
        table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
        try:
            self.client.get_table(table_ref)
            self.logger.info(f"Tabela {self.table_id} já existe")
        except NotFound:
            schema = self._get_table_schema()
            table = bigquery.Table(table_ref, schema=schema)
            # particionamento por JOB_RUN
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="JOB_RUN"
            )
            # clustering sugerido
            table.clustering_fields = ["seller", "condition", "currency"]
            table = self.client.create_table(table)
            self.logger.info(f"Tabela {self.table_id} criada com sucesso (particionada por JOB_RUN)")

    def load_data(self, products: List[Dict[str, Any]]) -> int:
        if not products:
            self.logger.info("Nenhum produto para carregar")
            return 0

        # Serializar valores não-JSON-serializáveis (ex.: datetime)
        json_rows = [self._serialize_item(p) for p in products]

        table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            schema=self._get_table_schema(),
            autodetect=False
        )

        try:
            job = self.client.load_table_from_json(json_rows, table_ref, job_config=job_config)
            job.result()
            self.logger.info(f"Carregados {len(products)} produtos no BigQuery")
            return len(products)
        except Exception as e:
            self.logger.exception(f"Erro ao carregar no BigQuery: {e}")
            raise

    def _serialize_item(self, item: Any) -> Any:
        """
        Converte recursivamente o item para tipos JSON serializáveis.
        - datetime/date/time -> ISO 8601 string (Z se naive)
        - decimal.Decimal -> float (ou string se preferir)
        - bytes -> decode utf-8
        - outros tipos compostos (list/dict/tuple) -> recursivo
        """
        if item is None:
            return None

        # Primitivos seguros
        if isinstance(item, (str, int, float, bool)):
            return item

        # datetime-like
        if isinstance(item, datetime):
            if item.tzinfo is None:
                return item.isoformat() + "Z"
            return item.isoformat()

        if isinstance(item, date) and not isinstance(item, datetime):
            # date -> iso date
            return item.isoformat()

        if isinstance(item, time):
            return item.isoformat()

        if isinstance(item, decimal.Decimal):
            # converter Decimal para float pode perder precisão, ajustar se precisar
            try:
                return float(item)
            except Exception:
                return str(item)

        # iteráveis
        if isinstance(item, (list, tuple, set)):
            return [self._serialize_item(v) for v in item]

        if isinstance(item, dict):
            out = {}
            for k, v in item.items():
                # BigQuery campo names devem ser strings; manter chaves como estão
                out[k] = self._serialize_item(v)
            return out

        # bytes
        if isinstance(item, (bytes, bytearray)):
            try:
                return item.decode("utf-8")
            except Exception:
                return str(item)

        # Fallback: string representation
        return str(item)

    def _get_table_schema(self):
        # Schema alinhado ao output do Apify
        return [
            bigquery.SchemaField("product_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("title", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("subtitle", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("originalPrice", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("price", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("price_string", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("alternativePrice", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("rating", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("reviews", "INT64", mode="NULLABLE"),
            bigquery.SchemaField("condition", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("seller", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("images", "STRING", mode="REPEATED"),
            bigquery.SchemaField("sellCount", "INT64", mode="NULLABLE"),
            bigquery.SchemaField("url", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("currency", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("extraction_date", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("JOB_RUN", "TIMESTAMP", mode="REQUIRED"),
        ]