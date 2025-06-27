import json
import os
from typing import Dict, List, Optional
from .anthropic_handler import AnthropicAsyncHandler
from ..config import settings
import logging

logger = logging.getLogger(__name__)


class EntityService:
    def __init__(self):
        # Create handler but don't initialize client yet (lazy initialization)
        self._handler: Optional[AnthropicAsyncHandler] = None

    def _get_handler(self) -> AnthropicAsyncHandler:
        """Get or create Anthropic handler with lazy initialization."""
        if self._handler is None:
            # Set up Claude handler using your settings
            os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
            self._handler = AnthropicAsyncHandler(
                config=settings.claude_config, print_response=False
            )
        return self._handler

    async def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract entities with enhanced temporal and action awareness."""
        prompt = f"""
        Extract entities from the following text and return them as a JSON array.
        
        Each entity should be an object with:
        - "name": the entity name
        - "type": one of "person", "project", "concept", "organization", "temporal", "action"
        - "confidence": a float between 0.0 and 1.0
        
        Enhanced Categories:
        - person: Names of individuals, stakeholders
        - project: Project names, initiatives, codenames, features
        - concept: Key topics, technologies, ideas, processes
        - organization: Companies, teams, departments, groups
        - temporal: Time references, deadlines, dates (e.g., "next week", "by Friday", "Q2")
        - action: Action items, tasks, deliverables (e.g., "schedule meeting", "follow up")
        
        Focus on extracting:
        1. Time-bound commitments and deadlines
        2. Action items and their ownership
        3. Dependencies and blockers
        4. Status indicators (completed, pending, blocked)
        
        Return format:
        [
            {{"name": "John Smith", "type": "person", "confidence": 0.95}},
            {{"name": "ProjectX", "type": "project", "confidence": 0.90}},
            {{"name": "next Friday", "type": "temporal", "confidence": 0.85}},
            {{"name": "schedule demo", "type": "action", "confidence": 0.80}}
        ]
        
        Text to analyze:
        {text}
        
        Return only valid JSON array, no other text.
        Dont include markdown tags like ```json.
        """

        try:
            handler = self._get_handler()
            messages = [{"role": "user", "content": prompt}]
            response = await handler.send_messages(messages)

            content = response.content[0].text if response.content else "[]"
            entities = json.loads(content)

            if not isinstance(entities, list):
                return []

            return entities

        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []

    async def close(self):
        """Close the Anthropic handler."""
        if self._handler:
            await self._handler.close()
            self._handler = None


entity_service = EntityService()
