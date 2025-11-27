from typing import List, Optional, Literal
from pydantic import BaseModel, Field


RncCorpusType = Literal[
    "MAIN", "SYNTAX", "PAPER", "REGIONAL", "PARA", "MULTI", "SCHOOL",
    "DIALECT", "POETIC", "SPOKEN", "ACCENT", "MURCO", "MULTIPARC_RUS",
    "MULTIPARC", "OLD_RUS", "BIRCHBARK", "MID_RUS", "ORTHLIB", "PANCHRON",
    "KIDS", "CLASSICS", "BLOGS", "EPIGRAPHICA"
]


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
        "MAIN",
        description="Corpus to search in.")
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
