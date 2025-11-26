from typing import List, Optional
from pydantic import BaseModel, Field

# Request Models


class TokenRequest(BaseModel):
    """Represents a single word in the search sequence."""
    lemma: Optional[str] = Field(
        None, description="The dictionary form of the word (e.g., 'бежать')."
    )
    wordform: Optional[str] = Field(
        None, description="The exact word form (e.g., 'бежал')."
    )
    gramm: Optional[str] = Field(
        None, description="Grammar tags separated by comma (e.g., 'S,m,anim')."
    )
    dist_min: int = Field(1, description="Min distance from previous word.")
    dist_max: int = Field(1, description="Max distance from previous word.")


class DateFilter(BaseModel):
    start_year: Optional[int] = None
    end_year: Optional[int] = None


class SearchQuery(BaseModel):
    """The main input model for the search tool."""
    corpus: str = Field(
        "MAIN",
        description="Corpus type (e.g., MAIN, PAPER). See rnc://corpora.")
    tokens: List[TokenRequest] = Field(...,
                                       min_length=1,
                                       description="List of words to find in sequence.")
    date_range: Optional[DateFilter] = Field(
        None, description="Filter by creation date.")
    page: int = Field(0, description="Page number (0-indexed).")
    per_page: int = Field(10, description="Results per page.")

# Response Models


class SnippetMetadata(BaseModel):
    title: str
    author: Optional[str] = None
    date: Optional[str] = None
    doc_id: str


class SearchResultItem(BaseModel):
    metadata: SnippetMetadata
    text: str = Field(...,
                      description="Formatted text with **hits** highlighted.")


class PaginationInfo(BaseModel):
    current_page: int
    total_pages: int
    total_documents: int


class RNCResponse(BaseModel):
    """Structured response for RNC search results."""
    pagination: PaginationInfo
    results: List[SearchResultItem]
