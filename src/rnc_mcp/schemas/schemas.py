from typing import List, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field
from rnc_mcp.config import Config


RncCorpusType = Enum(
    'RncCorpusType',
    {code: code for code in Config.RNC_CORPORA.keys()},
    type=str
)

_corpus_options_doc = "\n".join(
    [f"- `{code}`: {desc}" for code, desc in Config.RNC_CORPORA.items()]
)


# Request schemas

class TokenRequest(BaseModel):
    lemma: Optional[str] = Field(
        None, description="The dictionary form of the word (e.g., 'бежать')."
    )
    wordform: Optional[str] = Field(
        None, description="The exact word form (e.g., 'бежал')."
    )
    gramm: Optional[str] = Field(
        None,
        description="Grammar tags (e.g., 'S')."
    )
    semantic: Optional[str] = Field(
        None,
        description="Semantic tags (e.g., 't:hum')."
    )
    syntax: Optional[str] = Field(
        None,
        description="Syntactic tags (e.g., 'clause_main')."
    )
    flags: Optional[str] = Field(
        None,
        description="Additional feature flags (e.g., 'lexred')."
    )
    dist_min: int = Field(1, description="Min distance from previous word.")
    dist_max: int = Field(1, description="Max distance from previous word.")

    def __str__(self):
        parts = []
        if self.lemma:
            parts.append(f"lemma='{self.lemma}'")
        if self.wordform:
            parts.append(f"form='{self.wordform}'")
        if self.gramm:
            parts.append(f"gr='{self.gramm}'")
        if self.semantic:
            parts.append(f"sem='{self.semantic}'")
        if self.syntax:
            parts.append(f"synt='{self.syntax}'")
        if self.flags:
            parts.append(f"flags='{self.flags}'")

        if self.dist_min != 1 or self.dist_max != 1:
            parts.append(f"dist={self.dist_min}..{self.dist_max}")

        content = ", ".join(parts) if parts else "empty_token"
        return f"Token[{content}]"


class DateFilter(BaseModel):
    start_year: Optional[int] = None
    end_year: Optional[int] = None

    def __str__(self):
        start = self.start_year if self.start_year is not None else ""
        end = self.end_year if self.end_year is not None else ""
        return f"{start}-{end}"


class SubcorpusFilter(BaseModel):
    author: Optional[str] = Field(
        None, description="Filter by author name (e.g., 'Пушкин')."
    )
    title: Optional[str] = Field(
        None,
        description="Filter by document title (e.g., 'Евгений Онегин')."
    )
    date_range: Optional[DateFilter] = Field(
        None, description="Filter by document creation date."
    )
    author_gender: Optional[Literal["male", "female"]] = Field(
        None, description="Filter by author gender."
    )
    author_birthyear_range: Optional[DateFilter] = Field(
        None, description="Filter by author's birth year range."
    )
    disambiguation: Optional[Literal["auto", "manual"]] = Field(
        None,
        description="Homonymy disambiguation mode (auto or manual tagging)."
    )

    def __str__(self):
        parts = []
        if self.author:
            parts.append(f"author='{self.author}'")
        if self.title:
            parts.append(f"title='{self.title}'")
        if self.date_range:
            parts.append(f"date={self.date_range}")
        if self.author_gender:
            parts.append(f"sex={self.author_gender}")
        if self.author_birthyear_range:
            parts.append(f"author_birth={self.author_birthyear_range}")
        if self.disambiguation:
            parts.append(f"mode={self.disambiguation}")

        return ", ".join(parts)


class SearchQuery(BaseModel):
    corpus: RncCorpusType = Field(  # type: ignore
        RncCorpusType.MAIN,  # type: ignore
        description=(
            f"Corpus to search in. Available options:\n"
            f"{_corpus_options_doc}"
        )
    )
    tokens: List[TokenRequest] = Field(
        ...,
        min_length=1,
        description="Sequence of words to find."
    )
    subcorpus: Optional[SubcorpusFilter] = Field(
        None, description="Subcorpus filtering options."
    )
    sort: Optional[str] = Field(
        None,
        description="Sort order (e.g., 'grcreated')."
    )
    page: int = Field(
        0, description="Page number (0-indexed)."
    )
    per_page: int = Field(
        10, description="Documents per page."
    )
    return_examples: bool = Field(
        True,
        description=(
            "Whether to return examples with results. "
            "If False, only statistics are returned."
        )
    )

    def __str__(self):
        lines = [f"SearchQuery ({self.corpus.value}):"]

        lines.append("  Tokens:")
        for i, token in enumerate(self.tokens, 1):
            lines.append(f"    {i}. {token}")

        if self.subcorpus:
            lines.append(f"  Subcorpus: {self.subcorpus}")

        lines.append(f"  Page: {self.page} (size={self.per_page})")
        if self.sort:
            lines.append(f"  Sort: {self.sort}")
        if not self.return_examples:
            lines.append("  Mode: Stats only")

        return "\n".join(lines)


# Response schemas

class DocMetadata(BaseModel):
    title: str
    author: Optional[str] = None
    year: Optional[str] = None

    def __str__(self):
        parts = [self.title]
        meta = []
        if self.author:
            meta.append(self.author)
        if self.year:
            meta.append(self.year)
        if meta:
            parts.append(f"({', '.join(meta)})")
        return " ".join(parts)


class DocumentItem(BaseModel):
    metadata: DocMetadata
    examples: List[str] = Field(...,
                                description="List of text fragments found in the document.")

    def __str__(self):
        return f"{self.metadata}: {len(self.examples)} matches"


class StatValues(BaseModel):
    textCount: Optional[int] = None
    wordUsageCount: Optional[int] = None

    def __str__(self):
        return f"docs={self.textCount or 0}, words={self.wordUsageCount or 0}"


class GlobalStats(BaseModel):
    corpusStats: Optional[StatValues] = None
    subcorpStats: Optional[StatValues] = None
    queryStats: Optional[StatValues] = None
    total_pages_available: int

    def __str__(self):
        lines = []
        if self.corpusStats:
            lines.append(f"Corpus: {self.corpusStats}")
        if self.subcorpStats:
            lines.append(f"Subcorpus: {self.subcorpStats}")
        if self.queryStats:
            lines.append(f"Found: {self.queryStats}")
        lines.append(f"Total Pages: {self.total_pages_available}")
        return ", ".join(lines)


class ConcordanceResponse(BaseModel):
    stats: GlobalStats
    results: List[DocumentItem]

    def __str__(self):
        header = f"Response Stats: [{self.stats}]"
        if not self.results:
            return header + "\nResults: None"

        preview = "\n".join([f"  - {doc}" for doc in self.results[:3]])
        remaining = len(self.results) - 3
        if remaining > 0:
            preview += f"\n  ... and {remaining} more"

        return f"{header}\nResults:\n{preview}"
