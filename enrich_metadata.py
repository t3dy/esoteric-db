import sqlite3
import os
import re

DB_NAME = "esoteric.db"

def enrich():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Ensure columns exist
    try:
        cursor.execute("ALTER TABLE documents ADD COLUMN century TEXT")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE documents ADD COLUMN language TEXT")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE documents ADD COLUMN summary TEXT")
    except sqlite3.OperationalError: pass

    cursor.execute("SELECT id, filename, path, topic, author, period FROM documents")
    docs = cursor.fetchall()
    
    updated_count = 0

    for doc in docs:
        doc_id = doc['id']
        fname = doc['filename']
        path = doc['path']
        
        new_author = doc['author']
        new_period = doc['period']
        new_century = None
        
        # 1. Author - Title Heuristic
        if " - " in fname:
            parts = fname.split(" - ", 1)
            new_author = parts[0].strip()
        elif " _ " in fname:
            parts = fname.split(" _ ", 1)
            new_author = parts[0].strip()

        # 2. Period Heuristic based on path and folder
        p_lower = path.lower()
        if any(k in p_lower for k in ["ancient", "classic", "greece", "rome"]):
            new_period = "Ancient"
        elif any(k in p_lower for k in ["late antique", "pgm", "gnostic", "papyri"]):
            new_period = "Late Antiquity"
        elif any(k in p_lower for k in ["medieval", "middle ages", "scholastic"]):
            new_period = "Medieval"
        elif any(k in p_lower for k in ["renaissance", "ficino", "bruno", "hermetic"]):
            new_period = "Renaissance"
        elif any(k in p_lower for k in ["enlightenment", "17th", "18th", "reason"]):
            new_period = "Enlightenment"
        elif "19th" in p_lower or "victorian" in p_lower or "romantic" in p_lower:
            new_period = "19th Century"
        elif any(k in p_lower for k in ["modern", "contemporary", "post-modern", "20th", "21st"]):
            new_period = "Contemporary"
        elif new_period == "Modern":
            new_period = "Contemporary"
        
        # Folder-based overrides
        if "/alchemy/" in path:
            if new_period == "Contemporary": new_period = "Renaissance" # Default to Renaissance for alchemy if modern
        
        # 3. Clean fallback
        if new_author == "Unknown" and "Press" in fname:
            new_author = "Academic Publication"

        cursor.execute("""
            UPDATE documents 
            SET author = ?, period = ?, century = ?
            WHERE id = ?
        """, (new_author, new_period, new_century, doc_id))
        updated_count += 1

    conn.commit()
    print(f"Enrichment complete. Updated {updated_count} records.")
    conn.close()

if __name__ == "__main__":
    enrich()
