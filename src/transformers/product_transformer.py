import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import hashlib
import re

class ProductTransformer:
    """
    Transforma cada registro retornado pelo Apify Actor para o formato de ingestão no BigQuery.
    Espera o objeto no formato que você forneceu.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def transform_products(self, raw_products: List[Dict[str, Any]], job_run_ts: datetime) -> List[Dict[str, Any]]:
        transformed = []
        for item in raw_products:
            try:
                transformed.append(self._transform_single(item, job_run_ts))
            except Exception as e:
                self.logger.exception(f"Erro transformando produto (title={item.get('title')}): {e}")
        return transformed

    def _transform_single(self, item: Dict[str, Any], job_run_ts: datetime) -> Dict[str, Any]:
        """
        Mapeia campos do output do Apify para o schema do BigQuery.
        Gera product_id via hash do URL quando não há ID.
        """
        url = item.get("url", "")
        product_id = self._derive_product_id(url, item)

        title = self._clean_text(item.get("title", ""))
        subtitle = self._clean_text(item.get("subtitle", ""))
        original_price = self._clean_price_string(item.get("originalPrice", ""))
        price_str = str(item.get("price", "")) if item.get("price") is not None else ""
        numeric_price = self._parse_numeric_price(price_str)  # float or None
        alt_price = self._clean_price_string(item.get("alternativePrice", ""))

        rating = self._parse_float(item.get("rating"))
        reviews = self._parse_int(item.get("reviews"))
        condition = item.get("condition") or item.get("conditionText") or ""
        seller = item.get("seller") or item.get("sellerNickname") or ""
        description = self._clean_text(item.get("description", ""))
        images = item.get("images") or []
        if isinstance(images, str):
            images = [images]
        sell_count = self._parse_int(item.get("sellCount") or item.get("sold") or item.get("sell_count"))

        currency = item.get("currency") or item.get("currency_id") or "ARS"

        # extraction_date: se Apify fornecer timestamp/createdAt, use, senão fallback para job_run_ts
        extraction_date = None
        if item.get("extractionDate"):
            try:
                extraction_date = datetime.fromisoformat(item.get("extractionDate").replace("Z", "+00:00"))
            except Exception:
                extraction_date = job_run_ts
        else:
            extraction_date = job_run_ts

        transformed = {
            "product_id": product_id,
            "title": title,
            "subtitle": subtitle,
            "originalPrice": original_price,
            "price": numeric_price,
            "price_string": price_str,
            "alternativePrice": alt_price,
            "rating": rating,
            "reviews": reviews,
            "condition": condition,
            "seller": seller,
            "description": description,
            "images": images,
            "sellCount": sell_count,
            "url": url,
            "currency": currency,
            "extraction_date": extraction_date,
            "JOB_RUN": job_run_ts
        }

        return transformed

    def _derive_product_id(self, url: str, item: Dict[str, Any]) -> str:
        """
        Deriva um product_id:
        - se existir campo 'id' retorna;
        - senão, usa SHA1 do URL (se existir URL);
        - se não houver URL, usa SHA1 do title+seller.
        """
        if item.get("id"):
            return str(item.get("id"))
        if url:
            return hashlib.sha1(url.encode("utf-8")).hexdigest()
        key = (item.get("title", "") + "|" + str(item.get("seller", "")))
        return hashlib.sha1(key.encode("utf-8")).hexdigest()

    def _parse_numeric_price(self, price_raw: str) -> Optional[float]:
        """
        Tenta extrair número de price em string que pode conter pontos e vírgulas.
        Ex: '1.645.944.69' -> remove não-dígitos exceto '.' e ',' e tenta determinar.
        """
        if price_raw is None or price_raw == "":
            return None
        # Normalizar: manter dígitos e ponto/virgula
        cleaned = re.sub(r"[^\d\.,]", "", price_raw)
        # Se houver mais de uma vírgula/ponto, tentar remover separadores de milhar:
        # Strategy: remover todos os '.' se houver mais de 1 '.', então replace ',' por '.'
        if cleaned.count(".") > 1:
            cleaned = cleaned.replace(".", "")
        cleaned = cleaned.replace(",", ".")
        try:
            return float(cleaned)
        except Exception:
            return None

    def _clean_price_string(self, s: str) -> str:
        if s is None:
            return ""
        return str(s).strip()

    def _parse_int(self, v) -> Optional[int]:
        try:
            if v is None or v == "":
                return None
            return int(str(v).replace(".", "").replace(",", ""))
        except Exception:
            return None

    def _parse_float(self, v) -> Optional[float]:
        try:
            if v is None or v == "":
                return None
            return float(str(v).replace(",", "."))
        except Exception:
            return None

    def _clean_text(self, text: str) -> str:
        if text is None:
            return ""
        if not isinstance(text, str):
            text = str(text)
        return text.strip()