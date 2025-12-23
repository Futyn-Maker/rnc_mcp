from typing import Any, Dict, List, Optional
from rnc_mcp.schemas.schemas import (
    SearchQuery, TokenRequest, SubcorpusFilter, DateFilter
)


class RNCQueryBuilder:
    @staticmethod
    def _build_token_conditions(token: TokenRequest) -> List[Dict[str, Any]]:
        conditions = []

        if token.lemma:
            conditions.append({"fieldName": "lex", "text": {"v": token.lemma}})

        if token.wordform:
            conditions.append(
                {"fieldName": "form", "text": {"v": token.wordform}})

        if token.gramm:
            conditions.append(
                {"fieldName": "gramm", "text": {"v": token.gramm}})

        if token.semantic:
            conditions.append(
                {"fieldName": "sem", "text": {"v": token.semantic}})

        if token.syntax:
            conditions.append(
                {"fieldName": "syntax", "text": {"v": token.syntax}})

        if token.flags:
            conditions.append(
                {"fieldName": "flags", "text": {"v": token.flags}})

        return conditions

    @staticmethod
    def _build_dist_condition(dist_min: int, dist_max: int) -> Dict[str, Any]:
        return {
            "fieldName": "dist",
            "intRange": {"begin": dist_min, "end": dist_max}
        }

    @staticmethod
    def _build_date_range_condition(
        date_range: DateFilter
    ) -> Optional[Dict[str, Any]]:
        """Build a date range condition for document creation date."""
        date_cond = {
            "fieldName": "created",
            "dateRange": {"matching": "INT_RANGE_INTERSECT"}
        }

        has_date = False
        if date_range.start_year:
            date_cond["dateRange"]["begin"] = {
                "year": date_range.start_year,
                "month": 1,
                "day": 1
            }
            has_date = True
        if date_range.end_year:
            date_cond["dateRange"]["end"] = {
                "year": date_range.end_year,
                "month": 12,
                "day": 31
            }
            has_date = True

        return date_cond if has_date else None

    @classmethod
    def _build_subcorpus_conditions(
        cls, subcorpus: SubcorpusFilter
    ) -> List[Dict[str, Any]]:
        """Build subcorpus filtering conditions."""
        conditions = []

        # Disambiguation (tagging)
        if subcorpus.disambiguation:
            conditions.append({
                "fieldName": "tagging",
                "text": {"v": subcorpus.disambiguation}
            })

        # Document title (header)
        if subcorpus.title:
            conditions.append({
                "fieldName": "header",
                "text": {"v": subcorpus.title}
            })

        # Document creation date
        if subcorpus.date_range:
            date_cond = cls._build_date_range_condition(
                subcorpus.date_range
            )
            if date_cond:
                conditions.append(date_cond)

        # Author name
        if subcorpus.author:
            conditions.append({
                "fieldName": "author",
                "text": {"v": subcorpus.author}
            })

        # Author gender (sex)
        if subcorpus.author_gender:
            gender_value = (
                "муж" if subcorpus.author_gender == "male" else "жен"
            )
            conditions.append({
                "fieldName": "sex",
                "text": {"v": gender_value}
            })

        # Author birth year
        if subcorpus.author_birthyear_range:
            birthyear_range = subcorpus.author_birthyear_range
            if birthyear_range.start_year or birthyear_range.end_year:
                birth_cond = {
                    "fieldName": "birthday",
                    "intRange": {"matching": "INT_RANGE_INTERSECT"}
                }
                if birthyear_range.start_year:
                    birth_cond["intRange"]["begin"] = (
                        birthyear_range.start_year
                    )
                if birthyear_range.end_year:
                    birth_cond["intRange"]["end"] = birthyear_range.end_year
                conditions.append(birth_cond)

        return conditions

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

        global_conditions = [
            {"fieldName": "disambmod", "text": {"v": "main"}},
            {"fieldName": "distmod", "text": {"v": "with_zeros"}}
        ]

        # Use minimal pagination if not returning examples
        if query.return_examples:
            docs_per_page = query.per_page
            snippets_per_doc = 50
        else:
            docs_per_page = 1
            snippets_per_doc = 1

        payload = {
            "corpus": {"type": query.corpus},
            "lexGramm": {
                "sectionValues": [
                    {
                        "conditionValues": global_conditions,
                        "subsectionValues": subsection_values
                    }
                ]
            },
            "params": {
                "pageParams": {
                    "page": 0 if not query.return_examples else query.page,
                    "docsPerPage": docs_per_page,
                    "snippetsPerDoc": snippets_per_doc
                }
            }
        }

        if query.sort:
            payload["params"]["sort"] = query.sort

        if query.subcorpus:
            subcorpus_conditions = cls._build_subcorpus_conditions(
                query.subcorpus
            )
            if subcorpus_conditions:
                payload["subcorpus"] = {
                    "sectionValues": [
                        {"conditionValues": subcorpus_conditions}
                    ]
                }

        return payload
