"""Shared fixtures and pytest configuration for RNC MCP tests."""

import pytest
import sys
from unittest.mock import Mock, AsyncMock
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# fmt: off
from rnc_mcp.clients.rnc_client import RNCClient  # noqa: E402
from rnc_mcp.config import Config  # noqa: E402
from tests.fixtures.mock_responses import (
    CONCORDANCE_SUCCESS,
    CONCORDANCE_EMPTY,
    CORPUS_CONFIG_MAIN,
    ATTRIBUTES_GRAMMAR,
)  # noqa: E402
from tests.fixtures.sample_queries import (
    SIMPLE_LEMMA_QUERY,
    COMPLEX_QUERY_WITH_SUBCORPUS,
    STATISTICS_ONLY_QUERY,
)  # noqa: E402
# fmt: on

# ==============================================================================
# Environment Fixtures
# ==============================================================================


@pytest.fixture
def mock_env_token(monkeypatch):
    """Mock environment variable for unit tests."""
    token = "mock_token_12345"
    monkeypatch.setenv("RNC_API_TOKEN", token)
    # Reset the Config cached token
    Config._RNC_TOKEN = token
    yield token
    # Cleanup
    Config._RNC_TOKEN = None


@pytest.fixture
def clear_env_token(monkeypatch):
    """Clear RNC_API_TOKEN for testing missing token."""
    monkeypatch.delenv("RNC_API_TOKEN", raising=False)
    # Reset cached token
    Config._RNC_TOKEN = None
    yield
    # Cleanup will be handled by monkeypatch

# ==============================================================================
# Client Fixtures
# ==============================================================================


@pytest.fixture
def mock_rnc_client():
    """Mock RNCClient with AsyncMock methods."""
    client = Mock(spec=RNCClient)
    client.execute_concordance = AsyncMock()
    client.get_corpus_config = AsyncMock()
    client.get_attributes = AsyncMock()
    return client

# ==============================================================================
# Mock Response Fixtures
# ==============================================================================


@pytest.fixture
def mock_concordance_response():
    """Sample RNC API concordance response."""
    return CONCORDANCE_SUCCESS.copy()


@pytest.fixture
def mock_concordance_empty():
    """Empty concordance response."""
    return CONCORDANCE_EMPTY.copy()


@pytest.fixture
def mock_corpus_config_response():
    """Sample corpus config response."""
    return CORPUS_CONFIG_MAIN.copy()


@pytest.fixture
def mock_attributes_response():
    """Sample attributes response."""
    return ATTRIBUTES_GRAMMAR.copy()


# ==============================================================================
# Query Fixtures
# ==============================================================================

@pytest.fixture
def simple_search_query():
    """Minimal valid SearchQuery."""
    return SIMPLE_LEMMA_QUERY


@pytest.fixture
def complex_search_query():
    """SearchQuery with all features."""
    return COMPLEX_QUERY_WITH_SUBCORPUS


@pytest.fixture
def statistics_only_query():
    """SearchQuery with return_examples=False."""
    return STATISTICS_ONLY_QUERY


# ==============================================================================
# Pytest Hooks and Configuration
# ==============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (no network)"
    )


# ==============================================================================
# Utility Fixtures
# ==============================================================================

@pytest.fixture
def temp_env_file(tmp_path, monkeypatch):
    """Create a temporary .env file for testing."""
    env_file = tmp_path / ".env"
    env_file.write_text("RNC_API_TOKEN=test_token_from_env\n")
    monkeypatch.chdir(tmp_path)
    return env_file


@pytest.fixture(autouse=True)
def reset_config():
    """Reset Config singleton between tests."""
    yield
    # Reset cached token after each test
    Config._RNC_TOKEN = None
