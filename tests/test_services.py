import pytest
import asyncio
from src.services.entity_service import entity_service
from src.services.openai_service import openai_service

class TestEntityService:
    def test_entity_extraction(self):
        """Test entity extraction - sync wrapper"""
        async def _test():
            text = "John Smith discussed the ReactApp project using TypeScript"
            entities = await entity_service.extract_entities(text)
            assert len(entities) > 0
            entity_names = [e["name"] for e in entities]
            assert any("John" in name for name in entity_names)
        
        # Run async test in sync context
        asyncio.run(_test())

class TestEmbeddings:
    def test_embedding_generation(self):
        """Test OpenAI embedding generation - sync wrapper"""
        async def _test():
            text = "This is a test note about AI and machine learning"
            embedding = await openai_service.generate_embeddings(text)
            assert len(embedding) == 1536
            assert all(isinstance(x, float) for x in embedding)
        
        # Run async test in sync context
        asyncio.run(_test())