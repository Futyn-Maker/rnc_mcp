"""OAuth2 provider for the RNC MCP server.

Implements a self-contained OAuth2 flow where the
authorization step presents a form for the user to enter
their RNC API token. The token is validated against the
RNC API, then an OAuth access token is issued that maps
back to the user's RNC token.

Also supports direct bearer tokens (raw RNC API tokens)
as a fallback for programmatic access.
"""

import secrets
import time
from typing import Optional
from urllib.parse import urlencode

from mcp.server.auth.provider import (
    AuthorizationCode,
    AuthorizationParams,
    RefreshToken,
    TokenError,
    construct_redirect_uri,
)
from mcp.shared.auth import (
    OAuthClientInformationFull,
    OAuthToken,
)
from pydantic import AnyHttpUrl
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route

from mcp.server.auth.settings import (
    ClientRegistrationOptions,
    RevocationOptions,
)
from fastmcp.server.auth.auth import (
    AccessToken,
    OAuthProvider,
)

from rnc_mcp.auth.rnc_validator import RNCTokenValidator
from rnc_mcp.auth.token_store import (
    ACCESS_TOKEN_EXPIRY,
    AUTH_CODE_EXPIRY,
    AuthCodeRecord,
    TokenRecord,
    TokenStore,
)
from rnc_mcp.auth.login_page import render_login_page


class RNCOAuthProvider(OAuthProvider):
    """OAuth2 provider with RNC token login form.

    Supports two authentication paths:
    1. OAuth2 flow: client redirects to /authorize,
       user enters RNC token in a form, server issues
       OAuth access/refresh tokens.
    2. Direct bearer: client sends a raw RNC API token
       as a bearer token (for programmatic access).
    """

    def __init__(
        self,
        store: TokenStore,
        rnc_validator: RNCTokenValidator,
        base_url: str,
        service_documentation_url: str | None = None,
    ):
        super().__init__(
            base_url=base_url,
            service_documentation_url=(
                service_documentation_url
            ),
            client_registration_options=(
                ClientRegistrationOptions(
                    enabled=True,
                    valid_scopes=["rnc:search"],
                )
            ),
            revocation_options=RevocationOptions(
                enabled=True,
            ),
            required_scopes=[],
        )
        self._store = store
        self._rnc_validator = rnc_validator

    # --- Client registration ---

    async def get_client(
        self, client_id: str
    ) -> Optional[OAuthClientInformationFull]:
        data = self._store.get_client(client_id)
        if data is None:
            return None
        return OAuthClientInformationFull(**data)

    async def register_client(
        self, client_info: OAuthClientInformationFull
    ) -> None:
        if client_info.client_id is None:
            raise ValueError("client_id is required")
        self._store.save_client(
            client_info.client_id,
            client_info.model_dump(mode="json"),
        )

    # --- Authorization ---

    async def authorize(
        self,
        client: OAuthClientInformationFull,
        params: AuthorizationParams,
    ) -> str:
        """Redirect to login form instead of
        auto-approving."""
        txn_id = self._store.create_pending_auth(
            client_id=client.client_id,
            redirect_uri=str(params.redirect_uri),
            redirect_uri_provided_explicitly=(
                params.redirect_uri_provided_explicitly
            ),
            state=params.state,
            code_challenge=params.code_challenge,
            scopes=params.scopes or [],
        )
        base = str(self.base_url).rstrip("/")
        return f"{base}/login?{urlencode({'txn': txn_id})}"

    # --- Authorization code ---

    async def load_authorization_code(
        self,
        client: OAuthClientInformationFull,
        authorization_code: str,
    ) -> Optional[AuthorizationCode]:
        record = self._store.get_auth_code(
            authorization_code
        )
        if record is None:
            return None
        if record.client_id != client.client_id:
            return None
        return AuthorizationCode(
            code=record.code,
            client_id=record.client_id,
            redirect_uri=AnyHttpUrl(record.redirect_uri),
            redirect_uri_provided_explicitly=(
                record.redirect_uri_provided_explicitly
            ),
            scopes=record.scopes,
            expires_at=record.expires_at,
            code_challenge=record.code_challenge,
        )

    async def exchange_authorization_code(
        self,
        client: OAuthClientInformationFull,
        authorization_code: AuthorizationCode,
    ) -> OAuthToken:
        # Retrieve the stored record to get the
        # encrypted RNC token
        record = self._store.get_auth_code(
            authorization_code.code
        )
        if record is None:
            raise TokenError(
                "invalid_grant",
                "Authorization code not found or expired.",
            )
        self._store.delete_auth_code(
            authorization_code.code
        )

        rnc_encrypted = record.rnc_token_encrypted
        now = time.time()

        access_value = secrets.token_urlsafe(48)
        refresh_value = secrets.token_urlsafe(48)
        access_expires = int(now + ACCESS_TOKEN_EXPIRY)

        self._store.save_access_token(
            TokenRecord(
                token=access_value,
                client_id=client.client_id,
                scopes=authorization_code.scopes,
                expires_at=access_expires,
                rnc_token_encrypted=rnc_encrypted,
            )
        )
        self._store.save_refresh_token(
            TokenRecord(
                token=refresh_value,
                client_id=client.client_id,
                scopes=authorization_code.scopes,
                expires_at=None,
                rnc_token_encrypted=rnc_encrypted,
            )
        )
        self._store.save_token_pair(
            access_value, refresh_value
        )

        return OAuthToken(
            access_token=access_value,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRY,
            refresh_token=refresh_value,
            scope=" ".join(authorization_code.scopes),
        )

    # --- Refresh tokens ---

    async def load_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: str,
    ) -> Optional[RefreshToken]:
        record = self._store.get_refresh_token(
            refresh_token
        )
        if record is None:
            return None
        if record.client_id != client.client_id:
            return None
        return RefreshToken(
            token=record.token,
            client_id=record.client_id,
            scopes=record.scopes,
            expires_at=record.expires_at,
        )

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        # Get the encrypted RNC token from the old
        # refresh token before revoking
        old_record = self._store.get_refresh_token(
            refresh_token.token
        )
        if old_record is None:
            raise TokenError(
                "invalid_grant",
                "Refresh token not found.",
            )
        rnc_encrypted = old_record.rnc_token_encrypted

        # Revoke old pair
        self._store.revoke_refresh_token(
            refresh_token.token
        )

        now = time.time()
        access_value = secrets.token_urlsafe(48)
        refresh_value = secrets.token_urlsafe(48)
        access_expires = int(now + ACCESS_TOKEN_EXPIRY)

        self._store.save_access_token(
            TokenRecord(
                token=access_value,
                client_id=client.client_id,
                scopes=scopes,
                expires_at=access_expires,
                rnc_token_encrypted=rnc_encrypted,
            )
        )
        self._store.save_refresh_token(
            TokenRecord(
                token=refresh_value,
                client_id=client.client_id,
                scopes=scopes,
                expires_at=None,
                rnc_token_encrypted=rnc_encrypted,
            )
        )
        self._store.save_token_pair(
            access_value, refresh_value
        )

        return OAuthToken(
            access_token=access_value,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRY,
            refresh_token=refresh_value,
            scope=" ".join(scopes),
        )

    # --- Token verification (dual path) ---

    async def load_access_token(
        self, token: str
    ) -> Optional[AccessToken]:
        # Path 1: check issued OAuth tokens
        record = self._store.get_access_token(token)
        if record is not None:
            return AccessToken(
                token=record.token,
                client_id=record.client_id,
                scopes=record.scopes,
                expires_at=record.expires_at,
            )

        # Path 2: raw RNC API token (direct bearer)
        if await self._rnc_validator.validate(token):
            return AccessToken(
                token=token,
                client_id="rnc-direct",
                scopes=["rnc:search"],
            )

        return None

    # --- Revocation ---

    async def revoke_token(
        self,
        token: AccessToken | RefreshToken,
    ) -> None:
        if isinstance(token, AccessToken):
            self._store.revoke_access_token(token.token)
        elif isinstance(token, RefreshToken):
            self._store.revoke_refresh_token(token.token)

    # --- Login page routes ---

    def get_routes(
        self, mcp_path: str | None = None
    ) -> list[Route]:
        routes = super().get_routes(mcp_path)
        routes.append(
            Route(
                "/login",
                endpoint=self._handle_login,
                methods=["GET", "POST"],
            )
        )
        return routes

    async def _handle_login(
        self, request: Request
    ) -> HTMLResponse | RedirectResponse:
        txn_id = request.query_params.get("txn", "")

        if request.method == "GET":
            pending = self._store.get_pending_auth(
                txn_id
            )
            if pending is None:
                return HTMLResponse(
                    render_login_page(
                        error=(
                            "This authorization session "
                            "has expired. Please try "
                            "connecting again."
                        ),
                        show_form=False,
                    ),
                    status_code=400,
                )
            return HTMLResponse(
                render_login_page(txn_id=txn_id)
            )

        # POST: validate token and redirect
        form = await request.form()
        rnc_token = str(
            form.get("rnc_token", "")
        ).strip()
        await form.close()

        pending = self._store.get_pending_auth(txn_id)
        if pending is None:
            return HTMLResponse(
                render_login_page(
                    error=(
                        "This authorization session "
                        "has expired. Please try "
                        "connecting again."
                    ),
                    show_form=False,
                ),
                status_code=400,
            )

        if not rnc_token:
            return HTMLResponse(
                render_login_page(
                    txn_id=txn_id,
                    error="Please enter your API token.",
                ),
                status_code=400,
            )

        is_valid = await self._rnc_validator.validate(
            rnc_token
        )
        if not is_valid:
            return HTMLResponse(
                render_login_page(
                    txn_id=txn_id,
                    error=(
                        "Invalid token. Please check "
                        "your token and try again."
                    ),
                ),
                status_code=400,
            )

        # Consume the pending auth
        pending = self._store.consume_pending_auth(
            txn_id
        )
        if pending is None:
            return HTMLResponse(
                render_login_page(
                    error=(
                        "This authorization session "
                        "has expired. Please try "
                        "connecting again."
                    ),
                    show_form=False,
                ),
                status_code=400,
            )

        # Generate authorization code
        code_value = secrets.token_urlsafe(32)
        encrypted = self._store.encrypt_rnc_token(
            rnc_token
        )

        self._store.save_auth_code(
            AuthCodeRecord(
                code=code_value,
                client_id=pending.client_id,
                scopes=pending.scopes,
                expires_at=(
                    time.time() + AUTH_CODE_EXPIRY
                ),
                code_challenge=pending.code_challenge,
                redirect_uri=pending.redirect_uri,
                redirect_uri_provided_explicitly=(
                    pending.redirect_uri_provided_explicitly
                ),
                rnc_token_encrypted=encrypted,
            )
        )

        redirect_url = construct_redirect_uri(
            pending.redirect_uri,
            code=code_value,
            state=pending.state,
        )
        return RedirectResponse(
            url=redirect_url, status_code=302
        )

    # --- RNC token resolution ---

    def resolve_rnc_token(
        self, oauth_token: str
    ) -> Optional[str]:
        """Resolve an OAuth access token to the
        underlying RNC API token.

        For OAuth-issued tokens: decrypts the stored
        RNC token.
        For direct bearer tokens: returns the token
        itself (it IS the RNC token).
        """
        record = self._store.get_access_token(
            oauth_token
        )
        if record is not None:
            return self._store.decrypt_rnc_token(
                record.rnc_token_encrypted
            )
        # Direct bearer: the token itself is the
        # RNC API token
        return oauth_token
