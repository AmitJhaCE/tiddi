import asyncio
import time
from typing import Dict, List, Any, Optional
from .openai_service import openai_service
from .entity_service import entity_service
from .entity_registry_service import entity_registry_service
from .database_service import database_service
import logging

logger = logging.getLogger(__name__)


class NoteService:
    async def store_note(
        self,
        content: str,
        user_id: str,
        tags: List[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Store note with full processing pipeline."""
        start_time = time.time()
        try:
            # Run embedding generation and entity extraction in parallel
            embedding_task = openai_service.generate_embeddings(content)
            entities_task = entity_service.extract_entities(content)
            embedding, raw_entities = await asyncio.gather(
                embedding_task, entities_task
            )

            # Store note with embedding and raw extracted entities
            note_id = await database_service.store_note_with_embedding(
                text=content,
                embedding=embedding,
                user_id=user_id,
                session_id=session_id,
                tags=tags,
                extracted_entities=raw_entities,  # Store raw entities in note
            )

            # Process entities through registry (deduplication, aliases, relationships)
            processed_entities = (
                await entity_registry_service.process_and_store_entities(
                    note_id=note_id, raw_entities=raw_entities
                )
            )

            processing_time = int((time.time() - start_time) * 1000)
            return {
                "note_id": note_id,
                "entities": raw_entities,  # Return original entities for API compatibility
                "processed_entities": processed_entities,  # Return processed entities with IDs
                "processing_time_ms": processing_time,
                "embedding_dimensions": len(embedding),
                "session_id": session_id,
                "tags": tags,
            }
        except Exception as e:
            logger.error(f"Error storing note: {e}")
            raise

    async def store_notes_bulk(
        self,
        notes_data: List[Dict[str, Any]],
        user_id: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Store multiple notes with parallel processing and error isolation."""
        start_time = time.time()

        stored_notes = []
        failed_notes = []

        # Process notes with controlled concurrency
        semaphore = asyncio.Semaphore(5)  # Limit concurrent processing

        async def process_single_note(note_data: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                note_start = time.time()
                try:
                    result = await self.store_note(
                        content=note_data["text"],
                        user_id=user_id,
                        tags=note_data.get("tags", []),
                        session_id=session_id or note_data.get("session_id"),
                    )

                    processing_time = int((time.time() - note_start) * 1000)
                    return {
                        "note_id": result["note_id"],
                        "entities": result["entities"],
                        "processing_time_ms": processing_time,
                        "success": True,
                        "error": None,
                    }
                except Exception as e:
                    processing_time = int((time.time() - note_start) * 1000)
                    logger.error(f"Failed to process note: {e}")
                    return {
                        "note_id": None,
                        "entities": [],
                        "processing_time_ms": processing_time,
                        "success": False,
                        "error": str(e),
                    }

        # Process all notes concurrently
        tasks = [process_single_note(note_data) for note_data in notes_data]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Separate successful and failed results
        for result in results:
            if isinstance(result, Exception):
                failed_notes.append(
                    {
                        "note_id": None,
                        "entities": [],
                        "processing_time_ms": 0,
                        "success": False,
                        "error": str(result),
                    }
                )
            elif result["success"]:
                stored_notes.append(result)
            else:
                failed_notes.append(result)

        total_processing_time = int((time.time() - start_time) * 1000)

        return {
            "stored_notes": stored_notes,
            "failed_notes": failed_notes,
            "total_processed": len(notes_data),
            "success_count": len(stored_notes),
            "failure_count": len(failed_notes),
            "total_processing_time_ms": total_processing_time,
            "session_id": session_id,
        }

    async def search_notes(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        days_back: Optional[int] = None,
        entity_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search notes using hybrid search."""
        start_time = time.time()
        try:
            # Generate embedding for search query
            query_embedding = await openai_service.generate_embeddings(query)

            # Perform search
            results = await database_service.hybrid_search(
                query, query_embedding, limit, user_id, days_back, entity_filter
            )

            search_time = int((time.time() - start_time) * 1000)
            return {
                "results": results,
                "total_found": len(results),
                "query_time_ms": search_time,
            }
        except Exception as e:
            logger.error(f"Error searching notes: {e}")
            raise


# Global instance
note_service = NoteService()
