from typing import List, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field
from config import Config


RncCorpusType = Enum(
    'RncCorpusType',
    {code: code for code in Config.CORPORA.keys()},
    type=str
)

_corpus_options_doc = "\n".join(
    [f"- `{code}`: {desc}" for code, desc in Config.CORPORA.items()]
)


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


class DateFilter(BaseModel):
    start_year: Optional[int] = None
    end_year: Optional[int] = None


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


class DocMetadata(BaseModel):
    title: str
    author: Optional[str] = None
    year: Optional[str] = None


class DocumentItem(BaseModel):
    metadata: DocMetadata
    examples: List[str] = Field(...,
                                description="List of text fragments found in the document.")


class StatValues(BaseModel):
    textCount: Optional[int] = None
    wordUsageCount: Optional[int] = None


class GlobalStats(BaseModel):
    corpusStats: Optional[StatValues] = None
    subcorpStats: Optional[StatValues] = None
    queryStats: Optional[StatValues] = None
    total_pages_available: int


class ConcordanceResponse(BaseModel):
    stats: GlobalStats
    results: List[DocumentItem]
