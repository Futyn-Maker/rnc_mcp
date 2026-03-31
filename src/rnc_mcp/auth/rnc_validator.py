import time

import httpx

from rnc_mcp.auth.base import TokenValidator
from rnc_mcp.config import Config


class RNCTokenValidator(TokenValidator):
    """Validates tokens against the RNC API with TTL caching."""

    def __init__(self, cache_ttl: float = 300.0):
        self._cache: dict[str, tuple[bool, float]] = {}
        self._cache_ttl = cache_ttl

    async def validate(self, token: str) -> bool:
        if not token or not token.strip():
            return False

        cached = self._cache.get(token)
        if cached is not None:
            is_valid, timestamp = cached
            if time.time() - timestamp < self._cache_ttl:
                return is_valid

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{Config.RNC_BASE_URL}"
                    f"/auth/check-authenticated/",
                    headers={
                        "Authorization": f"Bearer {token}"
                    },
                )
                is_valid = (
                    response.status_code == 200
                    and response.json() is True
                )
        except Exception:
            is_valid = False

        self._cache[token] = (is_valid, time.time())
        return is_valid
