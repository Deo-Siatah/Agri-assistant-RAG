"""
Tier 1 ingestion: reads the verified pest/disease CSV, embeds the diagnostic
text for each row, and upserts into diagnosis_entries.

Run manually, offline, whenever the CSV is added to or corrected:
    python -m src.ingestion.tier1_ingest
"""

from __future__ import annotations

import csv
from pathlib import Path

import psycopg2
from pgvector.psycopg2 import register_vector

from src.config.settings import get_settings
from src.embeddings.embedding_service import get_embeddings

CSV_PATH = Path("data/csv/maize_conditions.csv")

UPSERT_SQL = """
INSERT INTO diagnosis_entries (
    id, common_name, category, symptom_description, likely_cause,
    trigger_conditions, disambiguation_notes, soil_related,
    recommended_action, confidence_source, region_notes, notes_conflicts,
    embedding_source_text, embedding, updated_at
) VALUES (
    %(id)s, %(common_name)s, %(category)s, %(symptom_description)s, %(likely_cause)s,
    %(trigger_conditions)s, %(disambiguation_notes)s, %(soil_related)s,
    %(recommended_action)s, %(confidence_source)s, %(region_notes)s, %(notes_conflicts)s,
    %(embedding_source_text)s, %(embedding)s, now()
)
ON CONFLICT (id) DO UPDATE SET
    common_name           = EXCLUDED.common_name,
    category               = EXCLUDED.category,
    symptom_description     = EXCLUDED.symptom_description,
    likely_cause            = EXCLUDED.likely_cause,
    trigger_conditions      = EXCLUDED.trigger_conditions,
    disambiguation_notes    = EXCLUDED.disambiguation_notes,
    soil_related            = EXCLUDED.soil_related,
    recommended_action      = EXCLUDED.recommended_action,
    confidence_source       = EXCLUDED.confidence_source,
    region_notes            = EXCLUDED.region_notes,
    notes_conflicts         = EXCLUDED.notes_conflicts,
    embedding_source_text   = EXCLUDED.embedding_source_text,
    embedding               = EXCLUDED.embedding,
    updated_at              = now();
"""


def _to_bool(value: str) -> bool:
    return str(value).strip().upper() == "TRUE"


def _none_if_blank(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value if value else None


def load_rows(csv_path: Path) -> list[dict]:
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def build_embedding_text(row: dict) -> str:
    parts = [
        row.get("symptom_description", "") or "",
        row.get("disambiguation_notes", "") or "",
    ]
    return " ".join(p.strip() for p in parts if p.strip())


def main() -> None:
    settings = get_settings()
    embeddings = get_embeddings()

    rows = load_rows(CSV_PATH)
    print(f"Loaded {len(rows)} rows from {CSV_PATH}")

    texts = [build_embedding_text(row) for row in rows]
    print("Embedding all rows (batch)...")
    vectors = embeddings.embed_documents(texts)

    conn = psycopg2.connect(settings.database_url)
    register_vector(conn)

    inserted = 0
    with conn:
        with conn.cursor() as cur:
            for row, embedding_text, vector in zip(rows, texts, vectors):
                params = {
                    "id": row["id"].strip(),
                    "common_name": row["common_name"].strip(),
                    "category": row["category"].strip(),
                    "symptom_description": row["symptom_description"].strip(),
                    "likely_cause": _none_if_blank(row.get("likely_cause")),
                    "trigger_conditions": _none_if_blank(row.get("trigger_conditions")),
                    "disambiguation_notes": _none_if_blank(row.get("disambiguation_notes")),
                    "soil_related": _to_bool(row.get("soil_related", "FALSE")),
                    "recommended_action": _none_if_blank(row.get("recommended_action")),
                    "confidence_source": row["confidence_source"].strip(),
                    "region_notes": _none_if_blank(row.get("region_notes")),
                    "notes_conflicts": _none_if_blank(row.get("notes_conflicts")),
                    "embedding_source_text": embedding_text,
                    "embedding": vector,
                }
                cur.execute(UPSERT_SQL, params)
                inserted += 1

    conn.close()
    print(f"Upserted {inserted} rows into diagnosis_entries.")


if __name__ == "__main__":
    main()