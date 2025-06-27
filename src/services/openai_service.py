from typing import List, Optional
from openai import AsyncOpenAI
from ..config import settings
import logging
import os

logger = logging.getLogger(__name__)


class OpenAIService:
    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None
        self._client_closed = False

    async def _get_client(self) -> AsyncOpenAI:
        """Get or create async client with lifecycle management."""
        if self._client is None or self._client_closed:
            self._client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                timeout=30.0,  # Add reasonable timeout
                max_retries=(
                    2 if os.getenv("ENVIRONMENT") == "testing" else 3
                ),  # Fewer retries in tests
            )
            self._client_closed = False
        return self._client

    async def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for given text using OpenAI."""
        try:
            client = await self._get_client()
            response = await client.embeddings.create(
                model="text-embedding-3-small", input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    async def close(self):
        """Close the async client."""
        if self._client and not self._client_closed:
            try:
                await self._client.close()
                logger.info("OpenAI client closed successfully")
            except Exception as e:
                logger.warning(f"Error closing OpenAI client: {e}")
            finally:
                self._client_closed = True
                self._client = None


# Global instance
openai_service = OpenAIService()
