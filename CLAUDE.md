# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Model Context Protocol (MCP) server that connects LLMs to the Russian National Corpus (RNC) API. Built with FastMCP, it exposes a `concordance` tool for lexicographic searches and dynamic resources for corpus configuration.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # for testing

# Run the server
python3 main.py                      # HTTP on port 8000
fastmcp run main.py                  # stdio transport
fastmcp run                          # uses fastmcp.json config

# Run tests
pytest                               # all tests
pytest -m unit                       # unit tests only
pytest tests/unit/test_config.py    # single test file
pytest -n auto                       # parallel execution

# Coverage
pytest --cov=src/rnc_mcp --cov-report=term-missing
```

## Environment Setup

Requires `RNC_API_TOKEN` environment variable. Get token from: https://ruscorpora.ru/accounts/profile/for-devs

## Architecture

```
src/rnc_mcp/
├── mcp.py              # FastMCP server entry point, registers tool & resources
├── config.py           # Config singleton (token, base URL, corpus types)
├── schemas/schemas.py  # Pydantic models for request/response (SearchQuery, ConcordanceResponse)
├── clients/
│   ├── base.py         # CorpusClient abstract base class
│   └── rnc_client.py   # HTTP client implementation using httpx
├── services/
│   ├── rnc_builder.py  # Transforms SearchQuery → RNC API payload
│   └── rnc_formatter.py # Transforms RNC API response → ConcordanceResponse
├── resources/
│   ├── base.py         # CorpusResourceGenerator abstract base class
│   └── rnc_generator.py # Generates markdown docs for corpus config/tags
├── utils.py            # Utility decorators (measure_time for performance logging)
└── exceptions.py       # RNCError hierarchy (Config, Auth, API errors)
```

## Data Flow

1. **Tool call**: `concordance(SearchQuery)` receives Pydantic-validated query
2. **Build**: `RNCQueryBuilder.build_payload()` converts to RNC API JSON format
3. **Execute**: `RNCClient.execute_concordance()` makes HTTP POST to RNC API
4. **Format**: `RNCResponseFormatter.format_search_results()` parses response into `ConcordanceResponse`

## Logging Strategy

This project uses FastMCP's Context object for logging instead of Python's standard `logging` module. The `ctx` parameter passed to tool handlers provides:
- `ctx.info()` - Informational messages (e.g., "Searching MAIN...")
- `ctx.debug()` - Debug details (query payloads, raw responses, timing)

The `@measure_time` decorator in `utils.py` automatically logs execution time via context when `ctx` is available in function arguments.

## Key Types

- `SearchQuery`: Main input schema with corpus, tokens, subcorpus filters, pagination
- `TokenRequest`: Search token with lemma, wordform, gramm, semantic, syntax, flags, distance
- `SubcorpusFilter`: Filter by author, title, date range, gender, disambiguation mode
- `ConcordanceResponse`: Output with stats (corpus/query/subcorpus counts) and document results

## Testing

Tests use pytest-asyncio with mock fixtures. Key fixtures in `tests/conftest.py`:
- `mock_env_token`: Sets mock RNC_API_TOKEN
- `mock_rnc_client`: AsyncMock of RNCClient
- Sample queries and responses in `tests/fixtures/`

### Unit Tests

- **test_config.py**: Config validation, token retrieval, headers, RncCorpusType enum
- **test_schemas.py**: Pydantic schema validation for TokenRequest, SubcorpusFilter, SearchQuery, response models
- **test_schemas_repr.py**: Custom `__str__` representations for schemas
- **services/test_rnc_builder.py**: Token conditions, distance conditions, date ranges, subcorpus filters, full payload building
- **services/test_rnc_formatter.py**: Metadata extraction, snippet formatting, stats parsing, response structure
- **resources/test_rnc_generator.py**: Markdown generation, sorting methods, attributes, error handling
