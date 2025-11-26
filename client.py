import httpx
import json
from typing import Dict, Any
from config import Config


class RNCClient:
    async def execute_search(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{Config.BASE_URL}/lex-gramm/concordance",
                    json=payload,
                    headers=Config.headers(),
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ValueError(
                        "Invalid or expired RNC Token. Please check your environment variables.")
                raise ValueError(
                    f"RNC API Error {
                        e.response.status_code}: {
                        e.response.text}")

    async def get_grammar_attributes(self) -> Dict[str, Any]:
        """Fetches the schema of grammatical attributes."""
        async with httpx.AsyncClient() as client:
            # Using MAIN corpus as context to resolve attributes
            params = {"corpus": json.dumps({"type": "MAIN"})}
            try:
                response = await client.get(
                    f"{Config.BASE_URL}/attrs/gramm",
                    params=params,
                    headers=Config.headers(),
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise ValueError(
                    f"Failed to fetch attributes: {e.response.status_code} - {e.response.text}")
            except json.JSONDecodeError:
                raise ValueError(
                    "Failed to decode attribute response. API might have returned HTML (error page).")
