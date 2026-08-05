-- migrate:up
ALTER TABLE documents ADD COLUMN filename TEXT;
ALTER TABLE documents ALTER COLUMN filename SET NOT NULL;
ALTER TABLE documents ADD CONSTRAINT documents_filename_key UNIQUE (filename);

ALTER TABLE documents DROP CONSTRAINT documents_content_hash_key;
CREATE INDEX idx_documents_content_hash ON documents (content_hash);

-- migrate:down
DROP INDEX IF EXISTS idx_documents_content_hash;
ALTER TABLE documents ADD CONSTRAINT documents_content_hash_key UNIQUE (content_hash);
ALTER TABLE documents DROP CONSTRAINT documents_filename_key;
ALTER TABLE documents DROP COLUMN filename;