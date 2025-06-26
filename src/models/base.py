from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID

class BaseResponse(BaseModel):
    success: bool = True
    message: str = "Operation completed successfully"
    timestamp: datetime = Field(default_factory=datetime.now)

class HealthResponse(BaseResponse):
    services: Dict[str, str] = Field(default_factory=dict)
    version: str = "1.0.0"

class StoreNoteRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Work note content")
    tags: Optional[List[str]] = Field(default=[], description="Optional tags")
    session_id: Optional[str] = Field(None, description="Chat session identifier")

class StoreNoteResponse(BaseResponse):
    note_id: str
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

class SearchNotesRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results")
    days_back: Optional[int] = Field(default=30, ge=1, description="Days to search back")
    entity_filter: Optional[str] = Field(None, description="Filter by entity name")

class SearchNotesResponse(BaseResponse):
    results: List[Dict[str, Any]] = Field(default_factory=list)
    total_found: int = 0
    query_time_ms: int = 0