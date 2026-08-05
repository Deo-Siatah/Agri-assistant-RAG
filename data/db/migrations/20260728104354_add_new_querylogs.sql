-- migrate:up
ALTER TABLE query_logs
    ADD COLUMN diagnosis_scores JSONB,  -- e.g. {"GLS": 0.91, "NLB": 0.74}
    ADD COLUMN chunk_scores JSONB,      -- e.g. {"<chunk_uuid>": 0.68}
    ADD COLUMN low_confidence BOOLEAN NOT NULL DEFAULT FALSE;

-- migrate:down
ALTER TABLE query_logs
    DROP COLUMN IF EXISTS diagnosis_scores,
    DROP COLUMN IF EXISTS chunk_scores,
    DROP COLUMN IF EXISTS low_confidence;
