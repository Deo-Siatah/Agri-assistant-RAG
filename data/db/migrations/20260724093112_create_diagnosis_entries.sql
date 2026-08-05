-- migrate:up
CREATE TABLE diagnosis_entries (
    id                    TEXT PRIMARY KEY,
    common_name           TEXT NOT NULL,
    category              TEXT NOT NULL,
    symptom_description   TEXT NOT NULL,
    likely_cause          TEXT,
    trigger_conditions    TEXT,
    disambiguation_notes  TEXT,
    soil_related          BOOLEAN NOT NULL DEFAULT FALSE,
    recommended_action    TEXT,
    confidence_source     TEXT NOT NULL,
    region_notes          TEXT,
    notes_conflicts       TEXT,
    embedding_source_text TEXT,
    embedding             vector(384),
    is_complete            BOOLEAN GENERATED ALWAYS AS (
                               recommended_action IS NOT NULL
                               AND recommended_action <> ''
                           ) STORED,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_diagnosis_category ON diagnosis_entries (category);
CREATE INDEX idx_diagnosis_soil_related ON diagnosis_entries (soil_related);
CREATE INDEX idx_diagnosis_embedding ON diagnosis_entries
    USING hnsw (embedding vector_cosine_ops);

-- migrate:down
DROP TABLE IF EXISTS diagnosis_entries;