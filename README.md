# Russian National Corpus MCP Server

This is a Model Context Protocol (MCP) server that connects Large Language Models (LLMs) to the **Russian National Corpus (RNC)**. It acts as a bridge, allowing MCP clients powered by AI (like Claude or ChatGPT, or custom services) to perform complex lexicographic searches and retrieve linguistic data via the [RNC Public API](https://ruscorpora.github.io/public-api).

The server abstracts the complexity of the raw RNC API, providing a streamlined toolset for concordance searches and dynamic resource generation without requiring custom code integration for the end user.

## Features

* **Zero-Code Integration:** Connects seamlessly to any MCP-compliant client (Claude Web or Desktop, IDEs, etc.).
* **Concordance Search:** Powerful querying capabilities including lemmas, exact word forms, grammar tags, semantic tags, and syntactic roles.
* **Subcorpus Filtering:** Filter results by author, title, date range, gender, and disambiguation mode.
* **Dynamic Resources:** Automatically generates context regarding available corpus configurations and tagsets.

## Configuration & Setup

### 1. Prerequisites

You must have a valid API token from the Russian National Corpus.

* **Get a Token:** [https://ruscorpora.ru/accounts/profile/for-devs](https://ruscorpora.ru/accounts/profile/for-devs)

### 2. Environment Variables

Create a `.env` file in the project root (you can copy `.env.example` as a template).

```bash
RNC_API_TOKEN=your_token_here
```

### 3. Running the Server

First, install the dependencies:

```bash
pip install -r requirements.txt
```

There are three ways to run the server:

**Method 1: Direct Python Execution**

Runs the server using the default HTTP transport on port 8000.

```bash
python3 main.py
```

**Method 2: FastMCP CLI**

Allows for flexible transport configuration.

```bash
# Standard Input/Output (stdio) - best for IDEs/Claude Desktop
fastmcp run main.py

# HTTP Transport with custom port
fastmcp run main.py --transport http --port 8080
```

**Method 3: FastMCP Configuration (Recommended)**

If you have `uv` installed, this method uses the `fastmcp.json` configuration file for a reproducible environment.

```bash
fastmcp run
```

## Tools

The server exposes a single, powerful tool for interacting with the corpus.

### `concordance`

Performs a lexicographic search in the corpus. It builds a complex query payload, handles pagination, and formats the results.

**Input Schema:**

The tool expects a `query` wrapper object containing the search parameters:

```json
{
  "query": {
    "corpus": "MAIN",
    "tokens": [...],
    "subcorpus": {...},
    ...
  }
}
```

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `corpus` | string | `"MAIN"` | Corpus to search. Options: `MAIN`, `PAPER`, `POETIC`, `SPOKEN`, `DIALECT`, `SCHOOL`, `SYNTAX`, `MULTI`, `ACCENT`, `MULTIPARC`, `KIDS`, `CLASSICS`, `BLOGS` |
| `tokens` | array | *required* | Sequence of token conditions to search for (see below) |
| `subcorpus` | object | `null` | Subcorpus filtering options (see below) |
| `sort` | string | `null` | Sort order (e.g., `"grcreated"` for creation date) |
| `page` | integer | `0` | Page number (0-indexed) |
| `per_page` | integer | `10` | Documents per page |
| `return_examples` | boolean | `true` | If `false`, returns only statistics without text snippets |

**Token parameters** (each token in the `tokens` array):

| Parameter | Type | Description |
|-----------|------|-------------|
| `lemma` | string | Dictionary form of the word (e.g., `"бежать"`) |
| `wordform` | string | Exact word form (e.g., `"бежал"`) |
| `gramm` | string | Grammar tags (e.g., `"S"` for noun, `"V"` for verb) |
| `semantic` | string | Semantic tags (e.g., `"t:hum"` for human) |
| `syntax` | string | Syntactic tags (e.g., `"clause_main"`) |
| `flags` | string | Additional feature flags (e.g., `"lexred"`) |
| `dist_min` | integer | Minimum distance from previous token (default: `1`) |
| `dist_max` | integer | Maximum distance from previous token (default: `1`) |

**Subcorpus filter parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `author` | string | Filter by author name (e.g., `"Пушкин"`) |
| `title` | string | Filter by document title |
| `date_range` | object | Filter by date: `{"start_year": 1820, "end_year": 1837}` |
| `author_gender` | string | Filter by author gender: `"male"` or `"female"` |
| `author_birthyear_range` | object | Filter by author's birth year range |
| `disambiguation` | string | Homonymy disambiguation mode: `"auto"` or `"manual"` |

**Example input:**

```json
{
  "query": {
    "corpus": "MAIN",
    "tokens": [
      { "lemma": "бежать", "gramm": "V" },
      { "wordform": "быстро", "dist_min": 1, "dist_max": 3 }
    ],
    "subcorpus": {
      "author": "Пушкин",
      "date_range": { "start_year": 1820, "end_year": 1837 }
    },
    "page": 0,
    "per_page": 10
  }
}
```

**Output Schema:**

Returns a `ConcordanceResponse` object with statistics and document matches:

```json
{
  "stats": {
    "corpusStats": {
      "textCount": 133554,
      "wordUsageCount": 389471513
    },
    "subcorpStats": null,
    "queryStats": {
      "textCount": 38728,
      "wordUsageCount": 399705
    },
    "total_pages_available": 3873
  },
  "results": [
    {
      "metadata": {
        "title": "Document Title",
        "author": "Author Name",
        "year": "1825"
      },
      "examples": [
        "Text snippet with **highlighted** search terms.",
        "Another **matching** snippet from the same document."
      ]
    }
  ]
}
```

**Stats fields:**

| Field | Description |
|-------|-------------|
| `corpusStats.textCount` | Total number of documents in the corpus |
| `corpusStats.wordUsageCount` | Total word count in the corpus |
| `subcorpStats` | Statistics for the filtered subcorpus (if subcorpus filter applied) |
| `queryStats.textCount` | Number of documents matching the query |
| `queryStats.wordUsageCount` | Number of word occurrences matching the query |
| `total_pages_available` | Total number of pages available for pagination |

**Results fields:**

| Field | Description |
|-------|-------------|
| `metadata.title` | Document title |
| `metadata.author` | Author name (may be `null`) |
| `metadata.year` | Publication year (may be `null`) |
| `examples` | Array of text snippets with `**highlighted**` search terms |

## Resources

The server provides dynamic resources that describe the configuration and available attributes for each corpus type. These are generated on-the-fly by querying the RNC API.

**URI Pattern:** `rnc://{CORPUS_CODE}/info`

**Example URIs:**

* `rnc://MAIN/info`
* `rnc://POETIC/info`

Reading these resources provides Markdown-formatted documentation of available sorting methods, grammar tags, and semantic categories specific to that corpus.

## Programmatic Usage

You can use the `fastmcp` client library to interact with this server programmatically using Python. This is useful for testing queries or building custom applications.

### Listing Available Tools and Resources

Before making queries, you can discover what tools and resources the server provides.

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

if __name__ == "__main__":
    asyncio.run(list_tools())
    asyncio.run(list_resources())
```

### Connection & Resources

This example shows how to connect to the running server and fetch dynamic resource documentation (e.g., available tags for the Main corpus).

```python
import asyncio
from fastmcp import Client

async def get_corpus_info():
    # Connect to the HTTP server (note: /mcp endpoint)
    async with Client("http://127.0.0.1:8000/mcp") as client:

        # Check connection
        await client.ping()
        print("Connected to RNC MCP Server")

        # Read dynamic resource for the MAIN corpus
        # This returns a list of resources (usually one element)
        data = await client.read_resource("rnc://MAIN/info")
        resource = data[0]
        print(f"\n--- Resource Content ---\n{resource.text}")

if __name__ == "__main__":
    asyncio.run(get_corpus_info())
```

### Simple Search Query

A basic example searching for the lemma *дом* (house) in the main corpus.

```python
import asyncio
from fastmcp import Client

async def simple_search():
    async with Client("http://127.0.0.1:8000/mcp") as client:

        # Call the concordance tool with a query parameter
        # The query must be wrapped in {"query": {...}}
        result = await client.call_tool(
            "concordance",
            {
                "query": {
                    "corpus": "MAIN",
                    "tokens": [
                        {"lemma": "дом"}
                    ]
                }
            }
        )

        # Use structured_content for JSON access
        data = result.structured_content
        stats = data["stats"]["queryStats"]
        print(f"Found {stats['textCount']} documents using the word 'дом'\n")

        # Print first 3 documents with snippets
        for doc in data["results"][:3]:
            meta = doc["metadata"]
            print(f"Document: {meta['author']} - {meta['title']} ({meta['year']})")
            for snippet in doc["examples"]:
                print(f"  > {snippet}")
            print()

if __name__ == "__main__":
    asyncio.run(simple_search())
```

### Complex Search Query

An advanced example demonstrating multi-token search with distance constraints, grammar tags, and subcorpus metadata filtering (author, date range, gender).

```python
import asyncio
from fastmcp import Client

async def complex_search():
    async with Client("http://127.0.0.1:8000/mcp") as client:

        # Complex query:
        # Find a Verb (gramm="V") with lemma *идти* (to go)
        # Followed by the word form *дождь* (rain) within 1-3 words distance
        # Filter by author "Pushkin", male gender, written between 1810-1837
        result = await client.call_tool(
            "concordance",
            {
                "query": {
                    "corpus": "MAIN",
                    "tokens": [
                        {
                            "lemma": "идти",
                            "gramm": "V"
                        },
                        {
                            "wordform": "дождь",
                            "dist_min": 1,
                            "dist_max": 3
                        }
                    ],
                    "subcorpus": {
                        "author": "Пушкин",
                        "date_range": {"start_year": 1810, "end_year": 1837},
                        "author_gender": "male"
                    },
                    "sort": "grcreated",
                    "page": 0,
                    "per_page": 5,
                    "return_examples": True
                }
            }
        )

        # Use structured_content for convenient JSON access
        data = result.structured_content
        print(f"Total results: {data['stats']['queryStats']['textCount']}")

        # Print matches
        for doc in data["results"]:
            meta = doc["metadata"]
            print(f"\nDocument: {meta['author']} - {meta['title']} ({meta['year']})")
            for snippet in doc["examples"]:
                print(f" > {snippet}")

if __name__ == "__main__":
    asyncio.run(complex_search())
```

## Development

To run the test suite, install the development dependencies and run `pytest`.

```bash
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run unit tests only
pytest -m unit
```

The project maintains high test coverage. You can view the coverage report by running:

```bash
pytest --cov=src/rnc_mcp --cov-report=term-missing
```
