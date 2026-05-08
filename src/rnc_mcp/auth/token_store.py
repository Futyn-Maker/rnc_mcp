"""Encrypted token store backed by an SQL database.

Stores OAuth tokens (access, refresh, authorization codes,
client registrations) and their mappings to RNC API tokens.
RNC tokens are encrypted at rest using Fernet symmetric
encryption.

The backend is configured by a SQLAlchemy connection URL,
so any supported dialect works (SQLite, PostgreSQL, MySQL,
...). The schema and all queries are dialect-agnostic; the
only place a dialect is consulted is upsert, where the SQLite
and PostgreSQL ``ON CONFLICT`` extensions are used when
available and a delete-then-insert fallback handles other
backends.
"""

import json
import os
import secrets
import time
from dataclasses import dataclass
from typing import Optional

from cryptography.fernet import Fernet
from sqlalchemy import (
    Column,
    Float,
    Integer,
    LargeBinary,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    delete,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import (
    insert as pg_insert,
)
from sqlalchemy.dialects.sqlite import (
    insert as sqlite_insert,
)
from sqlalchemy.engine import Engine, make_url


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


_metadata = MetaData()

_clients = Table(
    "rnc_oauth_clients",
    _metadata,
    Column("client_id", String(255), primary_key=True),
    Column("data", Text, nullable=False),
)

_auth_codes = Table(
    "rnc_oauth_auth_codes",
    _metadata,
    Column("code", String(255), primary_key=True),
    Column("client_id", String(255), nullable=False),
    Column("scopes", Text, nullable=False),
    Column("expires_at", Float, nullable=False),
    Column("code_challenge", Text, nullable=False),
    Column("redirect_uri", Text, nullable=False),
    Column(
        "redirect_uri_explicit", Integer, nullable=False
    ),
    Column("rnc_token", LargeBinary, nullable=False),
)

_access_tokens = Table(
    "rnc_oauth_access_tokens",
    _metadata,
    Column("token", String(255), primary_key=True),
    Column("client_id", String(255), nullable=False),
    Column("scopes", Text, nullable=False),
    Column("expires_at", Float, nullable=True),
    Column("rnc_token", LargeBinary, nullable=False),
)

_refresh_tokens = Table(
    "rnc_oauth_refresh_tokens",
    _metadata,
    Column("token", String(255), primary_key=True),
    Column("client_id", String(255), nullable=False),
    Column("scopes", Text, nullable=False),
    Column("expires_at", Float, nullable=True),
    Column("rnc_token", LargeBinary, nullable=False),
)

_token_pairs = Table(
    "rnc_oauth_token_pairs",
    _metadata,
    Column("access_token", String(255), primary_key=True),
    Column("refresh_token", String(255), primary_key=True),
)


def _build_engine(database_url: str) -> Engine:
    """Create an SQLAlchemy engine from a connection URL.

    For SQLite file URLs, the parent directory is created on
    demand and ``check_same_thread`` is disabled so the engine
    can be shared across the FastMCP worker threads.
    """
    url = make_url(database_url)
    connect_args: dict = {}
    if url.drivername.startswith("sqlite"):
        if url.database and url.database != ":memory:":
            parent = os.path.dirname(url.database)
            if parent:
                os.makedirs(parent, exist_ok=True)
        connect_args["check_same_thread"] = False
    return create_engine(
        database_url,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


class TokenStore:
    """Encrypted SQL-backed token store.

    All RNC API tokens are encrypted with Fernet before they
    are written. The encryption key may be supplied directly
    (``fernet_key``), pulled from the ``RNC_FERNET_KEY``
    environment variable, or — for SQLite-on-disk deployments
    only — auto-generated next to the database file.

    For non-SQLite backends an explicit key is required:
    auto-generating one would silently break decryption across
    restarts because the key would not be persisted next to a
    networked database.
    """

    def __init__(
        self,
        database_url: str = "sqlite:////tmp/oauth.db",
        fernet_key: Optional[bytes] = None,
        engine: Optional[Engine] = None,
    ):
        self._database_url = database_url
        self._engine: Engine = (
            engine if engine is not None
            else _build_engine(database_url)
        )
        self._dialect = self._engine.dialect.name
        self._pending: dict[str, PendingAuth] = {}

        if fernet_key is None:
            fernet_key = self._resolve_fernet_key(
                database_url
            )
        self._fernet = Fernet(fernet_key)

        _metadata.create_all(self._engine)

    @staticmethod
    def _resolve_fernet_key(database_url: str) -> bytes:
        """Locate or create the Fernet key.

        Order: ``RNC_FERNET_KEY`` env var → file alongside a
        SQLite database → ``RuntimeError`` for any other
        backend (auto-generation would lose the key on the
        next restart).
        """
        env_key = os.getenv("RNC_FERNET_KEY")
        if env_key:
            # Allow either bytes-text or str input. Fernet
            # validates the format on instantiation.
            return env_key.encode()

        url = make_url(database_url)
        if not url.drivername.startswith("sqlite"):
            raise RuntimeError(
                "RNC_FERNET_KEY must be set when using a "
                "non-SQLite database backend. Generate one "
                "with: python -c \"from cryptography.fernet "
                "import Fernet; print(Fernet.generate_key()"
                ".decode())\""
            )

        if url.database in (None, "", ":memory:"):
            return Fernet.generate_key()

        key_dir = os.path.dirname(url.database) or "."
        key_path = os.path.join(key_dir, ".fernet.key")
        if os.path.exists(key_path):
            with open(key_path, "rb") as f:
                return f.read()
        key = Fernet.generate_key()
        os.makedirs(key_dir, exist_ok=True)
        fd = os.open(
            key_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        try:
            os.write(fd, key)
        finally:
            os.close(fd)
        return key

    def encrypt_rnc_token(self, rnc_token: str) -> bytes:
        return self._fernet.encrypt(rnc_token.encode())

    def decrypt_rnc_token(self, encrypted: bytes) -> str:
        return self._fernet.decrypt(encrypted).decode()

    # --- Generic upsert ---

    def _upsert(
        self,
        conn,
        table: Table,
        pk_columns: list,
        values: dict,
    ) -> None:
        """Backend-agnostic INSERT-or-REPLACE."""
        pk_names = {c.name for c in pk_columns}
        update_set = {
            k: v for k, v in values.items()
            if k not in pk_names
        }
        if self._dialect == "postgresql":
            stmt = pg_insert(table).values(**values)
            if update_set:
                stmt = stmt.on_conflict_do_update(
                    index_elements=pk_columns,
                    set_=update_set,
                )
            else:
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=pk_columns,
                )
            conn.execute(stmt)
            return
        if self._dialect == "sqlite":
            stmt = sqlite_insert(table).values(**values)
            if update_set:
                stmt = stmt.on_conflict_do_update(
                    index_elements=pk_columns,
                    set_=update_set,
                )
            else:
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=pk_columns,
                )
            conn.execute(stmt)
            return
        # Generic fallback: delete by PK, then insert.
        where_clause = None
        for col in pk_columns:
            cond = col == values[col.name]
            where_clause = (
                cond if where_clause is None
                else where_clause & cond
            )
        conn.execute(delete(table).where(where_clause))
        conn.execute(insert(table).values(**values))

    # --- Clients ---

    def save_client(self, client_id: str, data: dict):
        with self._engine.begin() as conn:
            self._upsert(
                conn,
                _clients,
                [_clients.c.client_id],
                {
                    "client_id": client_id,
                    "data": json.dumps(data),
                },
            )

    def get_client(self, client_id: str) -> Optional[dict]:
        with self._engine.connect() as conn:
            row = conn.execute(
                select(_clients.c.data).where(
                    _clients.c.client_id == client_id
                )
            ).fetchone()
            return json.loads(row[0]) if row else None

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
        with self._engine.begin() as conn:
            self._upsert(
                conn,
                _auth_codes,
                [_auth_codes.c.code],
                {
                    "code": record.code,
                    "client_id": record.client_id,
                    "scopes": json.dumps(record.scopes),
                    "expires_at": record.expires_at,
                    "code_challenge": record.code_challenge,
                    "redirect_uri": record.redirect_uri,
                    "redirect_uri_explicit": int(
                        record.redirect_uri_provided_explicitly
                    ),
                    "rnc_token": (
                        record.rnc_token_encrypted
                    ),
                },
            )

    def get_auth_code(
        self, code: str
    ) -> Optional[AuthCodeRecord]:
        with self._engine.begin() as conn:
            row = conn.execute(
                select(_auth_codes).where(
                    _auth_codes.c.code == code
                )
            ).fetchone()
            if not row:
                return None
            if row.expires_at < time.time():
                conn.execute(
                    delete(_auth_codes).where(
                        _auth_codes.c.code == code
                    )
                )
                return None
            return AuthCodeRecord(
                code=row.code,
                client_id=row.client_id,
                scopes=json.loads(row.scopes),
                expires_at=row.expires_at,
                code_challenge=row.code_challenge,
                redirect_uri=row.redirect_uri,
                redirect_uri_provided_explicitly=bool(
                    row.redirect_uri_explicit
                ),
                rnc_token_encrypted=bytes(row.rnc_token),
            )

    def delete_auth_code(self, code: str):
        with self._engine.begin() as conn:
            conn.execute(
                delete(_auth_codes).where(
                    _auth_codes.c.code == code
                )
            )

    # --- Access tokens ---

    def save_access_token(self, record: TokenRecord):
        with self._engine.begin() as conn:
            self._upsert(
                conn,
                _access_tokens,
                [_access_tokens.c.token],
                {
                    "token": record.token,
                    "client_id": record.client_id,
                    "scopes": json.dumps(record.scopes),
                    "expires_at": record.expires_at,
                    "rnc_token": (
                        record.rnc_token_encrypted
                    ),
                },
            )

    def get_access_token(
        self, token: str
    ) -> Optional[TokenRecord]:
        with self._engine.begin() as conn:
            row = conn.execute(
                select(_access_tokens).where(
                    _access_tokens.c.token == token
                )
            ).fetchone()
            if not row:
                return None
            if (
                row.expires_at is not None
                and row.expires_at < time.time()
            ):
                self._delete_access_token(conn, row.token)
                return None
            return TokenRecord(
                token=row.token,
                client_id=row.client_id,
                scopes=json.loads(row.scopes),
                expires_at=(
                    int(row.expires_at)
                    if row.expires_at is not None
                    else None
                ),
                rnc_token_encrypted=bytes(row.rnc_token),
            )

    # --- Refresh tokens ---

    def save_refresh_token(self, record: TokenRecord):
        with self._engine.begin() as conn:
            self._upsert(
                conn,
                _refresh_tokens,
                [_refresh_tokens.c.token],
                {
                    "token": record.token,
                    "client_id": record.client_id,
                    "scopes": json.dumps(record.scopes),
                    "expires_at": record.expires_at,
                    "rnc_token": (
                        record.rnc_token_encrypted
                    ),
                },
            )

    def get_refresh_token(
        self, token: str
    ) -> Optional[TokenRecord]:
        with self._engine.begin() as conn:
            row = conn.execute(
                select(_refresh_tokens).where(
                    _refresh_tokens.c.token == token
                )
            ).fetchone()
            if not row:
                return None
            if (
                row.expires_at is not None
                and row.expires_at < time.time()
            ):
                self._delete_refresh_token(conn, row.token)
                return None
            return TokenRecord(
                token=row.token,
                client_id=row.client_id,
                scopes=json.loads(row.scopes),
                expires_at=(
                    int(row.expires_at)
                    if row.expires_at is not None
                    else None
                ),
                rnc_token_encrypted=bytes(row.rnc_token),
            )

    # --- Token pairs ---

    def save_token_pair(
        self, access_token: str, refresh_token: str
    ):
        with self._engine.begin() as conn:
            self._upsert(
                conn,
                _token_pairs,
                [
                    _token_pairs.c.access_token,
                    _token_pairs.c.refresh_token,
                ],
                {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                },
            )

    # --- Revocation ---

    def revoke_access_token(self, token: str):
        with self._engine.begin() as conn:
            row = conn.execute(
                select(
                    _token_pairs.c.refresh_token
                ).where(
                    _token_pairs.c.access_token == token
                )
            ).fetchone()
            if row:
                self._delete_refresh_token(
                    conn, row.refresh_token
                )
            self._delete_access_token(conn, token)

    def revoke_refresh_token(self, token: str):
        with self._engine.begin() as conn:
            row = conn.execute(
                select(
                    _token_pairs.c.access_token
                ).where(
                    _token_pairs.c.refresh_token == token
                )
            ).fetchone()
            if row:
                self._delete_access_token(
                    conn, row.access_token
                )
            self._delete_refresh_token(conn, token)

    def _delete_access_token(self, conn, token: str):
        conn.execute(
            delete(_access_tokens).where(
                _access_tokens.c.token == token
            )
        )
        conn.execute(
            delete(_token_pairs).where(
                _token_pairs.c.access_token == token
            )
        )

    def _delete_refresh_token(self, conn, token: str):
        conn.execute(
            delete(_refresh_tokens).where(
                _refresh_tokens.c.token == token
            )
        )
        conn.execute(
            delete(_token_pairs).where(
                _token_pairs.c.refresh_token == token
            )
        )
