"""E2E test configuration and fixtures.

These tests connect to a real RNC MCP server and execute actual requests.
Server URL is configurable via .env.e2e file or E2E_SERVER_URL environment variable.
"""

import os
import pytest
from pathlib import Path

# Load E2E-specific environment
from dotenv import load_dotenv

# Load .env.e2e file (separate from main .env to avoid token conflicts)
env_e2e_path = Path(__file__).parent.parent.parent / ".env.e2e"
if env_e2e_path.exists():
    load_dotenv(env_e2e_path)


def pytest_configure(config):
    """Register E2E test markers."""
    config.addinivalue_line("markers", "e2e: End-to-end tests (requires running server)")


@pytest.fixture(scope="session")
def server_url():
    """Get the server URL from environment or use default."""
    return os.environ.get("E2E_SERVER_URL", "http://127.0.0.1:8000/mcp")


@pytest.fixture(scope="session")
def mcp_client(server_url):
    """Create a FastMCP client factory for the session."""
    from fastmcp import Client

    def create_client():
        return Client(server_url)

    return create_client
