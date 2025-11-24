import httpx
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
                # Handle 401 specifically for better UX
                if e.response.status_code == 401:
                    raise ValueError("Invalid or expired RNC Token. Please update configuration.")
                raise e

    async def get_config(self) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{Config.BASE_URL}/config",
                params={"corpus": '{"type": "MAIN"}'}, # Default config
                headers=Config.headers()
            )
            return response.json()
