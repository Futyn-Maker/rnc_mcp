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

Optional variables for multi-page fetching:
- `RNC_PAGE_DELAY` — delay in seconds between page requests (default: `0.5`)
- `RNC_MAX_RETRIES` — consecutive failures before aborting multi-page fetch (default: `3`)

## Architecture

```
src/rnc_mcp/
├── mcp.py              # FastMCP server entry point, registers tool & resources, multi-page collection
├── config.py           # Config singleton (token, base URL, corpus types, page delay, max retries)
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

### Single-page (default)

1. **Tool call**: `concordance(SearchQuery)` receives Pydantic-validated query
2. **Build**: `RNCQueryBuilder.build_payload()` converts to RNC API JSON format
3. **Execute**: `RNCClient.execute_concordance()` makes HTTP POST to RNC API
4. **Format**: `RNCResponseFormatter.format_search_results()` parses response into `ConcordanceResponse`

### Multi-page (when `max_examples` is set)

1. **Tool call**: `concordance(SearchQuery)` detects `max_examples` is set and delegates to `_collect_examples()`
2. **Build**: `RNCQueryBuilder.build_payload()` builds the base payload; `docsPerPage` is overridden to 50, `snippetsPerDoc` to 10
3. **Loop**: For each page starting from `query.page`:
   - **Execute**: `RNCClient.execute_concordance()` fetches one page
   - **Format**: `RNCResponseFormatter.format_search_results()` parses the page
   - **Accumulate**: Documents are appended to results; total examples (snippets) are counted
   - **Trim**: If the last document pushes total over `max_examples`, its examples list is truncated
   - **Stop conditions**: `max_examples` reached, all pages exhausted, or `RNC_MAX_RETRIES` consecutive failures
   - **Retry**: On error, the same page is retried up to `RNC_MAX_RETRIES` times; counter resets on success
   - **Delay**: `RNC_PAGE_DELAY` seconds between requests
4. **Return**: Single `ConcordanceResponse` with merged results and stats from the first page; `last_page_fetched` indicates the last successfully fetched page

The RNC API hard-caps `docsPerPage` at 50; requesting more still returns 50.

## Logging Strategy

This project uses FastMCP's Context object for logging instead of Python's standard `logging` module. The `ctx` parameter passed to tool handlers provides:
- `ctx.info()` - Informational messages (e.g., "Searching MAIN...")
- `ctx.debug()` - Debug details (query payloads, raw responses, timing)

The `@measure_time` decorator in `utils.py` automatically logs execution time via context when `ctx` is available in function arguments.

## Key Types

- `SearchQuery`: Main input schema with corpus, tokens, subcorpus filters, pagination, `max_examples` for multi-page collection
- `TokenRequest`: Search token with lemma, wordform, gramm, semantic, syntax, flags, distance
- `SubcorpusFilter`: Filter by author, title, date range, gender, disambiguation mode
- `ConcordanceResponse`: Output with stats (corpus/query/subcorpus counts, `last_page_fetched`) and document results

## Testing

Tests use pytest-asyncio with mock fixtures. Key fixtures in `tests/conftest.py`:
- `mock_env_token`: Sets mock RNC_API_TOKEN
- `mock_rnc_client`: AsyncMock of RNCClient
- Sample queries and responses in `tests/fixtures/`

### Unit Tests

- **test_config.py**: Config validation, token retrieval, headers, RncCorpusType enum
- **test_schemas.py**: Pydantic schema validation for TokenRequest, SubcorpusFilter, SearchQuery, response models
- **test_schemas_repr.py**: Custom `__str__` representations for schemas
- **test_collect_examples.py**: Multi-page collection logic (pagination, trimming, retry, exhaustion, payload overrides)
- **services/test_rnc_builder.py**: Token conditions, distance conditions, date ranges, subcorpus filters, full payload building
- **services/test_rnc_formatter.py**: Metadata extraction, snippet formatting, stats parsing, response structure
- **resources/test_rnc_generator.py**: Markdown generation, sorting methods, attributes, error handling

### E2E Tests

E2E tests connect to a running server and execute real requests. They test the server as a "black box" without importing any source code.

```bash
# Run E2E tests (requires server running on localhost:8000)
pytest -m e2e

# Run E2E tests against remote server
E2E_SERVER_URL=http://remote-server:8000/mcp pytest -m e2e
```

Configuration via `.env.e2e` file (separate from main `.env`):
```
E2E_SERVER_URL=http://127.0.0.1:8000/mcp
```

E2E test files:
- **tests/e2e/test_concordance.py**: Concordance tool tests for all 16 corpora + multi-page collection (500 examples)
- **tests/e2e/test_resources.py**: Resource generation tests for all corpora
- **tests/fixtures/e2e_queries.py**: Raw JSON query fixtures (including `MULTI_PAGE_500_EXAMPLES`)

### Corpus Status (E2E Test Results)

Based on E2E tests, here is the current status of each corpus. All corpora support resource generation. Concordance query support varies:

| Corpus | Simple Query | Subcorpus Filter | Notes |
|--------|--------------|------------------|-------|
| MAIN | ✓ | ✓ | Fully working |
| PAPER | ✓ | ✓ | Fully working |
| POETIC | ✓ | ✓ | Fully working |
| SPOKEN | ✓ | ✓ | Fully working |
| DIALECT | ✓ | ✗ 500 | `author_gender` filter fails |
| SCHOOL | ✓ | ✓ | Fully working |
| SYNTAX | ✗ 500 | ✗ 500 | Simple lemma queries fail |
| MULTI | ✗ 500 | ✓ | Simple fails, `author_gender` works |
| ACCENT | ✓ | ✓ | Fully working |
| MULTIPARC | ✓ | ✓ | Fully working |
| KIDS | ✓ | ✗ 500 | `author_gender` filter fails |
| CLASSICS | ✓ | ✓ | Fully working |
| BLOGS | ✓ | ✓ | Fully working |
| PANCHRON | ✓ | ✓ | Fully working |
| OLD_RUS | ✓ | ✓ | Fully working |
| MID_RUS | ✓ | ✓ | Fully working |

**Fully working corpora (12):** MAIN, PAPER, POETIC, SPOKEN, SCHOOL, ACCENT, MULTIPARC, CLASSICS, BLOGS, PANCHRON, OLD_RUS, MID_RUS

**Partially working (4):**
- DIALECT: Simple queries work, `author_gender` filter fails with 500
- KIDS: Simple queries work, `author_gender` filter fails with 500
- SYNTAX: Simple lemma queries fail with 500, but syntax tag queries on MAIN corpus work
- MULTI: Simple queries fail with 500, but queries with `author_gender` filter work

### Manual Testing with FastMCP Client

For manual testing against a running server, use the FastMCP client library. Start the server first with `python3 main.py`.

**List available tools and resources:**

```python
import asyncio
from fastmcp import Client

async def list_tools():
    async with Client("http://127.0.0.1:8000/mcp") as client:
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

async def list_resources():
    async with Client("http://127.0.0.1:8000/mcp") as client:
        resources = await client.list_resources()
        print("Available resources:")
        for resource in resources:
            print(f"  - {resource.name}: {resource.uri}")

asyncio.run(list_tools())
asyncio.run(list_resources())
```

**Read a resource (returns a list):**

```python
async def get_corpus_info():
    async with Client("http://127.0.0.1:8000/mcp") as client:
        data = await client.read_resource("rnc://MAIN/info")
        resource = data[0]  # Returns a list, get first element
        print(resource.text)

asyncio.run(get_corpus_info())
```

**Call the concordance tool:**

```python
async def simple_search():
    async with Client("http://127.0.0.1:8000/mcp") as client:
        # Tool arguments must wrap query in {"query": {...}}
        result = await client.call_tool(
            "concordance",
            {
                "query": {
                    "corpus": "MAIN",
                    "tokens": [{"lemma": "дом"}]
                }
            }
        )
        # Use structured_content for JSON, or result.data for Pydantic models
        print(result.structured_content)

asyncio.run(simple_search())
```

**Collect many examples across pages:**

```python
async def multi_page_search():
    async with Client("http://127.0.0.1:8000/mcp") as client:
        result = await client.call_tool(
            "concordance",
            {
                "query": {
                    "corpus": "MAIN",
                    "tokens": [{"lemma": "дом"}],
                    "max_examples": 200
                }
            }
        )
        data = result.structured_content
        total = sum(len(d["examples"]) for d in data["results"])
        print(f"Collected {total} examples")
        print(f"Last page fetched: {data['stats']['last_page_fetched']}")
        print(f"Total pages available: {data['stats']['total_pages_available']}")

asyncio.run(multi_page_search())
```

**Result object attributes:**
- `result.structured_content` - JSON dict (recommended for easy access)
- `result.data` - Pydantic models created by FastMCP (nested `Root` objects)
- `result.content` - Raw content list
- `result.is_error` - Boolean indicating if the call failed

## Adding New Corpora

To add a new corpus to the wrapper:

1. **Find the corpus type** in [RNC OpenAPI spec](https://ruscorpora.github.io/public-api/openapi/index.html) — look for `corpusType` enum values

2. **Add to config** in `src/rnc_mcp/config.py`:
   ```python
   RNC_CORPORA: Dict[str, str] = {
       # ... existing corpora ...
       "NEW_TYPE": "Human-readable description",
   }
   ```

3. **Update unit tests** in `tests/unit/test_config.py` — increment the corpus count in two tests:
   - `test_corpora_has_N_entries`: update the expected count in `assert len(Config.RNC_CORPORA) == N`
   - `test_enum_has_all_N_corpus_types`: update the expected count in `assert len(corpus_types) == N`

4. **Add E2E test queries** in `tests/fixtures/e2e_queries.py`:
   - Add corpus to `ALL_CORPUS_TYPES` list
   - Create `NEW_TYPE_SIMPLE` and `NEW_TYPE_WITH_DATE` (or other filter) queries
   - Add entries to `SIMPLE_QUERIES` and `SUBCORPUS_QUERIES` dicts

5. **Run tests** to verify functionality:
   ```bash
   python3 main.py &                    # start server
   pytest -m e2e -k "NEW_TYPE" -v       # run corpus-specific tests
   ```

6. **Update documentation** — add corpus status to the table in `CLAUDE.md`
