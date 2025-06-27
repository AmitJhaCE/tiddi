import logging
import time
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from contextlib import asynccontextmanager
from .services.note_service import note_service
from .config import settings
from .database import db_manager
from .models.base import HealthResponse, StoreNoteRequest, StoreNoteResponse
from .models.search import SearchNotesResponse, SearchMetadata
from .models.notes import BulkStoreNotesRequest, BulkStoreNotesResponse, BulkNoteResult


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with proper async client cleanup"""
    # Startup
    logger.info("Starting Work Management API...")
    try:
        await db_manager.initialize()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    # Shutdown - Clean up async clients
    logger.info("Shutting down Work Management API...")
    try:
        # Import services here to avoid circular imports
        from .services.openai_service import openai_service
        from .services.entity_service import entity_service
        
        # Close async clients
        await openai_service.close()
        await entity_service.close()
        
        # Close database connections
        await db_manager.close()
        
        logger.info("Application shutdown completed successfully")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

# Create FastAPI application
app = FastAPI(
    title="Work Management Tools",
    description="LLM-powered work management and knowledge system",
    version="1.0.0",
    lifespan=lifespan,
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
    overall_healthy = all("healthy" in status.lower() for status in services.values())

    return HealthResponse(
        success=overall_healthy,
        services=services,
        message=f"Health check completed in {response_time}ms",
        version="1.0.0",
    )


# Store_note_tool function:
@app.post("/tools/notes", response_model=StoreNoteResponse, tags=["Tools"])
async def store_note_tool(
    request: StoreNoteRequest, user_id: str = Depends(get_current_user_id)
):
    """Store work note with automatic entity extraction"""
    try:
        result = await note_service.store_note(
            content=request.text,
            user_id=user_id,
            tags=request.tags,
            session_id=request.session_id,
        )

        return StoreNoteResponse(
            note_id=result["note_id"],
            entities=result["entities"],
            message=f"Note stored successfully in {result['processing_time_ms']}ms",
        )
    except Exception as e:
        logger.error(f"Error storing note: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store note: {str(e)}")


# Bulk store_note_tool
@app.post("/tools/notes/bulk", response_model=BulkStoreNotesResponse, tags=["Tools"])
async def store_notes_bulk_tool(
    request: BulkStoreNotesRequest, user_id: str = Depends(get_current_user_id)
):
    """Store multiple work notes at once with parallel processing"""
    try:
        # Convert request to format expected by service
        notes_data = [
            {"text": note.text, "tags": note.tags, "session_id": note.session_id}
            for note in request.notes
        ]

        result = await note_service.store_notes_bulk(
            notes_data=notes_data,
            user_id=user_id,
            session_id=request.session_id,
        )

        # Convert service response to API response format
        stored_notes = [
            BulkNoteResult(
                note_id=note["note_id"],
                entities=note["entities"],
                processing_time_ms=note["processing_time_ms"],
                success=note["success"],
                error=note.get("error"),
            )
            for note in result["stored_notes"]
        ]

        failed_notes = [
            BulkNoteResult(
                note_id=note["note_id"],
                entities=note["entities"],
                processing_time_ms=note["processing_time_ms"],
                success=note["success"],
                error=note.get("error"),
            )
            for note in result["failed_notes"]
        ]

        return BulkStoreNotesResponse(
            stored_notes=stored_notes,
            failed_notes=failed_notes,
            total_processed=result["total_processed"],
            success_count=result["success_count"],
            failure_count=result["failure_count"],
            total_processing_time_ms=result["total_processing_time_ms"],
            message=f"Processed {result['total_processed']} notes in {result['total_processing_time_ms']}ms",
        )

    except Exception as e:
        logger.error(f"Error in bulk note storage: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk storage failed: {str(e)}")


@app.get("/tools/notes/search", response_model=SearchNotesResponse, tags=["Tools"])
async def search_notes_tool(
    query: str = Query(..., description="Search query"),
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    days_back: Optional[int] = Query(30, description="Days to search back"),
    entity_filter: Optional[str] = Query(None, description="Filter by entity"),
):
    """Search notes using semantic similarity"""
    try:
        result = await note_service.search_notes(
            query=query,
            user_id=user_id,
            limit=limit,
            days_back=days_back,
            entity_filter=entity_filter,
        )

        # CREATE proper metadata
        metadata = SearchMetadata(
            total_found=result["total_found"],
            query_time_ms=result["query_time_ms"],
            query=query,
            filters_applied={
                "days_back": days_back,
                "entity_filter": entity_filter,
                "limit": limit,
            },
        )

        return SearchNotesResponse(
            results=result["results"],
            metadata=metadata,
            message=f"Search completed in {result['query_time_ms']}ms",
        )
    except Exception as e:
        logger.error(f"Error searching notes: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """API root endpoint"""
    return {
        "message": "Work Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "environment": settings.environment,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower(),
    )
