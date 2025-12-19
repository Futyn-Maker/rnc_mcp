#!/usr/bin/env python3
"""
Main entry point for the RNC MCP Server.
This script can be run directly or via fastmcp CLI.
"""

import sys
from pathlib import Path

# Add the src directory to Python path so imports work
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# fmt: off
from rnc_mcp.mcp import mcp  # noqa: E402
# fmt: on

if __name__ == "__main__":
    mcp.run(transport="http")
