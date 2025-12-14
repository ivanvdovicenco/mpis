-- MPIS Module 3: Social Publisher - Database Migration
-- Tables for content planning, generation, approval, and publishing

-- Content Plans table: stores content calendar items
CREATE TABLE IF NOT EXISTS content_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    topic TEXT NOT NULL,
    goal TEXT,
    target_audience TEXT,
    channel TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'en',
    max_length INTEGER DEFAULT 1000,
    schedule_window_start TIMESTAMPTZ,
    schedule_window_end TIMESTAMPTZ,
    constraints JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'planned' CHECK (status IN (
        'planned',
        'generating',
        'draft_ready',
        'approved',
        'scheduled',
        'published',
        'cancelled'
    )),
    run_id UUID,
    meta JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Content Drafts table: stores generated content drafts
CREATE TABLE IF NOT EXISTS content_drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES content_plans(id) ON DELETE CASCADE,
    persona_version_id UUID REFERENCES persona_versions(id) ON DELETE SET NULL,
    draft_no INTEGER NOT NULL DEFAULT 1,
    content_json JSONB NOT NULL DEFAULT '{}',
    provenance JSONB NOT NULL DEFAULT '{}',
    run_id UUID,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(plan_id, draft_no)
);

-- Published Items table: stores published content records
CREATE TABLE IF NOT EXISTS published_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    draft_id UUID NOT NULL REFERENCES content_drafts(id) ON DELETE CASCADE,
    channel TEXT NOT NULL,
    channel_item_id TEXT,
    channel_url TEXT,
    published_payload JSONB NOT NULL DEFAULT '{}',
    published_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    persona_version_used TEXT,
    meta JSONB NOT NULL DEFAULT '{}'
);

-- Channel Accounts table: stores channel configuration
CREATE TABLE IF NOT EXISTS channel_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    channel TEXT NOT NULL,
    account_id TEXT NOT NULL,
    account_name TEXT,
    config JSONB NOT NULL DEFAULT '{}',
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(persona_id, channel, account_id)
);

-- Item Metrics table: stores metrics for published items
CREATE TABLE IF NOT EXISTS item_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    published_item_id UUID NOT NULL REFERENCES published_items(id) ON DELETE CASCADE,
    metric_type TEXT NOT NULL,
    metric_value NUMERIC NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source TEXT DEFAULT 'manual',
    meta JSONB NOT NULL DEFAULT '{}'
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_content_plans_persona_id ON content_plans(persona_id);
CREATE INDEX IF NOT EXISTS idx_content_plans_status ON content_plans(status);
CREATE INDEX IF NOT EXISTS idx_content_plans_channel ON content_plans(channel);
CREATE INDEX IF NOT EXISTS idx_content_plans_schedule ON content_plans(schedule_window_start, schedule_window_end);

CREATE INDEX IF NOT EXISTS idx_content_drafts_plan_id ON content_drafts(plan_id);
CREATE INDEX IF NOT EXISTS idx_content_drafts_status ON content_drafts(status);
CREATE INDEX IF NOT EXISTS idx_content_drafts_run_id ON content_drafts(run_id);

CREATE INDEX IF NOT EXISTS idx_published_items_draft_id ON published_items(draft_id);
CREATE INDEX IF NOT EXISTS idx_published_items_channel ON published_items(channel);
CREATE INDEX IF NOT EXISTS idx_published_items_published_at ON published_items(published_at DESC);

CREATE INDEX IF NOT EXISTS idx_channel_accounts_persona_id ON channel_accounts(persona_id);
CREATE INDEX IF NOT EXISTS idx_channel_accounts_channel ON channel_accounts(channel);

CREATE INDEX IF NOT EXISTS idx_item_metrics_published_item_id ON item_metrics(published_item_id);
CREATE INDEX IF NOT EXISTS idx_item_metrics_metric_type ON item_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_item_metrics_recorded_at ON item_metrics(recorded_at DESC);

-- Add updated_at trigger for content_plans
CREATE OR REPLACE FUNCTION update_content_plans_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_content_plans_updated_at ON content_plans;
CREATE TRIGGER trigger_update_content_plans_updated_at
    BEFORE UPDATE ON content_plans
    FOR EACH ROW
    EXECUTE FUNCTION update_content_plans_updated_at();

-- Comments for documentation
COMMENT ON TABLE content_plans IS 'Content calendar and planning for social publishing';
COMMENT ON TABLE content_drafts IS 'Generated content drafts with provenance tracking';
COMMENT ON TABLE published_items IS 'Records of published content with channel identifiers';
COMMENT ON TABLE channel_accounts IS 'Channel account configuration per persona';
COMMENT ON TABLE item_metrics IS 'Metrics collected for published content items';
