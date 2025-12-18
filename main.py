from fastmcp import FastMCP, Context
from schemas.schemas import SearchQuery, ConcordanceResponse
from services.builder import RNCQueryBuilder
from services.formatter import ResponseFormatter
from client import RNCClient
from config import Config
from resources.generator import CorpusResourceGenerator


mcp = FastMCP(
    "Russian National Corpus")
client = RNCClient()
resource_generator = CorpusResourceGenerator(client)


def register_corpus_resources():
    """
    Registers a static resource for each corpus defined in Config.
    The resource URI is rnc://{CODE}/info.
    """
    # Factory function to create a handler with the captured corpus code
    def create_handler(corpus_code: str):
        async def handler() -> str:
            return await resource_generator.generate(corpus_code)
        return handler

    for code, desc in Config.CORPORA.items():
        uri = f"rnc://{code}/info"
        name = f"{desc}: Info"

        # Register programmatically
        mcp.resource(uri, name=name)(create_handler(code))


# Initialize resources on startup
register_corpus_resources()


@mcp.tool
async def concordance(query: SearchQuery, ctx: Context) -> ConcordanceResponse:
    """
    Performs a lexicographic search in the Russian National Corpus.
    Returns statistics and optionally a list of documents with examples.
    """
    try:
        Config.get_token()
    except ValueError as e:
        raise RuntimeError(str(e))

    await ctx.info(f"Searching {query.corpus}...")

    try:
        payload = RNCQueryBuilder.build_payload(query)
    except Exception as e:
        raise RuntimeError(f"Query Build Error: {str(e)}")

    try:
        raw_result = await client.execute_concordance(payload)
    except Exception as e:
        raise RuntimeError(f"API Execution Error: {str(e)}")

    try:
        formatted_response = ResponseFormatter.format_search_results(
            raw_result)

        # Clear results if user only wants statistics
        if not query.return_examples:
            formatted_response.results = []

        return formatted_response
    except Exception as e:
        raise RuntimeError(f"Response Formatting Error: {str(e)}")


if __name__ == "__main__":
    mcp.run(transport="http")
