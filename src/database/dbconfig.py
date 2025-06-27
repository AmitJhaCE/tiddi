import asyncpg
from typing import Optional
import logging
import numpy as np
from ..config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.pg_pool: Optional[asyncpg.Pool] = None
        self._initialized = False
        logger.info("DatabaseManager initialized")

    async def ensure_initialized(self):
        """Ensure database is initialized (call this before any operation)"""
        if not self._initialized:
            await self.initialize()

    async def initialize(self):
        """Initialize PostgreSQL connection with pgvector"""
        if self._initialized:
            logger.info("Database already initialized")
            return

        logger.info("Starting database initialization...")
        try:
            await self._init_postgresql()
            self._initialized = True
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
                init=self._setup_vector_type,
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

            logger.info("PostgreSQL initialized successfully")
        except Exception as e:
            logger.error(f"PostgreSQL initialization failed: {e}")
            raise

    async def _setup_vector_type(self, conn):
        """Setup vector type for asyncpg"""
        try:
            await conn.set_type_codec(
                "vector",
                encoder=self._encode_vector,
                decoder=self._decode_vector,
                schema="public",
            )
            logger.debug("Vector type codec registered")
        except Exception as e:
            logger.warning(f"Vector type codec registration failed: {e}")

    def _encode_vector(self, vector):
        """Encode numpy array to vector format"""
        if isinstance(vector, list):
            vector = np.array(vector)
        return f"[{','.join(map(str, vector))}]"

    def _decode_vector(self, vector_str):
        """Decode vector string to numpy array"""
        values = vector_str.strip("[]").split(",")
        return np.array([float(v) for v in values])

    async def close(self):
        """Close database connections"""
        if self.pg_pool:
            await self.pg_pool.close()
            self._initialized = False
            logger.info("PostgreSQL connections closed")

    def get_connection(self):
        """Get database connection context manager"""
        if not self._initialized or not self.pg_pool:
            raise Exception(
                "PostgreSQL pool not initialized. Call ensure_initialized() first."
            )
        return self.pg_pool.acquire()

    def get_pg_pool(self) -> asyncpg.Pool:
        """Get the connection pool directly"""
        if not self.pg_pool:
            raise Exception("PostgreSQL pool not initialized")
        return self.pg_pool

    async def health_check(self):
        """Perform health check on PostgreSQL"""
        health_status = {}

        try:
            await self.ensure_initialized()  # Auto-initialize if needed
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
