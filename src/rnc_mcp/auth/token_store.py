"""Encrypted token store backed by SQLite.

Stores OAuth tokens (access, refresh, authorization codes,
client registrations) and their mappings to RNC API tokens.
RNC tokens are encrypted at rest using Fernet symmetric
encryption. The SQLite database survives server restarts.
"""

import json
import os
import secrets
import sqlite3
import time
from dataclasses import dataclass
from typing import Optional

from cryptography.fernet import Fernet


@dataclass
class TokenRecord:
    """A stored OAuth token with its RNC token mapping."""
    token: str
    client_id: str
    scopes: list[str]
    expires_at: Optional[int]
    rnc_token_encrypted: bytes


@dataclass
class AuthCodeRecord:
    """A stored authorization code."""
    code: str
    client_id: str
    scopes: list[str]
    expires_at: float
    code_challenge: str
    redirect_uri: str
    redirect_uri_provided_explicitly: bool
    rnc_token_encrypted: bytes


@dataclass
class PendingAuth:
    """A pending authorization request (before user submits
    the login form)."""
    transaction_id: str
    client_id: str
    redirect_uri: str
    redirect_uri_provided_explicitly: bool
    state: str
    code_challenge: str
    scopes: list[str]
    expires_at: float


# Default expiration times
AUTH_CODE_EXPIRY = 5 * 60  # 5 minutes
ACCESS_TOKEN_EXPIRY = 60 * 60  # 1 hour
PENDING_AUTH_EXPIRY = 10 * 60  # 10 minutes


class TokenStore:
    """Encrypted SQLite-backed token store.

    All RNC API tokens are encrypted with Fernet before
    storage. The encryption key is auto-generated on first
    run and stored in the database directory.
    """

    def __init__(
        self,
        db_path: str = "data/oauth.db",
        fernet_key: Optional[bytes] = None,
    ):
        self._db_path = db_path
        self._pending: dict[str, PendingAuth] = {}

        if fernet_key:
            self._fernet = Fernet(fernet_key)
        else:
            key_path = os.path.join(
                os.path.dirname(db_path) or ".",
                ".fernet.key",
            )
            self._fernet = Fernet(
                self._load_or_create_key(key_path)
            )

        self._init_db()

    @staticmethod
    def _load_or_create_key(key_path: str) -> bytes:
        """Load existing Fernet key or generate a new one."""
        if os.path.exists(key_path):
            with open(key_path, "rb") as f:
                return f.read()
        key = Fernet.generate_key()
        os.makedirs(
            os.path.dirname(key_path) or ".", exist_ok=True
        )
        fd = os.open(
            key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
        )
        try:
            os.write(fd, key)
        finally:
            os.close(fd)
        return key

    def _init_db(self):
        os.makedirs(
            os.path.dirname(self._db_path) or ".",
            exist_ok=True,
        )
        conn = sqlite3.connect(self._db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS clients (
                    client_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS auth_codes (
                    code TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL,
                    scopes TEXT NOT NULL,
                    expires_at REAL NOT NULL,
                    code_challenge TEXT NOT NULL,
                    redirect_uri TEXT NOT NULL,
                    redirect_uri_explicit INTEGER NOT NULL,
                    rnc_token BLOB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS access_tokens (
                    token TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL,
                    scopes TEXT NOT NULL,
                    expires_at REAL,
                    rnc_token BLOB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS refresh_tokens (
                    token TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL,
                    scopes TEXT NOT NULL,
                    expires_at REAL,
                    rnc_token BLOB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS token_pairs (
                    access_token TEXT NOT NULL,
                    refresh_token TEXT NOT NULL,
                    PRIMARY KEY (access_token, refresh_token)
                );
            """)
        finally:
            conn.close()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def encrypt_rnc_token(self, rnc_token: str) -> bytes:
        return self._fernet.encrypt(rnc_token.encode())

    def decrypt_rnc_token(self, encrypted: bytes) -> str:
        return self._fernet.decrypt(encrypted).decode()

    # --- Clients ---

    def save_client(self, client_id: str, data: dict):
        conn = self._conn()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO clients "
                "(client_id, data) VALUES (?, ?)",
                (client_id, json.dumps(data)),
            )
            conn.commit()
        finally:
            conn.close()

    def get_client(self, client_id: str) -> Optional[dict]:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT data FROM clients "
                "WHERE client_id = ?",
                (client_id,),
            ).fetchone()
            return json.loads(row[0]) if row else None
        finally:
            conn.close()

    # --- Pending authorizations (in-memory only) ---

    def create_pending_auth(
        self,
        client_id: str,
        redirect_uri: str,
        redirect_uri_provided_explicitly: bool,
        state: str,
        code_challenge: str,
        scopes: list[str],
    ) -> str:
        txn_id = secrets.token_urlsafe(32)
        self._pending[txn_id] = PendingAuth(
            transaction_id=txn_id,
            client_id=client_id,
            redirect_uri=redirect_uri,
            redirect_uri_provided_explicitly=(
                redirect_uri_provided_explicitly
            ),
            state=state,
            code_challenge=code_challenge,
            scopes=scopes,
            expires_at=time.time() + PENDING_AUTH_EXPIRY,
        )
        return txn_id

    def get_pending_auth(
        self, txn_id: str
    ) -> Optional[PendingAuth]:
        pending = self._pending.get(txn_id)
        if pending and time.time() < pending.expires_at:
            return pending
        if pending:
            del self._pending[txn_id]
        return None

    def consume_pending_auth(
        self, txn_id: str
    ) -> Optional[PendingAuth]:
        pending = self.get_pending_auth(txn_id)
        if pending:
            del self._pending[txn_id]
        return pending

    # --- Authorization codes ---

    def save_auth_code(self, record: AuthCodeRecord):
        conn = self._conn()
        try:
            conn.execute(
                "INSERT INTO auth_codes "
                "(code, client_id, scopes, expires_at, "
                "code_challenge, redirect_uri, "
                "redirect_uri_explicit, rnc_token) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record.code,
                    record.client_id,
                    json.dumps(record.scopes),
                    record.expires_at,
                    record.code_challenge,
                    record.redirect_uri,
                    int(
                        record.redirect_uri_provided_explicitly
                    ),
                    record.rnc_token_encrypted,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_auth_code(
        self, code: str
    ) -> Optional[AuthCodeRecord]:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT code, client_id, scopes, "
                "expires_at, code_challenge, redirect_uri, "
                "redirect_uri_explicit, rnc_token "
                "FROM auth_codes WHERE code = ?",
                (code,),
            ).fetchone()
            if not row:
                return None
            if row[3] < time.time():
                conn.execute(
                    "DELETE FROM auth_codes "
                    "WHERE code = ?",
                    (code,),
                )
                conn.commit()
                return None
            return AuthCodeRecord(
                code=row[0],
                client_id=row[1],
                scopes=json.loads(row[2]),
                expires_at=row[3],
                code_challenge=row[4],
                redirect_uri=row[5],
                redirect_uri_provided_explicitly=bool(
                    row[6]
                ),
                rnc_token_encrypted=row[7],
            )
        finally:
            conn.close()

    def delete_auth_code(self, code: str):
        conn = self._conn()
        try:
            conn.execute(
                "DELETE FROM auth_codes WHERE code = ?",
                (code,),
            )
            conn.commit()
        finally:
            conn.close()

    # --- Access tokens ---

    def save_access_token(
        self, record: TokenRecord
    ):
        conn = self._conn()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO access_tokens "
                "(token, client_id, scopes, expires_at, "
                "rnc_token) VALUES (?, ?, ?, ?, ?)",
                (
                    record.token,
                    record.client_id,
                    json.dumps(record.scopes),
                    record.expires_at,
                    record.rnc_token_encrypted,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_access_token(
        self, token: str
    ) -> Optional[TokenRecord]:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT token, client_id, scopes, "
                "expires_at, rnc_token "
                "FROM access_tokens WHERE token = ?",
                (token,),
            ).fetchone()
            if not row:
                return None
            if row[3] and row[3] < time.time():
                self._delete_access_token_conn(
                    conn, row[0]
                )
                conn.commit()
                return None
            return TokenRecord(
                token=row[0],
                client_id=row[1],
                scopes=json.loads(row[2]),
                expires_at=row[3],
                rnc_token_encrypted=row[4],
            )
        finally:
            conn.close()

    # --- Refresh tokens ---

    def save_refresh_token(
        self, record: TokenRecord
    ):
        conn = self._conn()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO refresh_tokens "
                "(token, client_id, scopes, expires_at, "
                "rnc_token) VALUES (?, ?, ?, ?, ?)",
                (
                    record.token,
                    record.client_id,
                    json.dumps(record.scopes),
                    record.expires_at,
                    record.rnc_token_encrypted,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_refresh_token(
        self, token: str
    ) -> Optional[TokenRecord]:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT token, client_id, scopes, "
                "expires_at, rnc_token "
                "FROM refresh_tokens WHERE token = ?",
                (token,),
            ).fetchone()
            if not row:
                return None
            if row[3] and row[3] < time.time():
                self._delete_refresh_token_conn(
                    conn, row[0]
                )
                conn.commit()
                return None
            return TokenRecord(
                token=row[0],
                client_id=row[1],
                scopes=json.loads(row[2]),
                expires_at=row[3],
                rnc_token_encrypted=row[4],
            )
        finally:
            conn.close()

    # --- Token pairs ---

    def save_token_pair(
        self, access_token: str, refresh_token: str
    ):
        conn = self._conn()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO token_pairs "
                "(access_token, refresh_token) "
                "VALUES (?, ?)",
                (access_token, refresh_token),
            )
            conn.commit()
        finally:
            conn.close()

    # --- Revocation ---

    def revoke_access_token(self, token: str):
        conn = self._conn()
        try:
            # Find and delete associated refresh token
            row = conn.execute(
                "SELECT refresh_token FROM token_pairs "
                "WHERE access_token = ?",
                (token,),
            ).fetchone()
            if row:
                self._delete_refresh_token_conn(
                    conn, row[0]
                )
            self._delete_access_token_conn(conn, token)
            conn.commit()
        finally:
            conn.close()

    def revoke_refresh_token(self, token: str):
        conn = self._conn()
        try:
            # Find and delete associated access token
            row = conn.execute(
                "SELECT access_token FROM token_pairs "
                "WHERE refresh_token = ?",
                (token,),
            ).fetchone()
            if row:
                self._delete_access_token_conn(
                    conn, row[0]
                )
            self._delete_refresh_token_conn(conn, token)
            conn.commit()
        finally:
            conn.close()

    def _delete_access_token_conn(
        self, conn: sqlite3.Connection, token: str
    ):
        conn.execute(
            "DELETE FROM access_tokens WHERE token = ?",
            (token,),
        )
        conn.execute(
            "DELETE FROM token_pairs "
            "WHERE access_token = ?",
            (token,),
        )

    def _delete_refresh_token_conn(
        self, conn: sqlite3.Connection, token: str
    ):
        conn.execute(
            "DELETE FROM refresh_tokens WHERE token = ?",
            (token,),
        )
        conn.execute(
            "DELETE FROM token_pairs "
            "WHERE refresh_token = ?",
            (token,),
        )
