import sqlite3
import json
import re
import os

DB_NAME = "esoteric.db"

def mine_candidates():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Heuristic: TitleCase phrases in chunks
    # We'll look for 2-3 word TitleCase sequences that appear frequently
    cursor.execute("SELECT doc_id, text_content FROM chunks LIMIT 1000")
    chunks = cursor.fetchall()
    
    candidate_map = {}
    
    # Patterns for discovery
    patterns = [
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b', # TitleCase entities
        r'called\s+"?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"?', # "called X"
        r'known\s+as\s+"?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"?' # "known as X"
    ]

    for chunk in chunks:
        text = chunk['text_content']
        for p in patterns:
            matches = re.findall(p, text)
            for m in matches:
                if len(m) < 4: continue
                if m not in candidate_map:
                    candidate_map[m] = {"term": m, "count": 0, "examples": []}
                candidate_map[m]["count"] += 1
                if len(candidate_map[m]["examples"]) < 3:
                    candidate_map[m]["examples"].append({
                        "doc_id": chunk['doc_id'],
                        "snippet": text[:150] + "..."
                    })

    # Sort and filter
    sorted_candidates = sorted(candidate_map.values(), key=lambda x: x['count'], reverse=True)
    top_candidates = [c for c in sorted_candidates if c['count'] > 1]

    # Save to JSON
    export_path = "docs"
    os.makedirs(export_path, exist_ok=True)
    
    with open(os.path.join(export_path, "candidate_terms.json"), "w") as f:
        json.dump(top_candidates[:100], f, indent=2)

    print(f"Candidate mining complete. Found {len(top_candidates)} potential terms.")
    conn.close()

if __name__ == "__main__":
    mine_candidates()
