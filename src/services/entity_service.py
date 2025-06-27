import json
import os
from typing import Dict, List
from .anthropic_handler import AnthropicAsyncHandler
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class EntityService:
    def __init__(self):
        # Set up Claude handler using your settings
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
        self.claude_handler = AnthropicAsyncHandler(
            config=settings.claude_config,
            print_response=False
        )
    
    async def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract entities from text using Claude and return in your expected format."""
        prompt = f"""
        Extract entities from the following text and return them as a JSON array.
        
        Each entity should be an object with:
        - "name": the entity name
        - "type": one of "person", "project", "concept", "organization"
        - "confidence": a float between 0.0 and 1.0
        
        Categories:
        - person: Names of individuals
        - project: Project names, initiatives, or codenames  
        - concept: Key topics, technologies, or ideas discussed
        - organization: Companies, teams, or groups mentioned
        
        Return format:
        [
            {{"name": "John Smith", "type": "person", "confidence": 0.95}},
            {{"name": "ProjectX", "type": "project", "confidence": 0.90}}
        ]
        
        Text to analyze:
        {text}
        
        Return only valid JSON array, no other text. 
        Dont include markdown tags like ```json.
        """
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.claude_handler.send_messages(messages)
            
            # Extract JSON from response
            content = response.content[0].text if response.content else "[]"
            entities = json.loads(content)
            
            # Ensure it's a list
            if not isinstance(entities, list):
                return []
                
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []

entity_service = EntityService()