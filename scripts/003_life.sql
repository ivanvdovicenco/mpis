-- MPIS Module 2: Persona Life - Database Migration
-- Tables for event ingestion, reflection cycles, metrics, and memory management

-- Life Events table: stores all persona life events
CREATE TABLE IF NOT EXISTS life_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    run_id UUID,
    meta JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Life Cycles table: tracks reflection cycle jobs
CREATE TABLE IF NOT EXISTS life_cycles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending',
        'processing',
        'awaiting_approval',
        'committed',
        'failed'
    )),
    cycle_type TEXT NOT NULL DEFAULT 'daily' CHECK (cycle_type IN ('daily', 'weekly', 'manual')),
    run_id UUID NOT NULL,
    options JSONB NOT NULL DEFAULT '{}',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);

-- Life Cycle Drafts table: stores draft outputs from reflection cycles
CREATE TABLE IF NOT EXISTS life_cycle_drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cycle_id UUID NOT NULL REFERENCES life_cycles(id) ON DELETE CASCADE,
    draft_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Life Metrics table: stores computed persona metrics
CREATE TABLE IF NOT EXISTS life_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    metric_key TEXT NOT NULL,
    metric_value NUMERIC NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(persona_id, metric_key, period_start, period_end)
);

-- Recommendations table: stores generated recommendations
CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    source TEXT NOT NULL CHECK (source IN ('life', 'publisher', 'analytics', 'eidos')),
    rec_json JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'expired')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_life_events_persona_id ON life_events(persona_id);
CREATE INDEX IF NOT EXISTS idx_life_events_event_type ON life_events(event_type);
CREATE INDEX IF NOT EXISTS idx_life_events_created_at ON life_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_life_events_run_id ON life_events(run_id);

CREATE INDEX IF NOT EXISTS idx_life_cycles_persona_id ON life_cycles(persona_id);
CREATE INDEX IF NOT EXISTS idx_life_cycles_status ON life_cycles(status);
CREATE INDEX IF NOT EXISTS idx_life_cycles_run_id ON life_cycles(run_id);

CREATE INDEX IF NOT EXISTS idx_life_cycle_drafts_cycle_id ON life_cycle_drafts(cycle_id);

CREATE INDEX IF NOT EXISTS idx_life_metrics_persona_id ON life_metrics(persona_id);
CREATE INDEX IF NOT EXISTS idx_life_metrics_metric_key ON life_metrics(metric_key);

CREATE INDEX IF NOT EXISTS idx_recommendations_persona_id ON recommendations(persona_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_source ON recommendations(source);
CREATE INDEX IF NOT EXISTS idx_recommendations_status ON recommendations(status);

-- Comments for documentation
COMMENT ON TABLE life_events IS 'Stores life events for persona evolution tracking';
COMMENT ON TABLE life_cycles IS 'Tracks reflection cycle jobs (daily/weekly/manual)';
COMMENT ON TABLE life_cycle_drafts IS 'Stores draft outputs from reflection cycles requiring approval';
COMMENT ON TABLE life_metrics IS 'Computed persona metrics over time periods';
COMMENT ON TABLE recommendations IS 'AI-generated recommendations from various sources';
