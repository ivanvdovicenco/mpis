-- MPIS Module 1: Persona Genesis Engine - Database Migration
-- This migration adds tables required for the Genesis Engine workflow

-- Create extension for UUID generation if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Genesis Jobs table: tracks the persona generation workflow
CREATE TABLE IF NOT EXISTS genesis_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_name TEXT NOT NULL,
    slug TEXT NOT NULL,
    input_json JSONB NOT NULL DEFAULT '{}',
    config_json JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN (
        'queued',
        'collecting',
        'processing',
        'awaiting_approval',
        'committed',
        'failed',
        'committed_with_memory_pending'
    )),
    error TEXT,
    persona_id UUID REFERENCES personas(id) ON DELETE SET NULL,
    draft_no INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Genesis Drafts table: stores each draft version of the persona core
CREATE TABLE IF NOT EXISTS genesis_drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES genesis_jobs(id) ON DELETE CASCADE,
    draft_no INTEGER NOT NULL,
    draft_core_json JSONB NOT NULL DEFAULT '{}',
    human_prompt TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(job_id, draft_no)
);

-- Genesis Messages table: stores conversation history for the generation process
CREATE TABLE IF NOT EXISTS genesis_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES genesis_jobs(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('system', 'assistant', 'user')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_genesis_jobs_status ON genesis_jobs(status);
CREATE INDEX IF NOT EXISTS idx_genesis_jobs_slug ON genesis_jobs(slug);
CREATE INDEX IF NOT EXISTS idx_genesis_jobs_persona_id ON genesis_jobs(persona_id);
CREATE INDEX IF NOT EXISTS idx_genesis_drafts_job_id ON genesis_drafts(job_id);
CREATE INDEX IF NOT EXISTS idx_genesis_messages_job_id ON genesis_messages(job_id);

-- Add updated_at trigger for genesis_jobs
CREATE OR REPLACE FUNCTION update_genesis_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_genesis_jobs_updated_at ON genesis_jobs;
CREATE TRIGGER trigger_update_genesis_jobs_updated_at
    BEFORE UPDATE ON genesis_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_genesis_jobs_updated_at();

-- Ensure base tables exist (if not created by prior migration)
-- personas table
CREATE TABLE IF NOT EXISTS personas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT,
    language TEXT DEFAULT 'en',
    active_version TEXT DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- persona_versions table
CREATE TABLE IF NOT EXISTS persona_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    version TEXT NOT NULL,
    core_json JSONB NOT NULL DEFAULT '{}',
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(persona_id, version)
);

-- sources table
CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID REFERENCES personas(id) ON DELETE SET NULL,
    job_id UUID REFERENCES genesis_jobs(id) ON DELETE SET NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('youtube', 'file', 'url', 'text')),
    source_ref TEXT NOT NULL,
    content_hash TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    extracted_text_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- audit_log table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type TEXT NOT NULL,
    entity_type TEXT,
    entity_id UUID,
    job_id UUID REFERENCES genesis_jobs(id) ON DELETE SET NULL,
    details JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for base tables
CREATE INDEX IF NOT EXISTS idx_personas_slug ON personas(slug);
CREATE INDEX IF NOT EXISTS idx_persona_versions_persona_id ON persona_versions(persona_id);
CREATE INDEX IF NOT EXISTS idx_sources_persona_id ON sources(persona_id);
CREATE INDEX IF NOT EXISTS idx_sources_job_id ON sources(job_id);
CREATE INDEX IF NOT EXISTS idx_sources_content_hash ON sources(content_hash);
CREATE INDEX IF NOT EXISTS idx_audit_log_event_type ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_job_id ON audit_log(job_id);

-- Add updated_at trigger for personas
CREATE OR REPLACE FUNCTION update_personas_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_personas_updated_at ON personas;
CREATE TRIGGER trigger_update_personas_updated_at
    BEFORE UPDATE ON personas
    FOR EACH ROW
    EXECUTE FUNCTION update_personas_updated_at();

-- Comments for documentation
COMMENT ON TABLE genesis_jobs IS 'Tracks persona generation workflow jobs';
COMMENT ON TABLE genesis_drafts IS 'Stores draft versions of persona core during approval loop';
COMMENT ON TABLE genesis_messages IS 'Stores LLM conversation history for persona generation';
COMMENT ON TABLE personas IS 'Core persona entity with metadata';
COMMENT ON TABLE persona_versions IS 'Versioned persona core configurations';
COMMENT ON TABLE sources IS 'Source materials used to generate personas';
COMMENT ON TABLE audit_log IS 'Audit trail for all major system events';
