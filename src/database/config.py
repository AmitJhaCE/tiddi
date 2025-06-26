import asyncpg
from typing import Optional, List, Dict, Any
import logging
import numpy as np
from config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.pg_pool: Optional[asyncpg.Pool] = None
        logger.info("DatabaseManager initialized")

    async def initialize(self):
        """Initialize PostgreSQL connection with pgvector"""
        logger.info("Starting database initialization...")
        try:
            await self._init_postgresql()
            logger.info("Database initialization completed successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def _init_postgresql(self):
        """Initialize PostgreSQL connection pool with pgvector support"""
        logger.info(f"Connecting to PostgreSQL: {settings.database_url}")
        try:
            self.pg_pool = await asyncpg.create_pool(
                settings.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60,
                # Register vector type
                init=self._setup_vector_type
            )
            
            # Test connection and pgvector extension
            async with self.pg_pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                if result != 1:
                    raise Exception("PostgreSQL connection test failed")
                
                # Test pgvector extension
                try:
                    vector_test = await conn.fetchval("SELECT '[1,2,3]'::vector")
                    logger.info("pgvector extension test successful")
                except Exception as e:
                    logger.warning(f"pgvector extension test failed: {e}")
                    # Continue without pgvector for now
                    
            logger.info("PostgreSQL initialized successfully")
        except Exception as e:
            logger.error(f"PostgreSQL initialization failed: {e}")
            raise

    async def _setup_vector_type(self, conn):
        """Setup vector type for asyncpg"""
        try:
            await conn.set_type_codec(
                'vector',
                encoder=self._encode_vector,
                decoder=self._decode_vector,
                schema='public'
            )
            logger.debug("Vector type codec registered")
        except Exception as e:
            logger.warning(f"Vector type codec registration failed: {e}")
            # Continue without vector codec

    def _encode_vector(self, vector):
        """Encode numpy array to vector format"""
        if isinstance(vector, list):
            vector = np.array(vector)
        return f"[{','.join(map(str, vector))}]"

    def _decode_vector(self, vector_str):
        """Decode vector string to numpy array"""
        # Remove brackets and split by comma
        values = vector_str.strip('[]').split(',')
        return np.array([float(v) for v in values])

    async def close(self):
        """Close database connections"""
        if self.pg_pool:
            await self.pg_pool.close()
            logger.info("PostgreSQL connections closed")

    def get_pg_pool(self) -> asyncpg.Pool:
        if not self.pg_pool:
            raise Exception("PostgreSQL pool not initialized")
        return self.pg_pool

    async def store_note_with_embedding(
        self, 
        user_id: str, 
        text: str, 
        embedding: List[float], 
        session_id: Optional[str] = None,
        entities: List[Dict] = None,
        tags: List[str] = None
    ) -> str:
        """Store note with vector embedding"""
        async with self.pg_pool.acquire() as conn:
            note_id = await conn.fetchval("""
                INSERT INTO notes (user_id, text, embedding, session_id, extracted_entities, tags)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, user_id, text, embedding, session_id, entities or [], tags or [])
            return str(note_id)

    async def search_notes_semantic(
        self, 
        user_id: str, 
        query_embedding: List[float], 
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search notes using vector similarity"""
        async with self.pg_pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT id, text, timestamp, extracted_entities, tags,
                       1 - (embedding <=> $2) as similarity
                FROM notes 
                WHERE user_id = $1 
                  AND 1 - (embedding <=> $2) > $4
                ORDER BY embedding <=> $2
                LIMIT $3
            """, user_id, query_embedding, limit, similarity_threshold)
            
            return [dict(record) for record in results]

    async def search_notes_fulltext(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search notes using full-text search"""
        async with self.pg_pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT id, text, timestamp, extracted_entities, tags,
                       ts_rank(text_search_vector, plainto_tsquery('english', $2)) as text_rank
                FROM notes 
                WHERE user_id = $1 
                  AND text_search_vector @@ plainto_tsquery('english', $2)
                ORDER BY ts_rank(text_search_vector, plainto_tsquery('english', $2)) DESC
                LIMIT $3
            """, user_id, query, limit)
            
            return [dict(record) for record in results]

    async def health_check(self):
        """Perform health check on PostgreSQL"""
        health_status = {}
        
        try:
            if self.pg_pool:
                async with self.pg_pool.acquire() as conn:
                    # Test basic connection
                    await conn.fetchval("SELECT 1")
                    health_status["postgresql"] = "healthy"
                    
                    # Test pgvector extension
                    try:
                        await conn.fetchval("SELECT '[1,2,3]'::vector")
                        health_status["pgvector"] = "healthy"
                    except Exception as e:
                        health_status["pgvector"] = f"unavailable: {str(e)}"
                        
            else:
                health_status["postgresql"] = "not initialized"
                health_status["pgvector"] = "not initialized"
        except Exception as e:
            health_status["postgresql"] = f"unhealthy: {str(e)}"
            health_status["pgvector"] = "unhealthy"
        
        return health_status

# Global database manager instance
db_manager = DatabaseManager()