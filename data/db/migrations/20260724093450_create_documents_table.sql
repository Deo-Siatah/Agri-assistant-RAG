-- migrate:up
CREATE TABLE documents (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title             TEXT NOT NULL,
    source_url        TEXT,
    doc_type          TEXT NOT NULL,
    source_authority  TEXT,
    region            TEXT,
    published_date    DATE,
    content_hash      TEXT UNIQUE NOT NULL,
    ingested_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- migrate:down
DROP TABLE IF EXISTS documents;