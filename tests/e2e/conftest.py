"""E2E test configuration and fixtures.

These tests connect to a real RNC MCP server and execute
actual requests. Server URL and RNC API token are
configured via .env.e2e file.

See .env.e2e.example for the template.
"""

import os
import pytest
from pathlib import Path

# Load E2E-specific environment
from dotenv import load_dotenv

# Load .env.e2e file (separate from main .env)
env_e2e_path = (
    Path(__file__).parent.parent.parent / ".env.e2e"
)
if env_e2e_path.exists():
    load_dotenv(env_e2e_path)


def pytest_configure(config):
    """Register E2E test markers."""
    config.addinivalue_line(
        "markers",
        "e2e: End-to-end tests (requires running "
        "server)",
    )


@pytest.fixture(scope="session")
def server_url():
    """Get the server URL from environment or use
    default."""
    return os.environ.get(
        "E2E_SERVER_URL",
        "http://127.0.0.1:8000/mcp",
    )


@pytest.fixture(scope="session")
def e2e_token():
    """Get the RNC API token for E2E tests from
    .env.e2e. Tests are skipped if no token is
    available."""
    token = os.environ.get("RNC_API_TOKEN")
    if not token:
        pytest.skip(
            "RNC_API_TOKEN not set in .env.e2e — "
            "skipping E2E tests"
        )
    return token


@pytest.fixture(scope="session")
def mcp_client(server_url, e2e_token):
    """Create a FastMCP client factory for the session.

    The client authenticates with the user's RNC API
    token via bearer auth.
    """
    from fastmcp import Client

    def create_client():
        return Client(server_url, auth=e2e_token)

    return create_client
