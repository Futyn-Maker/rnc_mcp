from typing import List, Optional, Literal
from pydantic import BaseModel, Field


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
    # Distance is relative to the PREVIOUS token in the list
    dist_min: int = Field(1, description="Min distance from previous word.")
    dist_max: int = Field(1, description="Max distance from previous word.")


class DateFilter(BaseModel):
    start_year: Optional[int] = None
    end_year: Optional[int] = None


class SearchQuery(BaseModel):
    """The main input model for the search tool."""
    corpus: Literal["MAIN", "PAPER", "POETIC", "SPOKEN"] = "MAIN"
    tokens: List[TokenRequest] = Field(..., min_length=1, description="List of words to find in sequence.")
    date_range: Optional[DateFilter] = Field(None, description="Filter by creation date.")
    page: int = Field(0, description="Page number (0-indexed).")
    per_page: int = Field(10, description="Results per page.")
