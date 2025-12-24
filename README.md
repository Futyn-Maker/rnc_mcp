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

**Input Schema (JSON):**

```json
{
  "corpus": "MAIN", // Options: MAIN, PAPER, POETIC, SPOKEN, etc.
  "tokens": [
    {
      "lemma": "бежать",
      "gramm": "V",
      "dist_min": 1,
      "dist_max": 3
    },
    {
      "wordform": "быстро"
    }
  ],
  "subcorpus": {
    "author": "Пушкин",
    "date_range": { "start_year": 1820, "end_year": 1837 },
    "author_gender": "male"
  },
  "return_examples": true, // If false, returns only statistics
  "page": 0,
  "per_page": 10
}
```

**Output:**

Returns a structured response containing global statistics (corpus size, total hits) and a list of document matches with highlighted text snippets.

## Resources

The server provides dynamic resources that describe the configuration and available attributes for each corpus type. These are generated on-the-fly by querying the RNC API.

**URI Pattern:** `rnc://{CORPUS_CODE}/info`

**Example URIs:**

* `rnc://MAIN/info`
* `rnc://POETIC/info`

Reading these resources provides Markdown-formatted documentation of available sorting methods, grammar tags, and semantic categories specific to that corpus.

## Programmatic Usage

You can use the `fastmcp` client library to interact with this server programmatically using Python. This is useful for testing queries or building custom applications.

### Connection & Resources

This example shows how to connect to the running server and fetch dynamic resource documentation (e.g., available tags for the Main corpus).

```python
import asyncio
from fastmcp import Client

async def get_corpus_info():
    # Connect to the HTTP server
    async with Client("http://127.0.0.1:8000") as client:

        # Check connection
        await client.ping()
        print("Connected to RNC MCP Server")

        # Read dynamic resource for the MAIN corpus
        # This returns Markdown documentation generated from the RNC API
        resource = await client.read_resource("rnc://MAIN/info")
        print(f"\n--- Resource Content ---\n{resource.text[:200]}...")

if __name__ == "__main__":
    asyncio.run(get_corpus_info())
```

### Simple Search Query

A basic example searching for the lemma *дом* (house) in the main corpus.

```python
import asyncio
from fastmcp import Client

async def simple_search():
    async with Client("http://127.0.0.1:8000") as client:

        # Simple query: find the lemma "дом"
        query = {
            "corpus": "MAIN",
            "tokens": [
                {"lemma": "дом"}
            ]
        }

        result = await client.call_tool("concordance", query)

        stats = result.data['stats']['corpusStats']
        print(f"Found {stats['textCount']} documents using the word 'дом'")

if __name__ == "__main__":
    asyncio.run(simple_search())
```

### Complex Search Query

An advanced example demonstrating multi-token search with distance constraints, grammar tags, and subcorpus metadata filtering (author, date range, gender).

```python
import asyncio
from fastmcp import Client

async def complex_search():
    async with Client("http://127.0.0.1:8000") as client:

        # Complex query:
        # Find a Verb (gramm="V") with lemma *идти* (to go)
        # Followed by the word form *дождь* (rain) within 1-3 words distance
        # Filter by author "Pushkin", male gender, written between 1810-1837
        payload = {
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
            "sort": "grcreated", # Sort by creation date
            "page": 0,
            "per_page": 5,
            "return_examples": True
        }

        result = await client.call_tool("concordance", payload)

        print(f"Total results: {result.data['stats']['queryStats']['textCount']}")

        # Print matches
        for doc in result.data['results']:
            meta = doc['metadata']
            print(f"\nDocument: {meta['author']} - {meta['title']} ({meta['year']})")
            for snippet in doc['examples']:
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
