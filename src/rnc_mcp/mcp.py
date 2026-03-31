import asyncio
from typing import List, Optional

from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_access_token
from rnc_mcp.schemas.schemas import (
    SearchQuery, ConcordanceResponse, GlobalStats,
    DocumentItem,
)
from rnc_mcp.services.rnc_builder import RNCQueryBuilder
from rnc_mcp.services.rnc_formatter import (
    RNCResponseFormatter,
)
from rnc_mcp.clients.rnc_client import RNCClient
from rnc_mcp.config import Config
from rnc_mcp.resources.rnc_generator import (
    RNCResourceGenerator,
)
from rnc_mcp.auth.rnc_validator import RNCTokenValidator
from rnc_mcp.auth.rnc_provider import RNCAuthProvider


validator = RNCTokenValidator(
    cache_ttl=Config.RNC_AUTH_CACHE_TTL
)
auth = RNCAuthProvider(validator)

mcp = FastMCP("Russian National Corpus", auth=auth)
client = RNCClient()
resource_generator = RNCResourceGenerator(client)


def _get_user_token() -> str:
    """Get user's RNC token from auth context or env var.

    HTTP transport: returns the bearer token provided by
    the user (validated by the auth layer).
    STDIO transport: returns RNC_API_TOKEN from env var.
    """
    access_token = get_access_token()
    if access_token is not None:
        return access_token.token
    return Config.get_rnc_token()


def register_corpus_resources():
    """
    Registers a static resource for each corpus defined
    in Config. The resource URI is rnc://{CODE}/info.
    """
    def create_handler(corpus_code: str):
        async def handler() -> str:
            token = _get_user_token()
            return await resource_generator.generate(
                corpus_code, token
            )
        return handler

    for code, desc in Config.RNC_CORPORA.items():
        uri = f"rnc://{code}/info"
        name = f"{desc}: Info"

        mcp.resource(uri, name=name)(
            create_handler(code)
        )


# Initialize resources on startup
register_corpus_resources()


async def _collect_examples(
    query: SearchQuery,
    corpus_client: RNCClient,
    ctx: Context,
    token: str,
) -> ConcordanceResponse:
    """Fetch multiple pages to collect up to
    max_examples."""
    assert query.max_examples is not None
    max_examples = query.max_examples
    delay = Config.RNC_PAGE_DELAY
    max_retries = Config.RNC_MAX_RETRIES

    all_results: List[DocumentItem] = []
    total_examples = 0
    stats: Optional[GlobalStats] = None
    consecutive_failures = 0
    current_page = query.page
    last_fetched_page: Optional[int] = None

    try:
        payload = RNCQueryBuilder.build_payload(query)
    except Exception as e:
        raise RuntimeError(
            f"Query Build Error: {str(e)}"
        )

    payload["params"]["pageParams"][
        "docsPerPage"
    ] = 50
    payload["params"]["pageParams"][
        "snippetsPerDoc"
    ] = 10

    while True:
        payload["params"]["pageParams"][
            "page"
        ] = current_page

        try:
            raw = (
                await corpus_client.execute_concordance(
                    payload, token=token, ctx=ctx
                )
            )
            consecutive_failures = 0
        except Exception as e:
            consecutive_failures += 1
            await ctx.info(
                f"Page {current_page} failed "
                f"(attempt {consecutive_failures}"
                f"/{max_retries}): {e}"
            )
            if consecutive_failures >= max_retries:
                await ctx.info(
                    f"Stopping after {max_retries} "
                    f"consecutive failures. "
                    f"Returning {total_examples} "
                    f"examples."
                )
                break
            await asyncio.sleep(delay)
            continue

        response = (
            RNCResponseFormatter.format_search_results(
                raw
            )
        )

        if stats is None:
            stats = response.stats

        last_fetched_page = current_page

        for doc in response.results:
            remaining = max_examples - total_examples
            if remaining <= 0:
                break
            if len(doc.examples) > remaining:
                doc.examples = doc.examples[:remaining]
            all_results.append(doc)
            total_examples += len(doc.examples)

        await ctx.info(
            f"Page {current_page}: "
            f"{total_examples}/{max_examples} examples "
            f"from {len(all_results)} docs"
        )

        if total_examples >= max_examples:
            break
        assert stats is not None
        if (
            current_page + 1
            >= stats.total_pages_available
        ):
            await ctx.info(
                f"All pages fetched "
                f"(total: "
                f"{stats.total_pages_available})"
            )
            break
        if not response.results:
            await ctx.info(
                f"Page {current_page} "
                f"returned no results."
            )
            break

        current_page += 1
        await asyncio.sleep(delay)

    if stats is None:
        raise RuntimeError(
            "Failed to fetch any results after "
            f"{max_retries} retries."
        )

    stats.last_page_fetched = (
        last_fetched_page
        if last_fetched_page is not None
        else query.page
    )
    return ConcordanceResponse(
        stats=stats, results=all_results
    )


@mcp.tool
async def concordance(
    query: SearchQuery, ctx: Context
) -> ConcordanceResponse:
    """
    Performs a lexicographic search in the Russian National
    Corpus. Returns statistics and optionally a list of
    documents with examples.
    """
    token = _get_user_token()

    await ctx.info(f"Searching {query.corpus}...")
    await ctx.debug(f"Query: {query}")

    if query.max_examples is not None:
        return await _collect_examples(
            query, client, ctx, token
        )

    try:
        payload = RNCQueryBuilder.build_payload(query)
        await ctx.debug(f"Payload: {payload}")
    except Exception as e:
        raise RuntimeError(
            f"Query Build Error: {str(e)}"
        )

    try:
        raw_result = await client.execute_concordance(
            payload, token=token, ctx=ctx
        )
        await ctx.debug(f"Raw Result: {raw_result}")
    except Exception as e:
        raise RuntimeError(
            f"API Execution Error: {str(e)}"
        )

    try:
        formatted_response = (
            RNCResponseFormatter.format_search_results(
                raw_result
            )
        )
        formatted_response.stats.last_page_fetched = (
            query.page
        )

        if not query.return_examples:
            formatted_response.results = []

        await ctx.debug(
            f"Formatted Response: "
            f"{formatted_response}"
        )

        return formatted_response
    except Exception as e:
        raise RuntimeError(
            f"Response Formatting Error: {str(e)}"
        )
