#!/usr/bin/env python3
"""
Main entry point for the RNC MCP Server.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    from rnc_mcp.mcp import mcp
    mcp.run(transport="http")
