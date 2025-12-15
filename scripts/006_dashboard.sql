-- MPIS Dashboard - Database Migration
-- Tables for Dashboard as independent service and proxy for MPIS API

-- Dashboard Projects table: stores project metadata with run_id and project_id mapping
CREATE TABLE IF NOT EXISTS dashboard_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    channels TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    meta JSONB NOT NULL DEFAULT '{}'
);

-- Dashboard Runs table: stores run metadata (mapping between Dashboard and MPIS)
CREATE TABLE IF NOT EXISTS dashboard_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL UNIQUE,
    project_id UUID NOT NULL REFERENCES dashboard_projects(id) ON DELETE CASCADE,
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending',
        'running',
        'success',
        'failed',
        'partial'
    )),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    n8n_execution_id UUID,
    error_message TEXT,
    meta JSONB NOT NULL DEFAULT '{}'
);

-- Dashboard Layouts table: stores user dashboard layout configurations
CREATE TABLE IF NOT EXISTS dashboard_layouts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID, -- Nullable for default/global layouts
    name TEXT NOT NULL DEFAULT 'My Dashboard',
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    layout_config JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Widget Registry table: stores widget definitions (built-in and custom)
CREATE TABLE IF NOT EXISTS widget_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    widget_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    widget_type TEXT NOT NULL CHECK (widget_type IN ('builtin', 'custom')),
    schema JSONB NOT NULL DEFAULT '{}',
    renderer_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Red Flags table: tracks critical system issues
CREATE TABLE IF NOT EXISTS red_flags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flag_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('warning', 'critical')),
    description TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolved_by TEXT
);

-- Metrics Ingestion Jobs table: schedules for periodic metrics collection
CREATE TABLE IF NOT EXISTS metrics_ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_name TEXT NOT NULL UNIQUE,
    channel TEXT NOT NULL,
    persona_id UUID REFERENCES personas(id) ON DELETE CASCADE,
    schedule_cron TEXT NOT NULL, -- Cron expression
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    config JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Normalized Metrics table: stores normalized metrics across all channels
CREATE TABLE IF NOT EXISTS normalized_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    published_item_id UUID NOT NULL REFERENCES published_items(id) ON DELETE CASCADE,
    channel TEXT NOT NULL,
    
    -- Normalized metric fields
    views INTEGER,
    impressions INTEGER,
    reach INTEGER,
    reactions INTEGER,
    comments INTEGER,
    shares INTEGER,
    saves INTEGER,
    clicks INTEGER,
    
    -- Calculated fields
    engagement_rate NUMERIC(5, 4),
    
    -- Raw data for reference
    raw_metrics JSONB NOT NULL DEFAULT '{}',
    
    -- Metadata
    measured_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source TEXT NOT NULL DEFAULT 'manual'
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_dashboard_projects_persona_id ON dashboard_projects(persona_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_projects_created_at ON dashboard_projects(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_dashboard_runs_run_id ON dashboard_runs(run_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_runs_project_id ON dashboard_runs(project_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_runs_persona_id ON dashboard_runs(persona_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_runs_status ON dashboard_runs(status);
CREATE INDEX IF NOT EXISTS idx_dashboard_runs_started_at ON dashboard_runs(started_at DESC);

CREATE INDEX IF NOT EXISTS idx_dashboard_layouts_user_id ON dashboard_layouts(user_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_layouts_is_default ON dashboard_layouts(is_default);

CREATE INDEX IF NOT EXISTS idx_red_flags_flag_type ON red_flags(flag_type);
CREATE INDEX IF NOT EXISTS idx_red_flags_severity ON red_flags(severity);
CREATE INDEX IF NOT EXISTS idx_red_flags_created_at ON red_flags(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_red_flags_resolved_at ON red_flags(resolved_at);

CREATE INDEX IF NOT EXISTS idx_metrics_ingestion_jobs_channel ON metrics_ingestion_jobs(channel);
CREATE INDEX IF NOT EXISTS idx_metrics_ingestion_jobs_next_run_at ON metrics_ingestion_jobs(next_run_at);
CREATE INDEX IF NOT EXISTS idx_metrics_ingestion_jobs_enabled ON metrics_ingestion_jobs(enabled);

CREATE INDEX IF NOT EXISTS idx_normalized_metrics_published_item_id ON normalized_metrics(published_item_id);
CREATE INDEX IF NOT EXISTS idx_normalized_metrics_channel ON normalized_metrics(channel);
CREATE INDEX IF NOT EXISTS idx_normalized_metrics_measured_at ON normalized_metrics(measured_at DESC);

-- Add updated_at triggers
CREATE OR REPLACE FUNCTION update_dashboard_projects_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_dashboard_projects_updated_at ON dashboard_projects;
CREATE TRIGGER trigger_update_dashboard_projects_updated_at
    BEFORE UPDATE ON dashboard_projects
    FOR EACH ROW
    EXECUTE FUNCTION update_dashboard_projects_updated_at();

CREATE OR REPLACE FUNCTION update_dashboard_layouts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_dashboard_layouts_updated_at ON dashboard_layouts;
CREATE TRIGGER trigger_update_dashboard_layouts_updated_at
    BEFORE UPDATE ON dashboard_layouts
    FOR EACH ROW
    EXECUTE FUNCTION update_dashboard_layouts_updated_at();

-- Comments for documentation
COMMENT ON TABLE dashboard_projects IS 'Dashboard project metadata with channel configurations';
COMMENT ON TABLE dashboard_runs IS 'Dashboard run tracking with status aggregation including partial status';
COMMENT ON TABLE dashboard_layouts IS 'User dashboard layout configurations';
COMMENT ON TABLE widget_registry IS 'Registry of built-in and custom dashboard widgets';
COMMENT ON TABLE red_flags IS 'Critical system issues requiring attention';
COMMENT ON TABLE metrics_ingestion_jobs IS 'Scheduled jobs for periodic metrics collection';
COMMENT ON TABLE normalized_metrics IS 'Normalized metrics across all channels';
