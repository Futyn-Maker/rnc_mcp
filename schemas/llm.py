from typing import List, Optional
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
        description="Grammar tags (e.g., 'S').")
    dist_min: int = Field(1, description="Min distance from previous word.")
    dist_max: int = Field(1, description="Max distance from previous word.")


class DateFilter(BaseModel):
    start_year: Optional[int] = None
    end_year: Optional[int] = None


class SearchQuery(BaseModel):
    corpus: RncCorpusType = Field(
        RncCorpusType.MAIN,
        description=f"Corpus to search in. Available options:\n{_corpus_options_doc}")
    tokens: List[TokenRequest] = Field(
        ...,
        min_length=1,
        description="Sequence of words to find."
    )
    date_range: Optional[DateFilter] = Field(
        None, description="Filter by creation date."
    )
    page: int = Field(0, description="Page number (0-indexed).")
    per_page: int = Field(10, description="Documents per page.")


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


class RNCResponse(BaseModel):
    stats: GlobalStats
    results: List[DocumentItem]
