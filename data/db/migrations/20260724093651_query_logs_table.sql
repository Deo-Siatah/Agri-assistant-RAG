-- migrate:up
CREATE TABLE query_logs (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text         TEXT NOT NULL,
    route_taken        TEXT,
    cache_hit          BOOLEAN NOT NULL DEFAULT FALSE,
    diagnosis_matches  TEXT[],
    chunk_matches      UUID[],
    weather_used       BOOLEAN NOT NULL DEFAULT FALSE,
    soil_used          BOOLEAN NOT NULL DEFAULT FALSE,
    latency_ms         INT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- migrate:down
DROP TABLE IF EXISTS query_logs;