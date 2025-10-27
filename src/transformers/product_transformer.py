import logging
from typing import List, Dict, Any
from datetime import datetime
import json

class ProductTransformer:
    """Transformador de dados de produtos do Mercado Libre."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def transform_products(self, raw_products: List[Dict]) -> List[Dict]:
        """
        Transforma produtos brutos em formato estruturado para BigQuery.
        
        Args:
            raw_products: Lista de produtos brutos da API
            
        Returns:
            Lista de produtos transformados
        """
        transformed_products = []
        
        for product in raw_products:
            try:
                transformed = self._transform_single_product(product)
                transformed_products.append(transformed)
            except Exception as e:
                self.logger.error(f"Erro ao transformar produto {product.get('id')}: {e}")
                
        return transformed_products
    
    def _transform_single_product(self, product: Dict) -> Dict:
        """Transforma um único produto."""
        job_run_time = datetime.utcnow()  # Timestamp único para todo o job
        
        return {
            'product_id': str(product.get('id', '')),
            'title': self._clean_text(product.get('title', '')),
            'price': float(product.get('price', 0)) if product.get('price') else None,
            'currency_id': product.get('currency_id', ''),
            'condition': product.get('condition', ''),
            'category_id': product.get('category_id', ''),
            'thumbnail_url': product.get('thumbnail', ''),
            'permalink': product.get('permalink', ''),
            
            # Seller info
            'seller_id': str(product.get('seller_id', '')),
            'seller_nickname': self._clean_text(product.get('seller_nickname', '')),
            'seller_reputation': self._extract_seller_reputation(product.get('seller_info', {})),
            'seller_power_seller_status': product.get('seller_info', {}).get('power_seller_status'),
            
            # Location
            'city': product.get('address', {}).get('city_name', ''),
            'state': product.get('address', {}).get('state_name', ''),
            
            # Product details
            'attributes': json.dumps(self._extract_attributes(product.get('attributes', []))),
            'pictures': json.dumps(self._extract_pictures(product.get('pictures', []))),
            'warranty': product.get('warranty'),
            
            # Technical specs
            'brand': self._extract_attribute_value(product.get('attributes', []), 'BRAND'),
            'model': self._extract_attribute_value(product.get('attributes', []), 'MODEL'),
            'memory': self._extract_attribute_value(product.get('attributes', []), 'INTERNAL_MEMORY'),
            'color': self._extract_attribute_value(product.get('attributes', []), 'COLOR'),
            
            # Metadata
            'extraction_date': self._parse_datetime(product.get('extraction_date')),
            'JOB_RUN': job_run_time  # Campo renomeado e padronizado
        }
    
    def _clean_text(self, text: str) -> str:
        """Limpa e normaliza texto."""
        if not text:
            return ''
        return text.strip().replace('\n', ' ').replace('\r', ' ')[:500]  # Limita tamanho
    
    def _extract_seller_reputation(self, seller_info: Dict) -> Dict:
        """Extrai informações de reputação do vendedor."""
        reputation = seller_info.get('seller_reputation', {})
        return {
            'level_id': reputation.get('level_id'),
            'power_seller_status': reputation.get('power_seller_status'),
            'transactions_total': reputation.get('transactions', {}).get('total', 0),
            'transactions_completed': reputation.get('transactions', {}).get('completed', 0)
        }
    
    def _extract_attributes(self, attributes: List[Dict]) -> Dict:
        """Extrai atributos do produto."""
        attr_dict = {}
        for attr in attributes:
            if attr.get('id') and attr.get('value_name'):
                attr_dict[attr['id']] = {
                    'name': attr.get('name', ''),
                    'value': attr.get('value_name', '')
                }
        return attr_dict
    
    def _extract_pictures(self, pictures: List[Dict]) -> List[str]:
        """Extrai URLs das imagens."""
        return [pic.get('secure_url', '') for pic in pictures if pic.get('secure_url')]
    
    def _extract_attribute_value(self, attributes: List[Dict], attr_id: str) -> str:
        """Extrai valor de um atributo específico."""
        for attr in attributes:
            if attr.get('id') == attr_id:
                return attr.get('value_name', '')
        return ''
    
    def _parse_datetime(self, date_str: str) -> datetime:
        """Converte string de data para datetime."""
        try:
            if date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception:
            pass
        return datetime.utcnow()