from fastmcp import FastMCP, Context
from rnc_mcp.schemas.llm import SearchQuery
from rnc_mcp.services.builder import RNCQueryBuilder
from rnc_mcp.services.formatter import ResponseFormatter
from rnc_mcp.client import RNCClient
from rnc_mcp.config import Config


# Initialize FastMCP
mcp = FastMCP(
    "Russian National Corpus Agent",
    dependencies=["httpx", "pydantic"],
    description="Agent for searching the Russian National Corpus (RNC)."
)

# Instantiate services
client = RNCClient()

@mcp.resource("rnc://config/attributes")
async def get_corpus_attributes() -> str:
    """
    Dynamic resource that fetches valid grammatical and semantic attributes
    from the RNC configuration. Useful for constructing filters.
    """
    try:
        raw_config = await client.get_config()
        return str(raw_config)
    except Exception as e:
        return f"Error fetching configuration: {str(e)}"

@mcp.tool
async def search_rnc(query: SearchQuery, ctx: Context) -> str:
    """
    Performs a lexicographic search in the Russian National Corpus.

    Use this tool to find specific words, lemmas, or grammatical constructions.
    Results are returned as plain text snippets with metadata.
    """
    # Validate / Notify User
    try:
        Config.get_token() # Check auth early
    except ValueError as e:
        await ctx.error("Authentication failed")
        return str(e)

    await ctx.info(f"Searching RNC for: {len(query.tokens)} tokens in {query.corpus}")

    # Build Payload
    try:
        payload = RNCQueryBuilder.build_payload(query)
        await ctx.debug(f"Generated Payload: {payload}")
    except Exception as e:
        return f"Error constructing query: {str(e)}"

    # Execute
    try:
        raw_result = await client.execute_search(payload)
    except Exception as e:
        return f"API Error: {str(e)}"

    # Format
    readable_result = ResponseFormatter.format_search_results(raw_result)

    return readable_result

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
