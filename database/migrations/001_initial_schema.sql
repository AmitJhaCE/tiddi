-- Migration: 001_initial_schema
-- Description: Initial database schema for work management system
-- Date: $(date +%Y-%m-%d)

-- This migration is already applied via init.sql
-- Future schema changes will go in separate migration files

-- Version tracking
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

INSERT INTO schema_migrations (version) VALUES ('001_initial_schema') 
ON CONFLICT (version) DO NOTHING;
