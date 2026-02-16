import sqlite3
import json
import os

DB_NAME = "esoteric.db"

def run_report():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Basic Stats
    cursor.execute("SELECT COUNT(*) FROM dictionary_entries")
    total_entries = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dictionary_entries WHERE short_definition IS NULL OR short_definition = ''")
    missing_def = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dictionary_entries WHERE domain IS NULL OR domain = ''")
    missing_cat = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dictionary_entries WHERE opus_stage IS NULL OR opus_stage = ''")
    missing_stage = cursor.fetchone()[0]

    # 2. Evidence Gaps (assuming an entry_evidence table or link)
    # If we don't have entry_evidence yet, this will be 0
    try:
        cursor.execute("SELECT entry_id, COUNT(*) as c FROM entry_evidence GROUP BY entry_id HAVING c < 3")
        thin_evidence = len(cursor.fetchall())
    except sqlite3.OperationalError:
        thin_evidence = total_entries

    # 3. New Candidate Headwords (High frequency entities not in dictionary)
    cursor.execute("""
        SELECT e.name, COUNT(r.id) as freq
        FROM entities e
        JOIN relationships r ON e.id = r.target_id
        WHERE e.name NOT IN (SELECT headword FROM dictionary_entries)
        GROUP BY e.name
        ORDER BY freq DESC
        LIMIT 200
    """)
    candidates = [{"term": r[0], "freq": r[1]} for r in cursor.fetchall()]

    report = {
        "total_entries": total_entries,
        "missing_short_definition": missing_def,
        "missing_category": missing_cat,
        "missing_opus_stage": missing_stage,
        "thin_evidence_count": thin_evidence,
        "new_candidate_headwords": candidates[:50]
    }

    # Ensure export directory exists
    export_path = "docs"
    os.makedirs(export_path, exist_ok=True)
    
    with open(os.path.join(export_path, "coverage.json"), "w") as f:
        json.dump(report, f, indent=2)

    print(f"Coverage report generated: {total_entries} entries analyzed.")
    conn.close()

if __name__ == "__main__":
    run_report()
