-- migrate:up
CREATE TABLE chunks (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id    UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index    INT NOT NULL,
    chunk_text     TEXT NOT NULL,
    metadata       JSONB NOT NULL DEFAULT '{}',
    embedding      vector(384),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_chunks_document_id ON chunks (document_id);
CREATE INDEX idx_chunks_metadata ON chunks USING gin (metadata);
CREATE INDEX idx_chunks_embedding ON chunks
    USING hnsw (embedding vector_cosine_ops);

-- migrate:down
DROP TABLE IF EXISTS chunks;