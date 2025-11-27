from typing import Any, Dict, List
from schemas.llm import SearchQuery, TokenRequest


class RNCQueryBuilder:
    @staticmethod
    def _build_token_conditions(token: TokenRequest) -> List[Dict[str, Any]]:
        conditions = []

        if token.lemma:
            conditions.append({"fieldName": "lex", "text": {"v": token.lemma}})

        if token.wordform:
            conditions.append(
                {"fieldName": "word", "text": {"v": token.wordform}})

        if token.gramm:
            conditions.append(
                {"fieldName": "gramm", "text": {"v": token.gramm}})

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

            if index > 0:
                dist_cond = cls._build_dist_condition(
                    token.dist_min, token.dist_max)
                conditions.append(dist_cond)

            if conditions:
                subsection_values.append({
                    "conditionValues": conditions
                })

        payload = {
            "corpus": {"type": query.corpus},
            "lexGramm": {
                "sectionValues": [
                    {"subsectionValues": subsection_values}
                ]
            },
            "params": {
                "pageParams": {
                    "page": query.page,
                    "docsPerPage": query.per_page,
                    "snippetsPerDoc": 10
                }
            }
        }

        if query.date_range:
            subcorpus_conditions = []
            date_cond = {
                "fieldName": "created",
                "dateRange": {"matching": "INT_RANGE_INTERSECT"}
            }

            has_date = False
            if query.date_range.start_year:
                date_cond["dateRange"]["begin"] = {
                    "year": query.date_range.start_year}
                has_date = True
            if query.date_range.end_year:
                date_cond["dateRange"]["end"] = {
                    "year": query.date_range.end_year}
                has_date = True

            if has_date:
                subcorpus_conditions.append(date_cond)
                payload["subcorpus"] = {
                    "sectionValues": [
                        {"conditionValues": subcorpus_conditions}
                    ]
                }

        return payload
