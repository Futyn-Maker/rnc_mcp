from typing import Dict, Any, List
from schemas.llm import RNCResponse, PaginationInfo, SearchResultItem, SnippetMetadata
from utils.text_processing import TextProcessor


class ResponseFormatter:
    @staticmethod
    def format_search_results(raw_response: Dict[str, Any]) -> RNCResponse:
        # Parse Pagination
        pagination_data = raw_response.get("pagination", {})

        current_page = pagination_data.get("page", 0)
        total_pages = pagination_data.get("totalPageCount", 0)
        total_docs = 0  # Placeholder if not found in root

        # Parse Results
        results: List[SearchResultItem] = []
        groups = raw_response.get("groups", [])

        for group in groups:
            docs = group.get("docs", [])
            for doc in docs:
                info = doc.get("info", {})

                # Extract Metadata
                meta = SnippetMetadata(
                    title=info.get("title", "Unknown Title"),
                    author=info.get("author", None),
                    date=info.get("created", None),
                    doc_id=info.get("source", {}).get("docId", "unknown")
                )

                # Extract and Join Text
                doc_text_parts = []
                snippet_groups = doc.get("snippetGroups", [])

                for sg in snippet_groups:
                    for snippet in sg.get("snippets", []):
                        for seq in snippet.get("sequences", []):
                            words = seq.get("words", [])
                            formatted_seq = TextProcessor.format_word_sequence(
                                words)
                            doc_text_parts.append(formatted_seq)

                full_text = "\n".join(doc_text_parts)

                results.append(SearchResultItem(
                    metadata=meta,
                    text=full_text
                ))

        return RNCResponse(
            pagination=PaginationInfo(
                current_page=current_page,
                total_pages=total_pages,
                total_documents=total_docs
            ),
            results=results
        )
