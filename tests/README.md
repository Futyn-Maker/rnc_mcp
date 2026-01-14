# RNC MCP Test Suite

## Overview

Comprehensive pytest test suite for the RNC MCP server with **90%+ coverage goal**.

## Quick Start

### Install Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
pytest
```

### Run by Category

```bash
# Unit tests only
pytest -m unit

# E2E tests only (requires server running on localhost:8000)
pytest -m e2e

# E2E tests against remote server
E2E_SERVER_URL=http://remote-server:8000/mcp pytest -m e2e
```

### Run Specific Test Files

```bash
# Config tests
pytest tests/unit/test_config.py

# Schema validation tests
pytest tests/unit/test_schemas.py

# Query builder tests
pytest tests/unit/services/test_builder.py

# Response formatter tests
pytest tests/unit/services/test_formatter.py
```

### Parallel Execution

```bash
# Auto-detect CPU cores
pytest -n auto

# Use specific number of workers
pytest -n 4
```

### Coverage Reports

```bash
# Terminal report
pytest --cov=src/rnc_mcp --cov-report=term-missing

# HTML report (opens in browser)
pytest --cov=src/rnc_mcp --cov-report=html
# Report saved to htmlcov/index.html
```

## Directory Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── pytest.ini                     # Configuration
│
├── unit/                          # Unit tests (mocked)
│   ├── test_config.py            # Config validation
│   ├── test_schemas.py           # Pydantic schemas
│   ├── services/
│   │   ├── test_rnc_builder.py   # Query building logic
│   │   └── test_rnc_formatter.py # Response formatting
│   └── resources/
│       └── test_rnc_generator.py # Resource generation
│
├── e2e/                           # End-to-end tests (real server)
│   ├── conftest.py               # E2E configuration
│   ├── test_concordance.py       # Concordance tool tests
│   └── test_resources.py         # Resource generation tests
│
└── fixtures/                      # Test data
    ├── mock_responses.py         # Mock API responses
    └── e2e_queries.py            # Raw JSON query fixtures
```

## Markers

Tests are organized with pytest markers:

- `@pytest.mark.unit` - Unit tests (no network, mocked dependencies)
- `@pytest.mark.e2e` - End-to-end tests (requires running server)
