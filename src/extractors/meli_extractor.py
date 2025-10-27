import requests
import logging
import time
from typing import List, Dict, Optional
from datetime import datetime

class MeliExtractor:
    """Extrator de dados da API do Mercado Libre."""
    
    BASE_URL = "https://api.mercadolibre.com"
    
    def __init__(self, site_id: str = "MLA"):
        """
        Inicializa o extrator.
        
        Args:
            site_id: Código do site (MLA para Argentina)
        """
        self.site_id = site_id
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        
    def search_products(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Busca produtos na API do Mercado Libre.
        
        Args:
            query: Termo de busca
            limit: Limite de resultados por página
            
        Returns:
            Lista de produtos encontrados
        """
        products = []
        offset = 0
        
        try:
            while len(products) < 200:  # Limite máximo de produtos
                url = f"{self.BASE_URL}/sites/{self.site_id}/search"
                params = {
                    'q': query,
                    'limit': limit,
                    'offset': offset
                }
                
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    break
                    
                # Enriquecer dados com informações detalhadas
                enriched_products = self._enrich_products(results)
                products.extend(enriched_products)
                
                offset += limit
                
                # Rate limiting
                time.sleep(0.5)
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro na busca de produtos: {e}")
            raise
            
        return products
    
    def _enrich_products(self, products: List[Dict]) -> List[Dict]:
        """
        Enriquece os dados dos produtos com informações detalhadas.
        
        Args:
            products: Lista de produtos básicos
            
        Returns:
            Lista de produtos enriquecidos
        """
        enriched = []
        
        for product in products:
            try:
                # Obter detalhes do produto
                details = self._get_product_details(product['id'])
                
                # Obter informações do vendedor
                seller_info = self._get_seller_info(product.get('seller', {}).get('id'))
                
                # Combinar informações
                enriched_product = {
                    'id': product['id'],
                    'title': product['title'],
                    'price': product['price'],
                    'currency_id': product['currency_id'],
                    'condition': product['condition'],
                    'thumbnail': product['thumbnail'],
                    'permalink': product['permalink'],
                    'category_id': product['category_id'],
                    'seller_id': product.get('seller', {}).get('id'),
                    'seller_nickname': product.get('seller', {}).get('nickname'),
                    'address': product.get('address', {}),
                    'attributes': details.get('attributes', []),
                    'pictures': details.get('pictures', []),
                    'warranty': details.get('warranty'),
                    'seller_info': seller_info,
                    'extraction_date': datetime.utcnow().isoformat()
                }
                
                enriched.append(enriched_product)
                
            except Exception as e:
                self.logger.warning(f"Erro ao enriquecer produto {product['id']}: {e}")
                # Adicionar produto básico mesmo com erro
                product['extraction_date'] = datetime.utcnow().isoformat()
                enriched.append(product)
                
        return enriched
    
    def _get_product_details(self, product_id: str) -> Dict:
        """Obtém detalhes específicos do produto."""
        try:
            url = f"{self.BASE_URL}/items/{product_id}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.warning(f"Erro ao obter detalhes do produto {product_id}: {e}")
            return {}
    
    def _get_seller_info(self, seller_id: Optional[int]) -> Dict:
        """Obtém informações do vendedor."""
        if not seller_id:
            return {}
            
        try:
            url = f"{self.BASE_URL}/users/{seller_id}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.warning(f"Erro ao obter info do vendedor {seller_id}: {e}")
            return {}