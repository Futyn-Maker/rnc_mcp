from typing import Any, Dict, List
from rnc_mcp.schemas.llm import SearchQuery, TokenRequest


class RNCQueryBuilder:
    """
    Responsible for converting linear LLM intent into the
    nested SearchFormValue JSON required by RNC API.
    """

    @staticmethod
    def _build_token_conditions(token: TokenRequest) -> List[Dict[str, Any]]:
        conditions = []

        if token.lemma:
            conditions.append({"fieldName": "lex", "text": {"v": token.lemma}})

        if token.wordform:
            conditions.append({"fieldName": "word", "text": {"v": token.wordform}})

        if token.gramm:
            conditions.append({"fieldName": "gramm", "text": {"v": token.gramm}})

        return conditions

    @staticmethod
    def _build_dist_condition(dist_min: int, dist_max: int) -> Dict[str, Any]:
        return {
            "fieldName": "dist",
            "intRange": {"begin": dist_min, "end": dist_max}
        }

    @classmethod
    def build_payload(cls, query: SearchQuery) -> Dict[str, Any]:
        subsection_values = []

        for index, token in enumerate(query.tokens):
            conditions = cls._build_token_conditions(token)

            # Distance logic:
            # The RNC API typically attaches the distance condition to the token
            # regarding its relation to the *neighbor*.
            # If this is NOT the first token, we add distance constraints.
            if index > 0:
                dist_cond = cls._build_dist_condition(token.dist_min, token.dist_max)
                conditions.append(dist_cond)

            subsection_values.append({
                "conditionValues": conditions
            })

        # Construct the root object
        payload = {
            "corpus": {"type": query.corpus},
            "lexGramm": {
                "sectionValues": [
                    {"subsectionValues": subsection_values}
                ]
            },
            "pagination": {
                "page": query.page,
                "docsPerPage": query.per_page,
                # We set a reasonable default for snippets per doc to keep output clean
                "snippetsPerDoc": 1
            },
            # Sorting defaults to relevance usually, but can be made explicit
            "sort": "random"
        }

        # Handle Metadata (Subcorpus)
        if query.date_range:
            subcorpus_conditions = []
            if query.date_range.start_year or query.date_range.end_year:
                # RNC uses 'created' or 'date' depending on corpus config.
                # 'created' is standard for Main.
                date_cond = {
                    "fieldName": "created",
                    "dateRange": {
                        "matching": "INT_RANGE_INTERSECT"
                    }
                }
                if query.date_range.start_year:
                    date_cond["dateRange"]["begin"] = {"year": query.date_range.start_year}
                if query.date_range.end_year:
                    date_cond["dateRange"]["end"] = {"year": query.date_range.end_year}

                subcorpus_conditions.append(date_cond)

            if subcorpus_conditions:
                payload["subcorpus"] = {
                    "sectionValues": [{"conditionValues": subcorpus_conditions}]
                }

        return payload
