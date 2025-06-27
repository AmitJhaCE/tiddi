-- Create database if it doesn't exist (commented out as Docker handles this)
-- CREATE DATABASE work_management_dev;

-- Connect to the database
\c work_management_dev;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy string matching

-- Create pgvector extension (graceful handling if not available)
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS "vector";
    RAISE NOTICE '✅ pgvector extension created successfully';
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING '⚠️  pgvector extension not available: %', SQLERRM;
END
$$;

-- ================================================================================
-- USERS TABLE
-- ================================================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    full_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- ================================================================================
-- NOTES TABLE - Primary note storage with embeddings and full-text search
-- ================================================================================
CREATE TABLE notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id TEXT,
    text TEXT NOT NULL CHECK (length(text) > 0),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
    
    -- Vector embedding for semantic search (OpenAI embeddings are 1536 dimensions)
    embedding vector(1536) NULL,
    
    -- Full-text search vector (always available)
    text_search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
    
    -- JSON fields for flexible data storage
    extracted_entities JSONB DEFAULT '[]',  -- Raw entities from extraction
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- ================================================================================
-- ENTITIES TABLE - Normalized entity registry with deduplication
-- ================================================================================
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canonical_name TEXT NOT NULL,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('person', 'project', 'technology', 'concept')),
    
    -- Entity registry features
    aliases JSONB DEFAULT '[]',  -- Alternative names for fuzzy matching
    mention_count INTEGER DEFAULT 0,  -- Usage tracking
    
    -- Temporal tracking
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT now(),
    
    -- Flexible metadata storage
    metadata JSONB DEFAULT '{}',
    
    -- Standard timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    
    -- Ensure unique entities per type
    UNIQUE(canonical_name, entity_type)
);

-- ================================================================================
-- ENTITY_MENTIONS TABLE - Many-to-many relationship between notes and entities
-- ================================================================================
CREATE TABLE entity_mentions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    
    -- Mention details
    mentioned_text TEXT NOT NULL,  -- How the entity was mentioned in this note
    confidence DECIMAL(3,2) DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    
    -- Position tracking (for future highlighting)
    position_start INTEGER,
    position_end INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- ================================================================================
-- PLANNED_INTENTIONS TABLE - For future planning features (Phase 4)
-- ================================================================================
CREATE TABLE planned_intentions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_note_id UUID REFERENCES notes(id) ON DELETE CASCADE,
    
    -- Intention details
    intention_text TEXT NOT NULL,
    mentioned_date DATE NOT NULL,
    target_date DATE,
    target_date_fuzzy TEXT,  -- "next week", "by month end", etc.
    
    -- Status tracking
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'completed', 'cancelled')),
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    
    -- Related data
    related_entities JSONB DEFAULT '[]',
    confidence DECIMAL(3,2) DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- ================================================================================
-- PLANNING_SESSIONS TABLE - Weekly planning sessions (Phase 4)
-- ================================================================================
CREATE TABLE planning_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Session details
    session_date DATE NOT NULL,
    week_start DATE NOT NULL,
    
    -- Generated content
    generated_plan JSONB,
    intentions_surfaced JSONB DEFAULT '[]',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- ================================================================================
-- PERFORMANCE INDEXES
-- ================================================================================

-- Notes indexes
CREATE INDEX idx_notes_user_timestamp ON notes(user_id, timestamp DESC);
CREATE INDEX idx_notes_text_search ON notes USING gin(text_search_vector);
CREATE INDEX idx_notes_session ON notes(session_id) WHERE session_id IS NOT NULL;

-- Vector index (only if pgvector is available)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        CREATE INDEX idx_notes_embedding ON notes USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
        RAISE NOTICE '✅ Vector index created successfully';
    ELSE
        RAISE NOTICE '⚠️  Skipping vector index - pgvector not available';
    END IF;
END
$$;

-- Entity indexes
CREATE INDEX idx_entities_type_name ON entities(entity_type, canonical_name);
CREATE INDEX idx_entities_mention_count ON entities(mention_count DESC);
CREATE INDEX idx_entities_canonical_name_gin ON entities USING gin(canonical_name gin_trgm_ops);  -- For fuzzy matching
CREATE INDEX idx_entities_aliases_gin ON entities USING gin(aliases);  -- For alias searches

-- Entity mentions indexes
CREATE INDEX idx_entity_mentions_note_id ON entity_mentions(note_id);
CREATE INDEX idx_entity_mentions_entity_id ON entity_mentions(entity_id);
CREATE INDEX idx_entity_mentions_confidence ON entity_mentions(confidence DESC);

-- Planning indexes (for future use)
CREATE INDEX idx_planned_intentions_user_date ON planned_intentions(user_id, target_date);
CREATE INDEX idx_planned_intentions_status ON planned_intentions(status) WHERE status = 'pending';
CREATE INDEX idx_planning_sessions_user_week ON planning_sessions(user_id, week_start);

-- ================================================================================
-- TRIGGER FUNCTIONS
-- ================================================================================

-- Generic updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Entity-specific trigger function (updates last_seen when mention_count changes)
CREATE OR REPLACE FUNCTION update_entities_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    -- If mention_count increased, update last_seen
    IF NEW.mention_count > OLD.mention_count THEN
        NEW.last_seen = now();
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ================================================================================
-- TRIGGERS
-- ================================================================================

-- Updated_at triggers
CREATE TRIGGER update_notes_updated_at 
    BEFORE UPDATE ON notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_entities_updated_at 
    BEFORE UPDATE ON entities
    FOR EACH ROW EXECUTE FUNCTION update_entities_updated_at();

CREATE TRIGGER update_planned_intentions_updated_at 
    BEFORE UPDATE ON planned_intentions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ================================================================================
-- SEED DATA
-- ================================================================================

-- Insert default test user
INSERT INTO users (username, email, full_name) VALUES
('testuser', 'test@example.com', 'Test User')
ON CONFLICT (username) DO NOTHING;

-- Insert sample entities for testing (optional)
INSERT INTO entities (canonical_name, entity_type, mention_count) VALUES
('AI', 'concept', 0),
('Machine Learning', 'technology', 0),
('Database Design', 'concept', 0)
ON CONFLICT (canonical_name, entity_type) DO NOTHING;

-- ================================================================================
-- FINAL STATUS CHECK
-- ================================================================================

DO $$
DECLARE
    vector_available BOOLEAN;
    trgm_available BOOLEAN;
    entity_count INTEGER;
BEGIN
    -- Check extensions
    SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector') INTO vector_available;
    SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm') INTO trgm_available;
    
    -- Check seed data
    SELECT COUNT(*) FROM entities INTO entity_count;
    
    -- Report status
    RAISE NOTICE '================================================================================';
    RAISE NOTICE '🚀 WORK MANAGEMENT DATABASE INITIALIZATION COMPLETE';
    RAISE NOTICE '================================================================================';
    
    IF vector_available THEN
        RAISE NOTICE '✅ pgvector extension: ENABLED (semantic search available)';
    ELSE
        RAISE NOTICE '⚠️  pgvector extension: DISABLED (text search only)';
    END IF;
    
    IF trgm_available THEN
        RAISE NOTICE '✅ pg_trgm extension: ENABLED (fuzzy matching available)';
    ELSE
        RAISE NOTICE '⚠️  pg_trgm extension: DISABLED (exact matching only)';
    END IF;
    
    RAISE NOTICE '📊 Tables created: 6 (users, notes, entities, entity_mentions, planned_intentions, planning_sessions)';
    RAISE NOTICE '🔍 Indexes created: 12+ (optimized for search and relationships)';
    RAISE NOTICE '👤 Test user created: testuser';
    RAISE NOTICE '🏷️  Sample entities: % seeded', entity_count;
    RAISE NOTICE '================================================================================';
    RAISE NOTICE '🎯 Ready for Phase 2+ features: Note storage, Entity registry, Hybrid search';
    RAISE NOTICE '================================================================================';
END
$$;