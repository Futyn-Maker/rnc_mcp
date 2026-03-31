from typing import Optional

from fastmcp.server.auth.auth import (
    TokenVerifier, AccessToken,
)

from rnc_mcp.auth.base import TokenValidator


class RNCAuthProvider(TokenVerifier):
    """FastMCP auth provider that validates RNC API
    tokens via a pluggable TokenValidator."""

    def __init__(self, validator: TokenValidator):
        super().__init__()
        self._validator = validator

    async def verify_token(
        self, token: str
    ) -> Optional[AccessToken]:
        if not token or not token.strip():
            return None

        if not await self._validator.validate(token):
            return None

        return AccessToken(
            token=token,
            client_id="rnc-user",
            scopes=["rnc:search"],
        )
