import os
import json
from datetime import datetime

def log_interaction(question, answer,confidence,retrieved_chunks,context,citations):
    record = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "answer": answer,
        "confidence": confidence,
        "retrieved_chunks": retrieved_chunks,
        "context": context,
        "citations": citations
    }

    # Ensure the outputs folder exists
    os.makedirs("data/outputs", exist_ok=True)

    with open("data/outputs/rag_logs.json", "a", encoding="utf-8") as f:
        f.write(json.dumps(record))
        f.write("\n")
