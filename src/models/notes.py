from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from .base import StoreNoteRequest, BaseResponse

class EntityMention(BaseModel):
    """Entity extracted from or linked to a note"""
    name: str
    type: str  # person, project, concept, technology
    confidence: float = Field(ge=0.0, le=1.0)

class NoteBase(BaseModel):
    """Base note fields"""
    text: str
    tags: List[str] = Field(default_factory=list)
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class NoteDetail(NoteBase):
    """Complete note with all database fields"""
    id: str
    user_id: str
    timestamp: datetime
    created_at: datetime
    updated_at: datetime
    extracted_entities: List[EntityMention] = Field(default_factory=list)
    linked_entities: List[EntityMention] = Field(default_factory=list)
    
class NoteSearchResult(NoteBase):
    """Note in search results with relevance scoring"""
    id: str
    timestamp: datetime
    extracted_entities: List[EntityMention] = Field(default_factory=list)
    linked_entities: List[EntityMention] = Field(default_factory=list)
    relevance_score: float = Field(ge=0.0, le=1.0, description="Combined relevance score")
    similarity_score: Optional[float] = Field(None, description="Semantic similarity score")
    text_rank: Optional[float] = Field(None, description="Full-text search rank")

# Models for Bulk Store 
class BulkStoreNotesRequest(BaseModel):
    """Request for bulk note storage"""
    notes: List[StoreNoteRequest] = Field(..., min_items=1, max_items=50)
    session_id: Optional[str] = Field(None, description="Bulk session identifier")

class BulkNoteResult(BaseModel):
    """Individual note result in bulk operation"""
    note_id: Optional[str] = None
    entities: List[EntityMention] = Field(default_factory=list)
    processing_time_ms: int = 0
    error: Optional[str] = None
    success: bool = True

class BulkStoreNotesResponse(BaseResponse):
    """Response for bulk note storage"""
    stored_notes: List[BulkNoteResult] = Field(default_factory=list)
    total_processed: int = 0
    total_processing_time_ms: int = 0
    failed_notes: List[BulkNoteResult] = Field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0