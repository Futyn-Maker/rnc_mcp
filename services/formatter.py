from typing import Dict, Any, List, Optional
from schemas.llm import RNCResponse, DocumentItem, DocMetadata, GlobalStats, StatValues


class ResponseFormatter:
    @staticmethod
    def _extract_meta(doc_info: Dict[str, Any]) -> DocMetadata:
        title = doc_info.get("title", "Unknown Title")
        author = None
        year = None

        explain_items = doc_info.get("docExplainInfo", {}).get("items", [])
        if explain_items:
            fields = explain_items[0].get("parsingFields", [])
            for f in fields:
                name = f.get("name")
                values = f.get("value", [])
                if not values:
                    continue

                val_str = values[0].get("valString", {}).get("v")

                if name == "author":
                    author = val_str
                elif name == "created":
                    year = val_str
                elif name == "header" and title == "Unknown Title":
                    title = val_str

        return DocMetadata(title=title, author=author, year=year)

    @staticmethod
    def _format_snippet_text(words: List[Dict[str, Any]]) -> str:
        if not words:
            return ""

        # Identify the range of hits
        hit_indices = [
            i for i,
            w in enumerate(words) if w.get(
                "displayParams",
                {}).get("hit")]

        start_hit = hit_indices[0] if hit_indices else -1
        end_hit = hit_indices[-1] if hit_indices else -1

        text_builder = []
        for i, word in enumerate(words):
            token = word.get("text", "")

            if i == start_hit:
                token = "**" + token

            if i == end_hit:
                token = token + "**"

            text_builder.append(token)

        return "".join(text_builder)

    @staticmethod
    def format_search_results(raw_response: Dict[str, Any]) -> RNCResponse:
        pagination = raw_response.get("pagination", {})
        total_pages = pagination.get("totalPageCount", 0)

        # Stats
        def parse_stats(key: str) -> Optional[StatValues]:
            data = raw_response.get(key)
            if not data:
                return None
            return StatValues(
                textCount=data.get("textCount"),
                wordUsageCount=data.get("wordUsageCount")
            )

        global_stats = GlobalStats(
            corpusStats=parse_stats("corpusStats"),
            subcorpStats=parse_stats("subcorpStats"),
            queryStats=parse_stats("queryStats"),
            total_pages_available=total_pages
        )

        results: List[DocumentItem] = []
        groups = raw_response.get("groups", [])

        for group in groups:
            docs = group.get("docs", [])
            for doc in docs:
                info = doc.get("info", {})
                metadata = ResponseFormatter._extract_meta(info)

                examples = []
                snippet_groups = doc.get("snippetGroups", [])
                for sg in snippet_groups:
                    for snippet in sg.get("snippets", []):
                        for seq in snippet.get("sequences", []):
                            words = seq.get("words", [])
                            text = ResponseFormatter._format_snippet_text(
                                words)
                            if text:
                                examples.append(text)

                if examples:
                    results.append(
                        DocumentItem(
                            metadata=metadata,
                            examples=examples))

        return RNCResponse(stats=global_stats, results=results)
