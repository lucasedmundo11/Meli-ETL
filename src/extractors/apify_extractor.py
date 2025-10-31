import os
import logging
from typing import List, Dict, Any, Optional
from apify_client import ApifyClient

class ApifyExtractor:
    """
    Extrator que executa um Actor Apify (passado por actor_id) e retorna os itens do dataset do run.
    Usa APIFY_TOKEN via variável de ambiente.
    """
    def __init__(self, actor_id: str = "q0PB9Xd1hjynYAEhi", apify_token: Optional[str] = None, domain_code: str = "AR"):
        self.logger = logging.getLogger(__name__)
        token = apify_token or os.getenv("APIFY_TOKEN")
        if not token:
            raise ValueError("APIFY_TOKEN não encontrado nas variáveis de ambiente")
        self.client = ApifyClient(token)
        self.actor_id = actor_id
        self.domain_code = domain_code

    def run_search(self, search: str, search_category: str = "all", sort_by: str = "relevance", fast_mode: bool = False, use_proxy: bool = True) -> List[Dict[str, Any]]:
        """
        Executa o actor do Apify com os inputs necessários e retorna a lista de itens (dicionários).
        """
        run_input = {
            "debugMode": False,
            "domainCode": self.domain_code,
            "fastMode": fast_mode,
            "maxItemCount": 50,
            "proxy": {
                "useApifyProxy": bool(use_proxy),
                "apifyProxyGroups": ["RESIDENTIAL"] if use_proxy else []
            },
            "search": search,
            "searchCategory": search_category,
            "sortBy": sort_by
        }

        self.logger.info(f"Executando Actor {self.actor_id} no Apify para busca: {search}")
        try:
            run = self.client.actor(self.actor_id).call(run_input=run_input)
        except Exception as e:
            self.logger.error(f"Erro ao executar actor {self.actor_id}: {e}")
            raise

        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            self.logger.warning("Run não retornou defaultDatasetId — sem resultados")
            return []

        self.logger.info(f"Recuperando resultados do dataset {dataset_id}")
        items = []
        try:
            # iterate_items retorna gerador
            for item in self.client.dataset(dataset_id).iterate_items():
                # O item já deve ser um dict no formato que você descreveu; só append
                items.append(item)
        except Exception as e:
            self.logger.error(f"Erro ao iterar items do dataset {dataset_id}: {e}")
            raise

        self.logger.info(f"Total de itens obtidos do Apify: {len(items)}")
        return items