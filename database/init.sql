-- Create database if it doesn't exist
-- CREATE DATABASE work_management_dev;

-- Connect to the database
\c work_management_dev;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create pgvector extension (this might fail if not installed)
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS "vector";
    RAISE NOTICE 'pgvector extension created successfully';
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'pgvector extension not available: %', SQLERRM;
END
$$;

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    full_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Primary note storage with optional embeddings
CREATE TABLE notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id TEXT,
    text TEXT NOT NULL CHECK (length(text) > 0),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
    
    -- Vector embedding for semantic search (OpenAI embeddings are 1536 dimensions)
    -- Make this conditional on pgvector availability
    embedding vector(1536) NULL,
    
    -- Full-text search (always available)
    text_search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
    
    extracted_entities JSONB DEFAULT '[]',
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Only create vector index if pgvector is available
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        CREATE INDEX idx_notes_embedding ON notes USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
        RAISE NOTICE 'Vector index created successfully';
    ELSE
        RAISE WARNING 'Skipping vector index creation - pgvector not available';
    END IF;
END
$$;

-- Rest of the schema...
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canonical_name TEXT NOT NULL,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('person', 'project', 'technology', 'concept')),
    aliases JSONB DEFAULT '[]',
    mention_count INTEGER DEFAULT 0,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT now(),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(canonical_name, entity_type)
);

CREATE TABLE entity_mentions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    mentioned_text TEXT NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    position_start INTEGER,
    position_end INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE planned_intentions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_note_id UUID REFERENCES notes(id) ON DELETE CASCADE,
    intention_text TEXT NOT NULL,
    mentioned_date DATE NOT NULL,
    target_date DATE,
    target_date_fuzzy TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'completed', 'cancelled')),
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    related_entities JSONB DEFAULT '[]',
    confidence DECIMAL(3,2) DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE planning_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_date DATE NOT NULL,
    week_start DATE NOT NULL,
    generated_plan JSONB,
    intentions_surfaced JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Performance indexes (always create these)
CREATE INDEX idx_notes_user_timestamp ON notes(user_id, timestamp DESC);
CREATE INDEX idx_notes_text_search ON notes USING gin(text_search_vector);
CREATE INDEX idx_entity_mentions_note_id ON entity_mentions(note_id);
CREATE INDEX idx_entity_mentions_entity_id ON entity_mentions(entity_id);
CREATE INDEX idx_entities_type_name ON entities(entity_type, canonical_name);
CREATE INDEX idx_entities_mention_count ON entities(mention_count DESC);
CREATE INDEX idx_planned_intentions_user_date ON planned_intentions(user_id, target_date);
CREATE INDEX idx_planned_intentions_status ON planned_intentions(status) WHERE status = 'pending';
CREATE INDEX idx_planning_sessions_user_week ON planning_sessions(user_id, week_start);

-- Insert default test user
INSERT INTO users (username, email, full_name) VALUES
('testuser', 'test@example.com', 'Test User');

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_notes_updated_at BEFORE UPDATE ON notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_planned_intentions_updated_at BEFORE UPDATE ON planned_intentions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Check final status
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE NOTICE '✅ Database initialized with pgvector support';
    ELSE
        RAISE NOTICE '⚠️  Database initialized without pgvector - using text search only';
    END IF;
END
$$;