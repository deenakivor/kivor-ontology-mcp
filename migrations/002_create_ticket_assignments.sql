-- =====================================================
-- Kivor Ontology MCP - Database Schema Migration
-- Migration 002: Create ticket_ontology_assignments table
-- =====================================================

-- Set schema
SET search_path TO kivorticketing, public;

-- Create ticket_ontology_assignments table
CREATE TABLE IF NOT EXISTS ticket_ontology_assignments (
    assignment_id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(50) NOT NULL,
    ontology_id INTEGER NOT NULL,
    project_id INTEGER,
    match_confidence DECIMAL(4,3) CHECK (match_confidence >= 0 AND match_confidence <= 1),
    match_method VARCHAR(50) NOT NULL,
    llm_reasoning TEXT,
    llm_category VARCHAR(255),
    llm_keywords_found TEXT[],
    llm_model VARCHAR(100),
    processing_time_ms INTEGER,
    is_override BOOLEAN DEFAULT false,
    override_reason TEXT,
    override_by VARCHAR(255),
    ticket_title TEXT,
    ticket_description TEXT,
    assigned_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_ontology FOREIGN KEY (ontology_id) 
        REFERENCES ontology_store(ontology_id) 
        ON DELETE RESTRICT
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_assignment_ticket ON ticket_ontology_assignments(ticket_id);
CREATE INDEX IF NOT EXISTS idx_assignment_ontology ON ticket_ontology_assignments(ontology_id);
CREATE INDEX IF NOT EXISTS idx_assignment_project ON ticket_ontology_assignments(project_id);
CREATE INDEX IF NOT EXISTS idx_assignment_date ON ticket_ontology_assignments(assigned_at DESC);
CREATE INDEX IF NOT EXISTS idx_assignment_override ON ticket_ontology_assignments(is_override) WHERE is_override = true;
CREATE INDEX IF NOT EXISTS idx_assignment_method ON ticket_ontology_assignments(match_method);

-- Add comments
COMMENT ON TABLE ticket_ontology_assignments IS 'Records all ticket-to-ontology assignments with LLM classification details';
COMMENT ON COLUMN ticket_ontology_assignments.assignment_id IS 'Primary key';
COMMENT ON COLUMN ticket_ontology_assignments.ticket_id IS 'Ticket identifier (e.g., TKT-ABC123)';
COMMENT ON COLUMN ticket_ontology_assignments.ontology_id IS 'Foreign key to ontology_store';
COMMENT ON COLUMN ticket_ontology_assignments.match_confidence IS 'LLM confidence score (0.0-1.0)';
COMMENT ON COLUMN ticket_ontology_assignments.match_method IS 'Method: llm_classification, manual_override, rule_based';
COMMENT ON COLUMN ticket_ontology_assignments.llm_reasoning IS 'LLM explanation for selection';
COMMENT ON COLUMN ticket_ontology_assignments.llm_category IS 'Category identified by LLM';
COMMENT ON COLUMN ticket_ontology_assignments.llm_keywords_found IS 'Keywords matched by LLM';
COMMENT ON COLUMN ticket_ontology_assignments.llm_model IS 'LLM model used (e.g., gpt-4o-mini)';
COMMENT ON COLUMN ticket_ontology_assignments.processing_time_ms IS 'Processing time in milliseconds';
COMMENT ON COLUMN ticket_ontology_assignments.is_override IS 'True if manual override';
COMMENT ON COLUMN ticket_ontology_assignments.override_reason IS 'Reason for manual override';
COMMENT ON COLUMN ticket_ontology_assignments.override_by IS 'User who performed override';

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE ON ticket_ontology_assignments TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE ticket_ontology_assignments_assignment_id_seq TO your_app_user;

-- Log migration
DO $$
BEGIN
    RAISE NOTICE 'Migration 002 completed: ticket_ontology_assignments table created';
END $$;
