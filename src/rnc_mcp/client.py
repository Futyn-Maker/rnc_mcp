import httpx
import json
from typing import Dict, Any
from rnc_mcp.config import Config


class RNCClient:
    def __init__(self):
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    async def execute_concordance(
            self, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = await client.post(
                    f"{Config.BASE_URL}/lex-gramm/concordance",
                    json=payload,
                    headers=Config.headers()
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ValueError("Invalid RNC Token.")
                raise ValueError(
                    f"RNC API Error {
                        e.response.status_code}: {
                        e.response.text}")

    async def get_corpus_config(self, corpus_type: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            params = {"corpus": json.dumps({"type": corpus_type})}
            response = await client.get(
                f"{Config.BASE_URL}/config/",
                params=params,
                headers=Config.headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_attributes(
        self, corpus_type: str, attr_type: str
    ) -> Dict[str, Any]:
        """
        Fetch attributes for a corpus.

        Args:
            corpus_type: The corpus type (e.g., 'MAIN')
            attr_type: The attribute type ('gr', 'sem', 'syntax', 'flags')
        """
        async with httpx.AsyncClient(
            timeout=self.timeout, follow_redirects=True
        ) as client:
            params = {"corpus": json.dumps({"type": corpus_type})}
            response = await client.get(
                f"{Config.BASE_URL}/attrs/{attr_type}",
                params=params,
                headers=Config.headers()
            )
            response.raise_for_status()
            return response.json()
