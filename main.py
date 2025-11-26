from fastmcp import FastMCP, Context
from schemas.llm import SearchQuery, RNCResponse
from services.builder import RNCQueryBuilder
from services.formatter import ResponseFormatter
from client import RNCClient
from config import Config


mcp = FastMCP(
    "Russian National Corpus Agent",
    dependencies=["httpx", "pydantic"]
)

client = RNCClient()


@mcp.resource("rnc://corpora")
def get_available_corpora() -> str:
    """
    Returns a Markdown list of valid corpus types supported by the API.
    Use these values in the 'corpus' field of search queries.
    """
    corpora = [
        "MAIN (Main Corpus)",
        "PAPER (Newspaper Corpus)",
        "POETIC (Poetic Corpus)",
        "SPOKEN (Spoken Corpus)",
        "DIALECT (Dialect Corpus)",
        "REGIONAL (Regional Corpus)",
        "SCHOOL (Educational Corpus)",
        "PARALLEL (Parallel Corpus - requires 'lang')",
    ]
    return "# Available RNC Corpora\n\n" + \
        "\n".join([f"- {c}" for c in corpora])


@mcp.resource("rnc://tags")
async def get_grammar_tags() -> str:
    """
    Returns a Markdown representation of valid grammatical attributes (POS, Case, Gender, etc.).
    Use these codes in the 'gramm' field of search queries.
    """
    try:
        # Validate auth before call
        Config.get_token()

        raw_data = await client.get_grammar_attributes()

        # Format the messy JSON tree into a clean Markdown list
        output = ["# RNC Grammar Tags\n"]

        vals = raw_data.get("vals", [])
        if not vals:
            return "No attributes found in response."

        # Recursive helper to print options
        def format_options(options, indent=0):
            res = ""
            prefix = "  " * indent + "- "
            for opt in options:
                title = opt.get("title", "Untitled")
                value = opt.get("value", None)

                line = f"{prefix}**{title}**"
                if value:
                    line += f" (`{value}`)"
                res += line + "\n"

                # Handle nested options or suboptions
                sub = opt.get("suboptions", {}).get("options", [])
                if sub:
                    res += format_options(sub, indent + 1)
            return res

        # Root level iteration
        for val in vals:
            options_root = val.get(
                "valOptions",
                {}).get(
                "v",
                {}).get(
                "options",
                [])
            output.append(format_options(options_root))

        return "".join(output)

    except Exception as e:
        return f"Error fetching tags: {str(e)}"


@mcp.tool
async def search_rnc(query: SearchQuery, ctx: Context) -> RNCResponse:
    """
    Performs a lexicographic search in the Russian National Corpus.
    Returns structured JSON with metadata and highlighted text.
    """
    # Validate Auth
    try:
        Config.get_token()
    except ValueError as e:
        raise RuntimeError(str(e))

    await ctx.info(f"Searching RNC: {len(query.tokens)} tokens in {query.corpus}")

    # Build
    try:
        payload = RNCQueryBuilder.build_payload(query)
    except Exception as e:
        raise RuntimeError(f"Query Build Error: {str(e)}")

    # Execute
    try:
        raw_result = await client.execute_search(payload)
    except Exception as e:
        raise RuntimeError(f"API Execution Error: {str(e)}")

    # Format
    try:
        formatted_response = ResponseFormatter.format_search_results(
            raw_result)
        return formatted_response
    except Exception as e:
        raise RuntimeError(f"Response Formatting Error: {str(e)}")

if __name__ == "__main__":
    mcp.run(transport="http")
