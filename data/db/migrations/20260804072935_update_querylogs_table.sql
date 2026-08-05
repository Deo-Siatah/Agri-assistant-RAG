-- migrate:up
ALTER TABLE query_logs ADD COLUMN request_id UUID;
CREATE INDEX idx_query_logs_request_id ON query_logs (request_id);

-- migrate:down
DROP INDEX IF EXISTS idx_query_logs_request_id;
ALTER TABLE query_logs DROP COLUMN request_id;