from typing import List
from openai import AsyncOpenAI
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for given text using OpenAI."""
        try:
            response = await self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

# Global instance
openai_service = OpenAIService()