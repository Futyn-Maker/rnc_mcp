from typing import Dict, Any, List


class ResponseFormatter:
    """
    Transforms the verbose RNC 'concordance' JSON into
    a lightweight text format for the LLM.
    """

    @staticmethod
    def format_search_results(raw_response: Dict[str, Any]) -> str:
        output = []

        # Extract Stats
        # API structure varies, check 'concordanceData' or root keys
        # Based on docs: root -> concordanceData (sometimes) or groups directly
        # We'll assume the standard structure found in modern RNC responses.

        groups = raw_response.get("groups", [])
        total_docs = 0

        for group in groups:
            docs = group.get("docs", [])
            for doc in docs:
                total_docs += 1
                info = doc.get("info", {})
                title = info.get("title", "Unknown Title")

                # Extract textual content
                snippets = []
                snippet_groups = doc.get("snippetGroups", [])
                for sg in snippet_groups:
                    for snippet in sg.get("snippets", []):
                        # Flatten sequences -> words -> text
                        text_parts = []
                        for seq in snippet.get("sequences", []):
                            for word in seq.get("words", []):
                                text_parts.append(word.get("text", ""))

                        snippets.append(" ".join(text_parts))

                # Format this document entry
                doc_str = f"--- Document: {title} ---\n"
                for s in snippets:
                    doc_str += f"> {s}\n"
                output.append(doc_str)

        header = f"Found results in {total_docs} documents (Page view).\n\n"
        return header + "\n".join(output)
