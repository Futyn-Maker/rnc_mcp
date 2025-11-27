from fastmcp import FastMCP, Context
from schemas.llm import SearchQuery, RNCResponse
from services.builder import RNCQueryBuilder
from services.formatter import ResponseFormatter
from client import RNCClient
from config import Config


mcp = FastMCP(
    "Russian National Corpus Agent",
    dependencies=[
        "httpx",
        "pydantic"])
client = RNCClient()


@mcp.resource("rnc://{corpus}/info")
async def get_corpus_info(corpus: str) -> str:
    """
    Returns configuration and grammatical tags for a specific corpus.
    Use this to discover valid Sort options, Filter fields, and Grammar tags.
    """
    try:
        Config.get_token()

        # Fetch Data
        config_data = await client.get_corpus_config(corpus)
        gramm_data = await client.get_grammar_attributes(corpus)

        output = [f"# Configuration for {corpus}\n"]

        # Sorting
        output.append("## Available Sorting Methods")
        sortings = config_data.get("sortings", [])
        valid_sorts = [
            s for s in sortings
            if "CONCORDANCE" in s.get("applicableTo", [])
        ]

        for s in valid_sorts:
            name = s.get("name")
            readable = s.get("humanReadable")
            line = f"- `{name}`"
            if readable:
                line += f" ({readable})"
            output.append(line)

        # Filters
        output.append("\n## Filter Fields")
        stats_fields = config_data.get("statFields", [])
        for f in stats_fields:
            output.append(f"- `{f}`")

        # Grammar Tags
        output.append("\n## Grammar Tags (attr: 'gramm')")

        def format_options(options, level=0):
            res = ""
            indent = "  " * level
            for opt in options:
                title = opt.get("title")
                val = opt.get("value")
                sub = opt.get("suboptions", {}).get("options", [])

                if sub:
                    res += f"\n{indent}- **{title}**\n"
                    res += format_options(sub, level + 1)
                elif val:
                    res += f"{indent}- `{val}` ({title})\n"
            return res

        vals = gramm_data.get("vals", [])
        for val in vals:
            root_options = val.get(
                "valOptions",
                {}).get(
                "v",
                {}).get(
                "options",
                [])
            output.append(format_options(root_options))

        return "\n".join(output)

    except Exception as e:
        return f"Error loading resource for {corpus}: {str(e)}"


@mcp.tool
async def search_rnc(query: SearchQuery, ctx: Context) -> RNCResponse:
    """
    Performs a lexicographic search in the Russian National Corpus.
    Returns statistics and a list of documents with examples.
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
        raw_result = await client.execute_search(payload)
    except Exception as e:
        raise RuntimeError(f"API Execution Error: {str(e)}")

    try:
        formatted_response = ResponseFormatter.format_search_results(
            raw_result)
        return formatted_response
    except Exception as e:
        raise RuntimeError(f"Response Formatting Error: {str(e)}")

if __name__ == "__main__":
    mcp.run(transport="http")
