-- MPIS Module 4: Analytics Dashboard + EIDOS - Database Migration
-- Tables for analytics rollups, recommendations, and experiments

-- Analytics Rollups table: stores computed analytics summaries
CREATE TABLE IF NOT EXISTS analytics_rollups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    rollup_type TEXT NOT NULL CHECK (rollup_type IN ('daily', 'weekly', 'monthly')),
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    metrics JSONB NOT NULL DEFAULT '{}',
    insights JSONB NOT NULL DEFAULT '{}',
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(persona_id, rollup_type, period_start)
);

-- EIDOS Recommendations table: stores AI-generated actionable recommendations
CREATE TABLE IF NOT EXISTS eidos_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    run_id UUID NOT NULL,
    recommendations JSONB NOT NULL DEFAULT '[]',
    evidence JSONB NOT NULL DEFAULT '{}',
    experiments JSONB NOT NULL DEFAULT '[]',
    content_briefs JSONB NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'actioned', 'expired')),
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Experiments table: tracks A/B testing and content experiments
CREATE TABLE IF NOT EXISTS experiments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    hypothesis TEXT,
    variants JSONB NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'completed', 'cancelled')),
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    results JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Dashboard Views table: stores user-defined dashboard configurations
CREATE TABLE IF NOT EXISTS dashboard_views (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID REFERENCES personas(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    view_config JSONB NOT NULL DEFAULT '{}',
    is_default BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_analytics_rollups_persona_id ON analytics_rollups(persona_id);
CREATE INDEX IF NOT EXISTS idx_analytics_rollups_type ON analytics_rollups(rollup_type);
CREATE INDEX IF NOT EXISTS idx_analytics_rollups_period ON analytics_rollups(period_start, period_end);

CREATE INDEX IF NOT EXISTS idx_eidos_recommendations_persona_id ON eidos_recommendations(persona_id);
CREATE INDEX IF NOT EXISTS idx_eidos_recommendations_run_id ON eidos_recommendations(run_id);
CREATE INDEX IF NOT EXISTS idx_eidos_recommendations_status ON eidos_recommendations(status);
CREATE INDEX IF NOT EXISTS idx_eidos_recommendations_computed_at ON eidos_recommendations(computed_at DESC);

CREATE INDEX IF NOT EXISTS idx_experiments_persona_id ON experiments(persona_id);
CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);

CREATE INDEX IF NOT EXISTS idx_dashboard_views_persona_id ON dashboard_views(persona_id);

-- Add updated_at triggers
CREATE OR REPLACE FUNCTION update_experiments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_experiments_updated_at ON experiments;
CREATE TRIGGER trigger_update_experiments_updated_at
    BEFORE UPDATE ON experiments
    FOR EACH ROW
    EXECUTE FUNCTION update_experiments_updated_at();

CREATE OR REPLACE FUNCTION update_dashboard_views_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_dashboard_views_updated_at ON dashboard_views;
CREATE TRIGGER trigger_update_dashboard_views_updated_at
    BEFORE UPDATE ON dashboard_views
    FOR EACH ROW
    EXECUTE FUNCTION update_dashboard_views_updated_at();

-- Comments for documentation
COMMENT ON TABLE analytics_rollups IS 'Computed analytics summaries by time period';
COMMENT ON TABLE eidos_recommendations IS 'AI-generated actionable recommendations from EIDOS engine';
COMMENT ON TABLE experiments IS 'A/B testing and content experiment tracking';
COMMENT ON TABLE dashboard_views IS 'User-defined dashboard configurations';
