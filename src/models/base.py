from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# Keep existing models
class BaseResponse(BaseModel):
    success: bool = True
    message: str = "Operation completed successfully"
    timestamp: datetime = Field(default_factory=datetime.now)

class HealthResponse(BaseResponse):
    services: Dict[str, str] = Field(default_factory=dict)
    version: str = "1.0.0"

# Keep existing request models - they're fine
class StoreNoteRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Work note content")
    tags: Optional[List[str]] = Field(default=[], description="Optional tags")
    session_id: Optional[str] = Field(None, description="Chat session identifier")

# UPDATE: Use new note model
class StoreNoteResponse(BaseResponse):
    note_id: str
    entities: List[Dict[str, Any]] = Field(default_factory=list)  # Keep for backward compatibility
    processing_time_ms: int = 0
    embedding_dimensions: int = 0

# ADD: Model conversion utilities
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import asyncpg

def convert_db_row_to_dict(row: 'asyncpg.Record') -> Dict[str, Any]:
    """Convert database row to dictionary with proper type conversion"""
    import json
    
    result = dict(row)
    
    # Convert UUID to string
    if 'id' in result and result['id']:
        result['id'] = str(result['id'])
    if 'user_id' in result and result['user_id']:
        result['user_id'] = str(result['user_id'])
    
    # Parse JSON fields
    json_fields = ['tags', 'extracted_entities', 'metadata', 'linked_entities']
    for field in json_fields:
        if field in result and result[field]:
            if isinstance(result[field], str):
                try:
                    result[field] = json.loads(result[field])
                except (json.JSONDecodeError, TypeError):
                    result[field] = []
    
    return result