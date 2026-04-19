"""Cliente HTTP para a API do Strapi 5.

Uso:
    from tools.strapi_client import StrapiClient

    client = StrapiClient()
    articles = client.get("artigos")
"""

import os
from typing import Any, Optional

import requests


class StrapiClient:
    """Wrapper minimalista para a REST API do Strapi."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("STRAPI_URL", "http://localhost:1337")).rstrip("/")
        self._token = token or os.getenv("STRAPI_TOKEN", "")
        if not self._token:
            raise RuntimeError("STRAPI_TOKEN não configurado.")

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    def get(self, endpoint: str, params: Optional[dict] = None) -> Any:
        """GET /api/{endpoint}."""
        url = f"{self.base_url}/api/{endpoint}"
        resp = requests.get(url, headers=self._headers, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def post(self, endpoint: str, payload: dict) -> Any:
        """POST /api/{endpoint} com JSON body."""
        url = f"{self.base_url}/api/{endpoint}"
        resp = requests.post(url, headers=self._headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def delete(self, endpoint: str, doc_id: str) -> int:
        """DELETE /api/{endpoint}/{doc_id}. Retorna status_code."""
        url = f"{self.base_url}/api/{endpoint}/{doc_id}"
        resp = requests.delete(url, headers=self._headers, timeout=15)
        resp.raise_for_status()
        return resp.status_code
