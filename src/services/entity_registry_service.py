import json
from typing import List, Dict, Any, Optional
from ..database import db_manager
import logging

logger = logging.getLogger(__name__)

class EntityRegistryService:
    """Advanced entity registry with deduplication, fuzzy matching, and alias management"""
    
    def __init__(self):
        # Entity type mapping from external services to database schema
        self.type_mapping = {
            "person": "person",
            "project": "project", 
            "concept": "concept",
            "organization": "concept",  # Map organization to concept
            "technology": "technology",
        }
    
    async def process_and_store_entities(
        self, 
        note_id: str, 
        raw_entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process raw entities from extraction, deduplicate, and store relationships.
        Returns the processed entities with their database IDs.
        """
        try:
            await db_manager.ensure_initialized()
            async with db_manager.get_connection() as conn:
                processed_entities = []
                
                for raw_entity in raw_entities:
                    # Process and deduplicate entity
                    entity_data = await self._process_single_entity(
                        conn, raw_entity["name"], raw_entity["type"]
                    )
                    
                    # Store note-entity relationship
                    mention_id = await self._create_entity_mention(
                        conn,
                        note_id=note_id,
                        entity_id=entity_data["id"],
                        mentioned_text=raw_entity["name"],
                        confidence=raw_entity.get("confidence", 0.5)
                    )
                    
                    processed_entities.append({
                        "id": entity_data["id"],
                        "name": entity_data["canonical_name"],
                        "type": entity_data["entity_type"],
                        "confidence": raw_entity.get("confidence", 0.5),
                        "mention_id": mention_id,
                        "is_new": entity_data["is_new"]
                    })
                
                return processed_entities
                
        except Exception as e:
            logger.error(f"Error processing entities: {e}")
            raise
    
    async def _process_single_entity(
        self, 
        conn, 
        name: str, 
        entity_type: str
    ) -> Dict[str, Any]:
        """
        Process a single entity with advanced deduplication logic.
        Returns entity data with database ID and metadata.
        """
        # Map entity type to database schema
        mapped_type = self.type_mapping.get(entity_type, "concept")
        
        # Step 1: Try exact match
        existing_entity = await self._find_exact_match(conn, name, mapped_type)
        if existing_entity:
            await self._update_entity_stats(conn, existing_entity["id"])
            return {
                "id": str(existing_entity["id"]),
                "canonical_name": existing_entity["canonical_name"],
                "entity_type": existing_entity["entity_type"],
                "is_new": False
            }
        
        # Step 2: Try fuzzy matching
        similar_entities = await self._find_fuzzy_matches(conn, name, mapped_type)
        if similar_entities:
            # Use the best match
            best_match = similar_entities[0]
            
            # Add current name as alias if different
            if name.lower() != best_match["canonical_name"].lower():
                await self._add_entity_alias(conn, best_match["id"], name)
            
            await self._update_entity_stats(conn, best_match["id"])
            return {
                "id": str(best_match["id"]),
                "canonical_name": best_match["canonical_name"],
                "entity_type": best_match["entity_type"],
                "is_new": False
            }
        
        # Step 3: Create new entity
        new_entity_id = await self._create_new_entity(conn, name, mapped_type)
        return {
            "id": str(new_entity_id),
            "canonical_name": name,
            "entity_type": mapped_type,
            "is_new": True
        }
    
    async def _find_exact_match(
        self, 
        conn, 
        name: str, 
        entity_type: str
    ) -> Optional[Dict[str, Any]]:
        """Find exact match by canonical name or aliases"""
        # Check canonical name
        result = await conn.fetchrow(
            """
            SELECT id, canonical_name, entity_type, aliases
            FROM entities 
            WHERE canonical_name = $1 AND entity_type = $2
            """,
            name, entity_type
        )
        
        if result:
            return dict(result)
        
        # Check aliases
        result = await conn.fetchrow(
            """
            SELECT id, canonical_name, entity_type, aliases
            FROM entities 
            WHERE entity_type = $1 AND aliases @> $2
            """,
            entity_type, json.dumps([name])
        )
        
        return dict(result) if result else None
    
    async def _find_fuzzy_matches(
        self, 
        conn, 
        name: str, 
        entity_type: str,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find similar entities using PostgreSQL similarity functions"""
        try:
            # Use PostgreSQL's similarity function (requires pg_trgm extension)
            results = await conn.fetch(
                """
                SELECT id, canonical_name, entity_type, 
                       similarity(canonical_name, $1) as sim_score
                FROM entities 
                WHERE entity_type = $2 
                  AND similarity(canonical_name, $1) > $3
                ORDER BY sim_score DESC
                LIMIT 5
                """,
                name, entity_type, threshold
            )
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.warning(f"Fuzzy matching failed, falling back to simple matching: {e}")
            # Fallback to simple case-insensitive matching
            results = await conn.fetch(
                """
                SELECT id, canonical_name, entity_type, 0.8 as sim_score
                FROM entities 
                WHERE entity_type = $1 
                  AND LOWER(canonical_name) LIKE LOWER($2)
                ORDER BY canonical_name
                LIMIT 3
                """,
                entity_type, f"%{name}%"
            )
            
            return [dict(row) for row in results]
    
    async def _add_entity_alias(self, conn, entity_id: str, alias: str):
        """Add an alias to an existing entity"""
        try:
            # Get current aliases
            current_aliases = await conn.fetchval(
                "SELECT aliases FROM entities WHERE id = $1",
                entity_id
            )
            
            # Parse current aliases
            aliases_list = json.loads(current_aliases) if current_aliases else []
            
            # Add new alias if not already present
            if alias not in aliases_list:
                aliases_list.append(alias)
                
                # Update entity with new aliases
                await conn.execute(
                    "UPDATE entities SET aliases = $1 WHERE id = $2",
                    json.dumps(aliases_list), entity_id
                )
                
                logger.info(f"Added alias '{alias}' to entity {entity_id}")
            
        except Exception as e:
            logger.error(f"Error adding alias: {e}")
    
    async def _update_entity_stats(self, conn, entity_id: str):
        """Update entity mention count and last seen timestamp"""
        await conn.execute(
            """
            UPDATE entities 
            SET mention_count = mention_count + 1, 
                last_seen = now(),
                updated_at = now()
            WHERE id = $1
            """,
            entity_id
        )
    
    async def _create_new_entity(
        self, 
        conn, 
        name: str, 
        entity_type: str
    ) -> str:
        """Create a new entity in the registry"""
        new_id = await conn.fetchval(
            """
            INSERT INTO entities (canonical_name, entity_type, mention_count, aliases)
            VALUES ($1, $2, 1, $3)
            RETURNING id
            """,
            name, entity_type, json.dumps([])
        )
        
        logger.info(f"Created new entity: {name} ({entity_type}) with ID {new_id}")
        return str(new_id)
    
    async def _create_entity_mention(
        self,
        conn,
        note_id: str,
        entity_id: str,
        mentioned_text: str,
        confidence: float
    ) -> str:
        """Create a relationship between note and entity"""
        mention_id = await conn.fetchval(
            """
            INSERT INTO entity_mentions (note_id, entity_id, mentioned_text, confidence)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            note_id, entity_id, mentioned_text, confidence
        )
        
        return str(mention_id)
    
    # Public API methods for entity management
    
    async def get_entity_details(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get complete entity details including aliases and stats"""
        try:
            await db_manager.ensure_initialized()
            async with db_manager.get_connection() as conn:
                result = await conn.fetchrow(
                    """
                    SELECT id, canonical_name, entity_type, aliases, mention_count,
                           first_seen, last_seen, created_at, metadata
                    FROM entities WHERE id = $1
                    """,
                    entity_id
                )
                
                if not result:
                    return None
                
                entity_data = dict(result)
                entity_data["id"] = str(entity_data["id"])
                entity_data["aliases"] = json.loads(entity_data["aliases"]) if entity_data["aliases"] else []
                entity_data["metadata"] = json.loads(entity_data["metadata"]) if entity_data["metadata"] else {}
                
                return entity_data
                
        except Exception as e:
            logger.error(f"Error getting entity details: {e}")
            return None
    
    async def merge_entities(
        self, 
        primary_entity_id: str, 
        duplicate_entity_id: str
    ) -> bool:
        """Merge duplicate entities, keeping the primary one"""
        try:
            await db_manager.ensure_initialized()
            async with db_manager.get_connection() as conn:
                async with conn.transaction():
                    # Get both entities
                    primary = await conn.fetchrow(
                        "SELECT * FROM entities WHERE id = $1", primary_entity_id
                    )
                    duplicate = await conn.fetchrow(
                        "SELECT * FROM entities WHERE id = $1", duplicate_entity_id
                    )
                    
                    if not primary or not duplicate:
                        return False
                    
                    # Merge aliases
                    primary_aliases = json.loads(primary["aliases"]) if primary["aliases"] else []
                    duplicate_aliases = json.loads(duplicate["aliases"]) if duplicate["aliases"] else []
                    
                    # Add duplicate's canonical name and aliases to primary
                    all_aliases = list(set(primary_aliases + duplicate_aliases + [duplicate["canonical_name"]]))
                    
                    # Update primary entity
                    await conn.execute(
                        """
                        UPDATE entities 
                        SET aliases = $1,
                            mention_count = mention_count + $2,
                            last_seen = GREATEST(last_seen, $3)
                        WHERE id = $4
                        """,
                        json.dumps(all_aliases),
                        duplicate["mention_count"],
                        duplicate["last_seen"],
                        primary_entity_id
                    )
                    
                    # Update all mentions to point to primary entity
                    await conn.execute(
                        "UPDATE entity_mentions SET entity_id = $1 WHERE entity_id = $2",
                        primary_entity_id, duplicate_entity_id
                    )
                    
                    # Delete duplicate entity
                    await conn.execute(
                        "DELETE FROM entities WHERE id = $1", duplicate_entity_id
                    )
                    
                    logger.info(f"Merged entity {duplicate_entity_id} into {primary_entity_id}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error merging entities: {e}")
            return False
    
    async def search_entities(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search entities by name with fuzzy matching"""
        try:
            await db_manager.ensure_initialized()
            async with db_manager.get_connection() as conn:
                base_query = """
                    SELECT id, canonical_name, entity_type, mention_count, aliases,
                           similarity(canonical_name, $1) as sim_score
                    FROM entities 
                    WHERE similarity(canonical_name, $1) > 0.3
                """
                
                params = [query]
                
                if entity_type:
                    base_query += " AND entity_type = $2"
                    params.append(entity_type)
                
                base_query += " ORDER BY sim_score DESC, mention_count DESC LIMIT $" + str(len(params) + 1)
                params.append(limit)
                
                results = await conn.fetch(base_query, *params)
                
                entities = []
                for row in results:
                    entity = dict(row)
                    entity["id"] = str(entity["id"])
                    entity["aliases"] = json.loads(entity["aliases"]) if entity["aliases"] else []
                    entities.append(entity)
                
                return entities
                
        except Exception as e:
            logger.error(f"Error searching entities: {e}")
            return []

# Global instance
entity_registry_service = EntityRegistryService()