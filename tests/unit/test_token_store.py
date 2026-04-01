"""Unit tests for the token store."""

import time

import pytest
from cryptography.fernet import Fernet

from rnc_mcp.auth.token_store import (
    AuthCodeRecord,
    TokenRecord,
    TokenStore,
    AUTH_CODE_EXPIRY,
)


@pytest.fixture
def fernet_key():
    return Fernet.generate_key()


@pytest.fixture
def store(tmp_path, fernet_key):
    db_path = str(tmp_path / "test_oauth.db")
    return TokenStore(
        db_path=db_path, fernet_key=fernet_key
    )


@pytest.mark.unit
class TestTokenStoreEncryption:
    """Tests for Fernet encryption of RNC tokens."""

    def test_encrypt_decrypt_roundtrip(self, store):
        """Encrypted token can be decrypted back."""
        original = "my_secret_rnc_token"
        encrypted = store.encrypt_rnc_token(original)
        assert encrypted != original.encode()
        decrypted = store.decrypt_rnc_token(encrypted)
        assert decrypted == original

    def test_different_encryptions_differ(self, store):
        """Same plaintext produces different ciphertexts
        (Fernet uses random IV)."""
        token = "same_token"
        enc1 = store.encrypt_rnc_token(token)
        enc2 = store.encrypt_rnc_token(token)
        assert enc1 != enc2

    def test_key_persistence(self, tmp_path):
        """Fernet key is persisted to disk and reused."""
        db_path = str(tmp_path / "persist.db")
        store1 = TokenStore(db_path=db_path)
        encrypted = store1.encrypt_rnc_token("secret")
        store2 = TokenStore(db_path=db_path)
        assert store2.decrypt_rnc_token(encrypted) == (
            "secret"
        )


@pytest.mark.unit
class TestTokenStoreClients:
    """Tests for client registration storage."""

    def test_save_and_get_client(self, store):
        data = {
            "client_id": "test-client",
            "redirect_uris": ["http://localhost/cb"],
        }
        store.save_client("test-client", data)
        result = store.get_client("test-client")
        assert result == data

    def test_get_nonexistent_client(self, store):
        assert store.get_client("nope") is None

    def test_update_client(self, store):
        store.save_client("c1", {"client_id": "c1"})
        store.save_client(
            "c1", {"client_id": "c1", "new": True}
        )
        result = store.get_client("c1")
        assert result["new"] is True


@pytest.mark.unit
class TestTokenStoreAuthCodes:
    """Tests for authorization code storage."""

    def _make_code(self, store, code="test_code"):
        return AuthCodeRecord(
            code=code,
            client_id="client1",
            scopes=["rnc:search"],
            expires_at=time.time() + AUTH_CODE_EXPIRY,
            code_challenge="challenge123",
            redirect_uri="http://localhost/cb",
            redirect_uri_provided_explicitly=True,
            rnc_token_encrypted=store.encrypt_rnc_token(
                "rnc_token"
            ),
        )

    def test_save_and_get_auth_code(self, store):
        record = self._make_code(store)
        store.save_auth_code(record)
        result = store.get_auth_code("test_code")
        assert result is not None
        assert result.code == "test_code"
        assert result.client_id == "client1"

    def test_expired_auth_code_returns_none(self, store):
        record = self._make_code(store)
        record.expires_at = time.time() - 1
        store.save_auth_code(record)
        assert store.get_auth_code("test_code") is None

    def test_delete_auth_code(self, store):
        record = self._make_code(store)
        store.save_auth_code(record)
        store.delete_auth_code("test_code")
        assert store.get_auth_code("test_code") is None

    def test_rnc_token_encrypted_in_db(self, store):
        record = self._make_code(store)
        store.save_auth_code(record)
        result = store.get_auth_code("test_code")
        decrypted = store.decrypt_rnc_token(
            result.rnc_token_encrypted
        )
        assert decrypted == "rnc_token"


@pytest.mark.unit
class TestTokenStoreAccessTokens:
    """Tests for access token storage."""

    def _make_token(self, store, token="at_123"):
        return TokenRecord(
            token=token,
            client_id="client1",
            scopes=["rnc:search"],
            expires_at=int(time.time() + 3600),
            rnc_token_encrypted=store.encrypt_rnc_token(
                "user_rnc_token"
            ),
        )

    def test_save_and_get_access_token(self, store):
        record = self._make_token(store)
        store.save_access_token(record)
        result = store.get_access_token("at_123")
        assert result is not None
        assert result.token == "at_123"
        assert result.client_id == "client1"

    def test_expired_access_token_returns_none(
        self, store
    ):
        record = self._make_token(store)
        record.expires_at = int(time.time() - 1)
        store.save_access_token(record)
        assert store.get_access_token("at_123") is None

    def test_nonexistent_access_token(self, store):
        assert store.get_access_token("nope") is None

    def test_rnc_token_recoverable(self, store):
        record = self._make_token(store)
        store.save_access_token(record)
        result = store.get_access_token("at_123")
        decrypted = store.decrypt_rnc_token(
            result.rnc_token_encrypted
        )
        assert decrypted == "user_rnc_token"


@pytest.mark.unit
class TestTokenStoreRefreshTokens:
    """Tests for refresh token storage."""

    def _make_token(self, store, token="rt_123"):
        return TokenRecord(
            token=token,
            client_id="client1",
            scopes=["rnc:search"],
            expires_at=None,
            rnc_token_encrypted=store.encrypt_rnc_token(
                "user_rnc_token"
            ),
        )

    def test_save_and_get_refresh_token(self, store):
        record = self._make_token(store)
        store.save_refresh_token(record)
        result = store.get_refresh_token("rt_123")
        assert result is not None
        assert result.expires_at is None

    def test_nonexistent_refresh_token(self, store):
        assert store.get_refresh_token("nope") is None


@pytest.mark.unit
class TestTokenStoreRevocation:
    """Tests for token revocation."""

    def _make_pair(self, store):
        at = TokenRecord(
            token="at_1",
            client_id="c1",
            scopes=["rnc:search"],
            expires_at=int(time.time() + 3600),
            rnc_token_encrypted=store.encrypt_rnc_token(
                "rnc"
            ),
        )
        rt = TokenRecord(
            token="rt_1",
            client_id="c1",
            scopes=["rnc:search"],
            expires_at=None,
            rnc_token_encrypted=store.encrypt_rnc_token(
                "rnc"
            ),
        )
        store.save_access_token(at)
        store.save_refresh_token(rt)
        store.save_token_pair("at_1", "rt_1")
        return at, rt

    def test_revoke_access_removes_both(self, store):
        self._make_pair(store)
        store.revoke_access_token("at_1")
        assert store.get_access_token("at_1") is None
        assert store.get_refresh_token("rt_1") is None

    def test_revoke_refresh_removes_both(self, store):
        self._make_pair(store)
        store.revoke_refresh_token("rt_1")
        assert store.get_access_token("at_1") is None
        assert store.get_refresh_token("rt_1") is None

    def test_revoke_nonexistent_token_ok(self, store):
        """Revoking nonexistent token doesn't error."""
        store.revoke_access_token("nope")
        store.revoke_refresh_token("nope")


@pytest.mark.unit
class TestTokenStorePendingAuth:
    """Tests for pending authorization requests."""

    def test_create_and_get_pending(self, store):
        txn = store.create_pending_auth(
            client_id="c1",
            redirect_uri="http://localhost/cb",
            redirect_uri_provided_explicitly=True,
            state="abc",
            code_challenge="challenge",
            scopes=["rnc:search"],
        )
        pending = store.get_pending_auth(txn)
        assert pending is not None
        assert pending.client_id == "c1"
        assert pending.state == "abc"

    def test_consume_pending(self, store):
        txn = store.create_pending_auth(
            client_id="c1",
            redirect_uri="http://localhost/cb",
            redirect_uri_provided_explicitly=True,
            state="abc",
            code_challenge="challenge",
            scopes=[],
        )
        pending = store.consume_pending_auth(txn)
        assert pending is not None
        # Second consume returns None
        assert store.consume_pending_auth(txn) is None

    def test_expired_pending_returns_none(self, store):
        txn = store.create_pending_auth(
            client_id="c1",
            redirect_uri="http://localhost/cb",
            redirect_uri_provided_explicitly=True,
            state="abc",
            code_challenge="challenge",
            scopes=[],
        )
        # Expire it
        store._pending[txn].expires_at = time.time() - 1
        assert store.get_pending_auth(txn) is None


@pytest.mark.unit
class TestTokenStorePersistence:
    """Tests for SQLite persistence across instances."""

    def test_data_survives_restart(
        self, tmp_path, fernet_key
    ):
        db_path = str(tmp_path / "persist.db")
        store1 = TokenStore(
            db_path=db_path, fernet_key=fernet_key
        )
        store1.save_client("c1", {"client_id": "c1"})
        record = TokenRecord(
            token="at_persist",
            client_id="c1",
            scopes=["rnc:search"],
            expires_at=int(time.time() + 3600),
            rnc_token_encrypted=(
                store1.encrypt_rnc_token("secret")
            ),
        )
        store1.save_access_token(record)

        # New store instance, same DB + key
        store2 = TokenStore(
            db_path=db_path, fernet_key=fernet_key
        )
        assert store2.get_client("c1") is not None
        result = store2.get_access_token("at_persist")
        assert result is not None
        assert (
            store2.decrypt_rnc_token(
                result.rnc_token_encrypted
            )
            == "secret"
        )
