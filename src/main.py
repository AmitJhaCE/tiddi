from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
import logging
import time
from typing import Optional
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from database.config import db_manager
from models.base import (
    HealthResponse,
    StoreNoteRequest,
    StoreNoteResponse,
    SearchNotesRequest,
    SearchNotesResponse
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Work Management API...")
    try:
        await db_manager.initialize()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Work Management API...")
    await db_manager.close()
    logger.info("Application shutdown completed")

# Create FastAPI application
app = FastAPI(
    title="Work Management Tools",
    description="LLM-powered work management and knowledge system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom OpenAPI schema for better tool integration
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Work Management Tools",
        version="1.0.0",
        description="Tools for intelligent work management through LLM chat interface",
        routes=app.routes,
    )
    
    # Enhance for LLM tool usage
    for path_data in openapi_schema.get("paths", {}).values():
        for operation in path_data.values():
            if isinstance(operation, dict):
                operation["x-openai-isConsequential"] = False
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Dependency to get current user (placeholder for now)
async def get_current_user_id() -> str:
    """Get current user ID - placeholder implementation"""
    return "testuser"

# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """System health check"""
    start_time = time.time()
    
    # Use the database manager's health check method
    services = await db_manager.health_check()
    
    response_time = int((time.time() - start_time) * 1000)
    
    # Determine overall health
    overall_healthy = all(
        "healthy" in status.lower() 
        for status in services.values()
    )
    
    return HealthResponse(
        success=overall_healthy,
        services=services,
        message=f"Health check completed in {response_time}ms",
        version="1.0.0"
    )

# Basic endpoints (placeholders for Phase 2)
@app.post("/tools/notes", response_model=StoreNoteResponse, tags=["Tools"])
async def store_note_tool(
    request: StoreNoteRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Store work note with automatic entity extraction"""
    # Placeholder implementation
    note_id = "placeholder-note-id"
    return StoreNoteResponse(
        note_id=note_id,
        entities=[],
        message="Note stored successfully (placeholder)"
    )

@app.get("/tools/notes/search", response_model=SearchNotesResponse, tags=["Tools"])
async def search_notes_tool(
    query: str = Query(..., description="Search query"),
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    days_back: Optional[int] = Query(30, description="Days to search back"),
    entity_filter: Optional[str] = Query(None, description="Filter by entity")
):
    """Search notes using semantic similarity"""
    # Placeholder implementation
    return SearchNotesResponse(
        results=[],
        total_found=0,
        message="Search completed (placeholder)"
    )

# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """API root endpoint"""
    return {
        "message": "Work Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "environment": settings.environment
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )