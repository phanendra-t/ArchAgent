-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Reviews table (stores full review results)
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    review_id VARCHAR(64) UNIQUE NOT NULL,
    system_name VARCHAR(128) NOT NULL DEFAULT 'unknown',
    diff_hash VARCHAR(64) NOT NULL,
    diff_preview TEXT,
    spec_file VARCHAR(256),
    health_score INT NOT NULL DEFAULT 100,
    summary TEXT,
    findings JSONB NOT NULL DEFAULT '[]'::jsonb,
    suppressed_findings JSONB NOT NULL DEFAULT '[]'::jsonb,
    stats JSONB NOT NULL DEFAULT '{}'::jsonb,
    reward_model_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reviews_review_id ON reviews(review_id);
CREATE INDEX IF NOT EXISTS idx_reviews_system_name ON reviews(system_name);
CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews(created_at DESC);

-- Annotations table (stores human feedback + embeddings)
CREATE TABLE IF NOT EXISTS annotations (
    id SERIAL PRIMARY KEY,
    finding_id VARCHAR(64) NOT NULL,
    review_id VARCHAR(64) REFERENCES reviews(review_id) ON DELETE SET NULL,
    finding_text TEXT NOT NULL,
    finding_category VARCHAR(32) NOT NULL,
    finding_severity VARCHAR(16) NOT NULL,
    rule_violated VARCHAR(128),
    context_violated VARCHAR(64),
    label VARCHAR(16) NOT NULL CHECK (label IN ('valid', 'false_positive', 'partial')),
    severity_accuracy INT CHECK (severity_accuracy BETWEEN 1 AND 5),
    explanation_quality INT CHECK (explanation_quality BETWEEN 1 AND 5),
    actionability INT CHECK (actionability BETWEEN 1 AND 5),
    embedding vector(384),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for vector similarity search
CREATE INDEX IF NOT EXISTS idx_annotations_embedding ON annotations USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);

-- Model metrics table (tracks reward model performance over time)
CREATE TABLE IF NOT EXISTS model_metrics (
    id SERIAL PRIMARY KEY,
    annotation_count INT,
    accuracy FLOAT,
    precision_score FLOAT,
    recall_score FLOAT,
    f1_score FLOAT,
    threshold FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
