from pydantic import BaseModel, Field
from typing import List, Dict, Any  # Make sure Any is imported
from .base import BaseResponse
from .notes import NoteSearchResult

class SearchMetadata(BaseModel):
    """Search execution metadata"""
    total_found: int
    query_time_ms: int
    query: str
    filters_applied: Dict[str, Any] = Field(default_factory=dict)  
    search_type: str = "hybrid"  # hybrid, semantic, fulltext

class SearchNotesResponse(BaseResponse):
    """Enhanced search response with proper models"""
    results: List[NoteSearchResult] = Field(default_factory=list)
    metadata: SearchMetadata