from typing import List, Dict, Any, Optional
import json
from ..database import db_manager
from ..config import settings
import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database service focused on core data storage and retrieval operations"""

    async def store_note_with_embedding(
        self,
        text: str,
        embedding: List[float],
        user_id: str,
        session_id: Optional[str] = None,
        tags: List[str] = None,
        extracted_entities: List[Dict] = None,
    ) -> str:
        """Store note with embedding, respecting max_note_length."""
        # Truncate text if needed
        if len(text) > settings.max_note_length:
            text = text[: settings.max_note_length]
            logger.warning(f"Note truncated to {settings.max_note_length} characters")

        try:
            # Ensure database is initialized
            await db_manager.ensure_initialized()
            async with db_manager.get_connection() as conn:
                # Get user UUID from username (assuming user_id is username)
                user_uuid = await conn.fetchval(
                    "SELECT id FROM users WHERE username = $1", user_id
                )
                if not user_uuid:
                    raise Exception(f"User '{user_id}' not found")

                # Convert Python objects to JSON strings for JSONB columns
                tags_json = json.dumps(tags or [])
                entities_json = json.dumps(extracted_entities or [])

                query = """
                    INSERT INTO notes (text, embedding, user_id, session_id, tags, extracted_entities)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                """
                note_id = await conn.fetchval(
                    query,
                    text,
                    embedding,
                    user_uuid,
                    session_id,
                    tags_json,
                    entities_json,
                )
                return str(note_id)
        except Exception as e:
            logger.error(f"Error storing note: {e}")
            raise

    async def get_note_by_id(
        self, note_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a single note by ID for detailed response"""
        try:
            await db_manager.ensure_initialized()
            async with db_manager.get_connection() as conn:
                user_uuid = await conn.fetchval(
                    "SELECT id FROM users WHERE username = $1", user_id
                )
                if not user_uuid:
                    raise Exception(f"User '{user_id}' not found")

                row = await conn.fetchrow(
                    """
                    SELECT n.*, COALESCE(entity_names.entities, '[]'::json) as linked_entities
                    FROM notes n
                    LEFT JOIN (
                        SELECT
                            em.note_id,
                            json_agg(json_build_object(
                                'name', e.canonical_name,
                                'type', e.entity_type,
                                'confidence', em.confidence
                            )) as entities
                        FROM entity_mentions em
                        JOIN entities e ON em.entity_id = e.id
                        GROUP BY em.note_id
                    ) entity_names ON n.id = entity_names.note_id
                    WHERE n.id = $1 AND n.user_id = $2
                    """,
                    note_id,
                    user_uuid,
                )

                return self._convert_db_row_to_dict(row) if row else None

        except Exception as e:
            logger.error(f"Error getting note by ID: {e}")
            raise

    async def hybrid_search(
        self,
        query_text: str,
        query_embedding: List[float],
        limit: int,
        user_id: str,
        days_back: Optional[int] = None,
        entity_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search with filters."""
        try:
            await db_manager.ensure_initialized()
            async with db_manager.get_connection() as conn:
                # Get user UUID from username
                user_uuid = await conn.fetchval(
                    "SELECT id FROM users WHERE username = $1", user_id
                )
                if not user_uuid:
                    raise Exception(f"User '{user_id}' not found")

                # Build dynamic query based on filters
                where_conditions = ["n.user_id = $3"]
                params = [query_text, query_embedding, user_uuid]

                # Add days_back filter if provided
                if days_back:
                    where_conditions.append(
                        f"n.timestamp >= NOW() - INTERVAL '{days_back} days'"
                    )

                # Add entity filter if provided
                if entity_filter:
                    where_conditions.append(
                        """EXISTS (
                            SELECT 1 FROM entity_mentions em
                            JOIN entities e ON em.entity_id = e.id
                            WHERE em.note_id = n.id AND e.canonical_name ILIKE $4
                        )"""
                    )
                    params.append(f"%{entity_filter}%")

                where_clause = " AND ".join(where_conditions)

                # Check if pgvector is available
                vector_available = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )

                if vector_available:
                    search_query = f"""
                        SELECT
                            n.id,
                            n.text,
                            n.timestamp,
                            n.session_id,
                            n.tags,
                            n.extracted_entities,
                            1 - (n.embedding <=> $2) as similarity_score,
                            ts_rank(n.text_search_vector, plainto_tsquery('english', $1)) as text_rank,
                            COALESCE(entity_names.entities, '[]'::json) as linked_entities
                        FROM notes n
                        LEFT JOIN (
                            SELECT
                                em.note_id,
                                json_agg(json_build_object(
                                    'name', e.canonical_name,
                                    'type', e.entity_type,
                                    'confidence', em.confidence
                                )) as entities
                            FROM entity_mentions em
                            JOIN entities e ON em.entity_id = e.id
                            GROUP BY em.note_id
                        ) entity_names ON n.id = entity_names.note_id
                        WHERE {where_clause}
                            AND (n.embedding <=> $2 < 0.8
                                 OR n.text_search_vector @@ plainto_tsquery('english', $1))
                        ORDER BY
                            (COALESCE(1 - (n.embedding <=> $2), 0) * 0.7 +
                             COALESCE(ts_rank(n.text_search_vector, plainto_tsquery('english', $1)), 0) * 0.3) DESC
                        LIMIT {limit}
                    """
                else:
                    # Fallback to text search only
                    search_query = f"""
                        SELECT
                            n.id,
                            n.text,
                            n.timestamp,
                            n.session_id,
                            n.tags,
                            n.extracted_entities,
                            0.5 as similarity_score,
                            ts_rank(n.text_search_vector, plainto_tsquery('english', $1)) as text_rank,
                            COALESCE(entity_names.entities, '[]'::json) as linked_entities
                        FROM notes n
                        LEFT JOIN (
                            SELECT
                                em.note_id,
                                json_agg(json_build_object(
                                    'name', e.canonical_name,
                                    'type', e.entity_type,
                                    'confidence', em.confidence
                                )) as entities
                            FROM entity_mentions em
                            JOIN entities e ON em.entity_id = e.id
                            GROUP BY em.note_id
                        ) entity_names ON n.id = entity_names.note_id
                        WHERE {where_clause.replace('$2', '$1').replace('$3', '$2').replace('$4', '$3')}
                            AND n.text_search_vector @@ plainto_tsquery('english', $1)
                        ORDER BY ts_rank(n.text_search_vector, plainto_tsquery('english', $1)) DESC
                        LIMIT {limit}
                    """
                    # Adjust parameters for text-only search (remove embedding parameter)
                    params = [query_text, user_uuid] + (
                        [f"%{entity_filter}%"] if entity_filter else []
                    )

                rows = await conn.fetch(search_query, *params)

                # Convert rows and add computed fields
                results = []
                for row in rows:
                    result = self._convert_db_row_to_dict(row)

                    # Add computed relevance score
                    similarity = result.get("similarity_score", 0) or 0
                    text_rank = result.get("text_rank", 0) or 0
                    result["relevance_score"] = (similarity * 0.7) + (text_rank * 0.3)

                    results.append(result)

                return results

        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            raise

    async def search_notes_semantic(
        self,
        user_id: str,
        query_embedding: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Search notes using vector similarity only."""
        try:
            await db_manager.ensure_initialized()
            async with db_manager.get_connection() as conn:
                # Get user UUID from username
                user_uuid = await conn.fetchval(
                    "SELECT id FROM users WHERE username = $1", user_id
                )
                if not user_uuid:
                    raise Exception(f"User '{user_id}' not found")

                results = await conn.fetch(
                    """
                    SELECT id, text, timestamp, tags, extracted_entities,
                           1 - (embedding <=> $2) as similarity
                    FROM notes
                    WHERE user_id = $1
                      AND embedding IS NOT NULL
                      AND 1 - (embedding <=> $2) > $3
                    ORDER BY embedding <=> $2
                    LIMIT $4
                """,
                    user_uuid,
                    query_embedding,
                    similarity_threshold,
                    limit,
                )
                return [self._convert_db_row_to_dict(record) for record in results]
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            raise

    async def search_notes_fulltext(
        self, user_id: str, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search notes using full-text search only."""
        try:
            await db_manager.ensure_initialized()
            async with db_manager.get_connection() as conn:
                # Get user UUID from username
                user_uuid = await conn.fetchval(
                    "SELECT id FROM users WHERE username = $1", user_id
                )
                if not user_uuid:
                    raise Exception(f"User '{user_id}' not found")

                results = await conn.fetch(
                    """
                    SELECT id, text, timestamp, tags, extracted_entities,
                           ts_rank(text_search_vector, plainto_tsquery('english', $2)) as text_rank
                    FROM notes
                    WHERE user_id = $1
                      AND text_search_vector @@ plainto_tsquery('english', $2)
                    ORDER BY ts_rank(text_search_vector, plainto_tsquery('english', $2)) DESC
                    LIMIT $3
                """,
                    user_uuid,
                    query,
                    limit,
                )
                return [self._convert_db_row_to_dict(record) for record in results]
        except Exception as e:
            logger.error(f"Error in fulltext search: {e}")
            raise

    def _convert_db_row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary with proper type conversion"""
        if not row:
            return {}

        result = dict(row)

        # Convert UUID to string
        if "id" in result and result["id"]:
            result["id"] = str(result["id"])
        if "user_id" in result and result["user_id"]:
            result["user_id"] = str(result["user_id"])

        # Parse JSON fields
        json_fields = ["tags", "extracted_entities", "metadata", "linked_entities"]
        for field in json_fields:
            if field in result and result[field]:
                if isinstance(result[field], str):
                    try:
                        result[field] = json.loads(result[field])
                    except (json.JSONDecodeError, TypeError):
                        result[field] = []

        return result


# Global instance
database_service = DatabaseService()
