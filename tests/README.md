# RNC MCP Test Suite

## Overview

Comprehensive pytest test suite for the RNC MCP server with **90%+ coverage goal** and professional organization.

## Test Results

Comprehensive test suite covering:
- **Test Categories**: Unit, Integration, E2E
- **Coverage Goal**: 90%+ overall, 100% for critical paths

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
# Unit tests only (no network)
pytest -m unit

# Integration tests (mocked HTTP)
pytest -m integration

# E2E tests (real API - requires RNC_API_TOKEN)
pytest -m e2e

# Run without E2E
pytest -m "not e2e"
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

# HTTP client tests
pytest tests/integration/test_client.py
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
├── unit/                          # Unit tests (isolated, mocked)
│   ├── test_config.py            # Config validation
│   ├── test_schemas.py           # Pydantic schemas
│   ├── services/
│   │   ├── test_builder.py       # Query building logic
│   │   └── test_formatter.py     # Response formatting
│   └── resources/
│       └── test_generator.py     # Resource generation
│
├── integration/                   # Integration tests (mocked HTTP)
│   ├── test_client.py            # RNCClient HTTP layer
│   └── test_mcp_tools.py         # MCP tool integration
│
├── e2e/                          # End-to-end (real API calls)
│   ├── test_concordance_e2e.py   # Full workflows
│   └── test_resources_e2e.py     # Resource endpoints
│
├── fixtures/                      # Test data
│   ├── mock_responses.py         # Mock API responses
│   └── sample_queries.py         # Sample queries
│
└── utils/                        # Test utilities
    └── assertions.py             # Custom assertions
```

## Test Coverage

### Critical Components (100% Goal)

- [src/rnc_mcp/config.py](../src/rnc_mcp/config.py) - Configuration
- [src/rnc_mcp/client.py](../src/rnc_mcp/client.py) - HTTP client
- [src/rnc_mcp/services/builder.py](../src/rnc_mcp/services/builder.py) - Query builder
- [src/rnc_mcp/services/formatter.py](../src/rnc_mcp/services/formatter.py) - Response formatter

### What's Tested

✅ **Config Management** (10 tests)
- Token validation
- Environment variable loading
- Headers construction
- Corpus type enumeration

✅ **Schema Validation** (40+ tests)
- TokenRequest validation
- DateFilter validation
- SubcorpusFilter validation
- SearchQuery validation
- Response schemas
- Edge cases (negative values, empty fields)

✅ **Query Building** (40+ tests)
- Token condition building (lemma, wordform, gramm, semantic, syntax, flags)
- Distance conditions
- Date transformations
- Subcorpus filtering
- Gender translation
- Pagination strategies

✅ **Response Formatting** (25+ tests)
- Metadata extraction
- Snippet highlighting
- Stats parsing
- Nested structure traversal
- Empty result handling

✅ **HTTP Client** (20+ tests)
- Concordance execution
- Corpus configuration
- Attributes retrieval
- Error handling (401, 404, 500, timeouts)
- Authorization headers

✅ **Resource Generation** (13 tests)
- Markdown generation
- Sorting methods
- Attribute formatting
- Graceful error handling

## Environment Setup

### Required Environment Variables

```bash
# For E2E tests (optional - E2E tests skip if not set)
export RNC_API_TOKEN="your_token_here"

# Or use .env file
cp .env.example .env
# Edit .env and set RNC_API_TOKEN
```

### Optional: Create .env File

```bash
echo "RNC_API_TOKEN=your_token_here" > .env
```

## Markers

Tests are organized with pytest markers:

- `@pytest.mark.unit` - Unit tests (no network, fast)
- `@pytest.mark.integration` - Integration tests (mocked HTTP)
- `@pytest.mark.e2e` - End-to-end tests (real API)
- `@pytest.mark.slow` - Tests that take significant time

## Fixtures

### Environment Fixtures

- `real_api_token` - Real token for E2E (skips if missing)
- `mock_env_token` - Mocked token for unit tests
- `clear_env_token` - Clears token for testing errors

### Client Fixtures

- `mock_rnc_client` - Mocked RNCClient with AsyncMock
- `real_rnc_client` - Real client for integration tests

### Response Fixtures

- `mock_concordance_response` - Success response
- `mock_concordance_empty` - Empty results
- `mock_corpus_config_response` - Config data
- `mock_attributes_response` - Attributes data

### Query Fixtures

- `simple_search_query` - Basic lemma search
- `complex_search_query` - Full-featured query
- `statistics_only_query` - return_examples=False

## Next Steps

### To Fix Failing Tests

1. **Adjust payload structure tests** to match actual RNCQueryBuilder implementation
2. **Update metadata extraction tests** to match actual precedence logic
3. **Fix snippet highlighting expectations** to match first/last wrapping
4. **Update resource generation expectations** for actual header names

### To Improve Coverage

1. Add MCP tool integration tests
2. Add more E2E test scenarios
3. Test error recovery paths
4. Add performance benchmarks

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure tests pass: `pytest -v`
3. Check coverage: `pytest --cov`
4. Run all markers: `pytest -m "unit and integration"`

## Troubleshooting

### Import Errors

If you see import errors, ensure you're in the project root:

```bash
cd /path/to/rnc_mcp
pytest
```

### E2E Tests Skipped

E2E tests require `RNC_API_TOKEN` environment variable:

```bash
export RNC_API_TOKEN="your_token"
pytest -m e2e
```

### Slow Tests

Run only fast tests:

```bash
pytest -m "not slow and not e2e"
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [respx (HTTP mocking)](https://lundberg.github.io/respx/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
