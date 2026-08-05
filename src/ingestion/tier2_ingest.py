"""
Tier 2 ingestion: reads data/pdfs/manifest.yaml, hashes each PDF, and for any
document that is new or changed, chunks it, embeds the chunks, and upserts
into documents + chunks. Unchanged documents (same content_hash) are skipped.

Run manually, offline, whenever a PDF is added or replaced:
    python -m src.ingestion.tier2_ingest
"""

from __future__ import annotations

import hashlib
import traceback
from pathlib import Path

import psycopg2
import psycopg2.extras
import yaml
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pgvector.psycopg2 import register_vector

from src.config.app_config import get_app_config
from src.config.settings import get_settings
from src.embeddings.embedding_service import get_embeddings

PDF_DIR = Path("data/pdfs")
MANIFEST_PATH = PDF_DIR / "manifest.yaml"


def load_manifest() -> list[dict]:
    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_existing_document(cur, filename: str) -> tuple[str, str] | None:
    cur.execute(
        "SELECT id, content_hash FROM documents WHERE filename = %s", (filename,)
    )
    row = cur.fetchone()
    return (str(row[0]), row[1]) if row else None


def upsert_document(cur, entry: dict, content_hash: str, document_id: str | None) -> str:
    if document_id:
        cur.execute(
            """
            UPDATE documents SET
                title = %(title)s,
                source_url = %(source_url)s,
                doc_type = %(doc_type)s,
                source_authority = %(source_authority)s,
                region = %(region)s,
                published_date = %(published_date)s,
                content_hash = %(content_hash)s,
                ingested_at = now()
            WHERE id = %(id)s
            """,
            {**entry, "content_hash": content_hash, "id": document_id},
        )
        return document_id

    cur.execute(
        """
        INSERT INTO documents (
            filename, title, source_url, doc_type, source_authority,
            region, published_date, content_hash
        ) VALUES (
            %(filename)s, %(title)s, %(source_url)s, %(doc_type)s, %(source_authority)s,
            %(region)s, %(published_date)s, %(content_hash)s
        )
        RETURNING id
        """,
        {**entry, "content_hash": content_hash},
    )
    return str(cur.fetchone()[0])


def delete_existing_chunks(cur, document_id: str) -> None:
    cur.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))


def chunk_pdf(path: Path, chunk_size: int, chunk_overlap: int) -> list[dict]:
    """Load a PDF page-by-page and split into chunks, preserving page numbers."""
    pages = PyPDFLoader(str(path)).load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for page in pages:
        page_number = page.metadata.get("page", None)
        for piece in splitter.split_text(page.page_content):
            piece = piece.strip()
            if piece:
                chunks.append({"text": piece, "page": page_number})
    return chunks


def insert_chunks(cur, document_id: str, chunks: list[dict], vectors: list, entry: dict) -> int:
    for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
        metadata = {
            "doc_type": entry["doc_type"],
            "region": entry.get("region"),
            "page": chunk["page"],
        }
        cur.execute(
            """
            INSERT INTO chunks (document_id, chunk_index, chunk_text, metadata, embedding)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (document_id, index, chunk["text"], psycopg2.extras.Json(metadata), vector),
        )
    return len(chunks)


def process_document(conn, entry: dict, app_config, embeddings) -> None:
    """Process one document in its own transaction, so a crash or error on
    one file never rolls back work already committed for another."""
    filename = entry["filename"]
    path = PDF_DIR / filename

    if not path.exists():
        print(f"SKIP (file not found): {filename}")
        return

    with conn.cursor() as cur:
        content_hash = hash_file(path)
        existing = get_existing_document(cur, filename)

        if existing:
            document_id, old_hash = existing
            if old_hash == content_hash:
                print(f"SKIP (unchanged): {filename}")
                return
            print(f"UPDATE (content changed): {filename}")
        else:
            document_id = None
            print(f"NEW: {filename}")

        document_id = upsert_document(cur, entry, content_hash, document_id)

        if existing:
            delete_existing_chunks(cur, document_id)

    # Chunking + embedding happen outside the open cursor, so if this crashes
    # (e.g. a bad PDF) there's no half-open transaction hanging around.
    chunks = chunk_pdf(
        path,
        chunk_size=app_config.splitting.chunk_size,
        chunk_overlap=app_config.splitting.chunk_overlap,
    )
    print(f"  parsed {len(chunks)} chunks, embedding...")
    texts = [c["text"] for c in chunks]
    vectors = embeddings.embed_documents(texts)

    with conn.cursor() as cur:
        count = insert_chunks(cur, document_id, chunks, vectors, entry)
    conn.commit()
    print(f"  -> {count} chunks embedded and inserted (committed)")


def main() -> None:
    settings = get_settings()
    app_config = get_app_config()
    embeddings = get_embeddings()

    manifest = load_manifest()
    print(f"Loaded manifest with {len(manifest)} documents")

    conn = psycopg2.connect(settings.database_url)
    register_vector(conn)

    for entry in manifest:
        try:
            process_document(conn, entry, app_config, embeddings)
        except Exception:
            conn.rollback()
            print(f"ERROR processing {entry['filename']}:")
            traceback.print_exc()
            print("  -> rolled back, continuing with next document")
            continue

    conn.close()
    print("Tier 2 ingestion complete.")


if __name__ == "__main__":
    main()