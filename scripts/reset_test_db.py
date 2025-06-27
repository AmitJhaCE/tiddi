#!/usr/bin/env python3
"""
Database reset script for test data cleanup
Usage: python scripts/reset_test_db.py
"""

import asyncio
import asyncpg
import sys
from pathlib import Path

# Add src to path so we can import our config
sys.path.append(str(Path(__file__).parent.parent / "src"))

from config import settings

async def reset_database():
    """Reset all test data from the database"""
    print("🗑️  Starting database reset...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(settings.database_url)
        
        # Start transaction
        async with conn.transaction():
            print("📊 Getting current data counts...")
            
            # Get current counts
            notes_count = await conn.fetchval("SELECT COUNT(*) FROM notes")
            entities_count = await conn.fetchval("SELECT COUNT(*) FROM entities")
            mentions_count = await conn.fetchval("SELECT COUNT(*) FROM entity_mentions")
            users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            
            print(f"   📝 Notes: {notes_count}")
            print(f"   🏷️  Entities: {entities_count}")
            print(f"   🔗 Entity mentions: {mentions_count}")
            print(f"   👤 Users: {users_count}")
            
            # Delete all data in correct order
            print("\n🧹 Clearing data...")
            
            await conn.execute("DELETE FROM entity_mentions")
            print("   ✅ Cleared entity mentions")
            
            await conn.execute("DELETE FROM planned_intentions")
            print("   ✅ Cleared planned intentions")
            
            await conn.execute("DELETE FROM planning_sessions")
            print("   ✅ Cleared planning sessions")
            
            await conn.execute("DELETE FROM notes")
            print("   ✅ Cleared notes")
            
            await conn.execute("DELETE FROM entities")
            print("   ✅ Cleared entities")
            
            # Reset test users (keep testuser, remove others)
            deleted_users = await conn.execute(
                "DELETE FROM users WHERE username != 'testuser'"
            )
            print(f"   ✅ Cleared extra users")
            
            # Ensure testuser exists
            await conn.execute("""
                INSERT INTO users (username, email, full_name) VALUES
                ('testuser', 'test@example.com', 'Test User')
                ON CONFLICT (username) DO NOTHING
            """)
            
            # Re-insert sample entities
            await conn.execute("""
                INSERT INTO entities (canonical_name, entity_type, mention_count) VALUES
                ('AI', 'concept', 0),
                ('Machine Learning', 'concept', 0),
                ('Database Design', 'concept', 0)
                ON CONFLICT (canonical_name, entity_type) DO NOTHING
            """)
            print("   ✅ Re-inserted sample entities")
            
        # Get final counts
        print("\n📊 Final data counts:")
        final_notes = await conn.fetchval("SELECT COUNT(*) FROM notes")
        final_entities = await conn.fetchval("SELECT COUNT(*) FROM entities")
        final_mentions = await conn.fetchval("SELECT COUNT(*) FROM entity_mentions")
        final_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        
        print(f"   📝 Notes: {final_notes}")
        print(f"   🏷️  Entities: {final_entities}")
        print(f"   🔗 Entity mentions: {final_mentions}")
        print(f"   👤 Users: {final_users}")
        
        await conn.close()
        print("\n✅ Database reset completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error resetting database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(reset_database())