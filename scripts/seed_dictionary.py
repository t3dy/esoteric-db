import sqlite3
import json
import uuid
import os

DB_NAME = "esoteric.db"

def seed():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Load candidates
    candidate_file = "docs/candidate_terms.json"
    if not os.path.exists(candidate_file):
        print("No candidates found. Run mine_candidate_terms.py first.")
        return

    with open(candidate_file, "r") as f:
        candidates = json.load(f)

    print(f"Seeding dictionary with {len(candidates)} candidates...")

    for c in candidates:
        term = c['term']
        ent_id = str(uuid.uuid4())[:8]
        
        # Determine domain
        domain = "Alchemy"
        if any(w in term.lower() for w in ["gnostic", "hermetic", "poimandres"]):
            domain = "Hermeticism"

        try:
            cursor.execute("""
                INSERT OR IGNORE INTO dictionary_entries (id, headword, domain, confidence_score, created_by)
                VALUES (?, ?, ?, ?, ?)
            """, (ent_id, term, domain, 10, "Heuristic Miner"))
        except sqlite3.Error as e:
            print(f"Error inserting {term}: {e}")

    conn.commit()
    print("Seeding complete.")
    conn.close()

if __name__ == "__main__":
    seed()
