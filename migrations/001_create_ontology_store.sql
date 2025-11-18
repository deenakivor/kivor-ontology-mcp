-- =====================================================
-- Kivor Ontology MCP - Database Schema Migration
-- Migration 001: Create ontology_store table
-- =====================================================

-- Set schema
SET search_path TO kivorticketing, public;

-- Create ontology_store table
CREATE TABLE IF NOT EXISTS ontology_store (
    ontology_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    ontology_json JSONB NOT NULL,
    category VARCHAR(100) DEFAULT 'general',
    description TEXT,
    tags TEXT[],
    priority INTEGER DEFAULT 50 CHECK (priority >= 1 AND priority <= 100),
    matching_config JSONB,
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(255) DEFAULT 'system',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP NULL,
    CONSTRAINT unique_name_version UNIQUE(name, version)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_ontology_name ON ontology_store(name);
CREATE INDEX IF NOT EXISTS idx_ontology_category ON ontology_store(category);
CREATE INDEX IF NOT EXISTS idx_ontology_active ON ontology_store(is_active) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_ontology_priority ON ontology_store(priority DESC);
CREATE INDEX IF NOT EXISTS idx_ontology_tags ON ontology_store USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_ontology_json ON ontology_store USING GIN(ontology_json);

-- Add comments
COMMENT ON TABLE ontology_store IS 'Stores all ontology definitions for dynamic ticket classification';
COMMENT ON COLUMN ontology_store.ontology_id IS 'Primary key';
COMMENT ON COLUMN ontology_store.name IS 'Unique ontology name (e.g., infrastructure_ontology)';
COMMENT ON COLUMN ontology_store.version IS 'Version in semver format (e.g., 1.0.0)';
COMMENT ON COLUMN ontology_store.ontology_json IS 'Complete ontology JSON with entities and relationships';
COMMENT ON COLUMN ontology_store.category IS 'Category: infrastructure, application, database, network, etc.';
COMMENT ON COLUMN ontology_store.description IS 'Human-readable description';
COMMENT ON COLUMN ontology_store.tags IS 'Array of tags for searching';
COMMENT ON COLUMN ontology_store.priority IS 'Selection priority (1-100, higher = preferred)';
COMMENT ON COLUMN ontology_store.matching_config IS 'Optional LLM matching configuration';
COMMENT ON COLUMN ontology_store.is_active IS 'Active status for selection';
COMMENT ON COLUMN ontology_store.deleted_at IS 'Soft delete timestamp';

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE ON ontology_store TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE ontology_store_ontology_id_seq TO your_app_user;

-- Log migration
DO $$
BEGIN
    RAISE NOTICE 'Migration 001 completed: ontology_store table created';
END $$;
