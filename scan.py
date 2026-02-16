import os
import sqlite3
import hashlib
import json
import argparse
import re
from datetime import datetime

# Try importing pypdf for text extraction
try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

# --- Configuration ---
DB_NAME = "esoteric.db"
EXPORT_DIR = "docs"
ROOT_DOCS_DIR = "."

def init_db(conn):
    """Initializes the database schema. Destructive for migration."""
    cursor = conn.cursor()
    # Migration: Drop if schema changed significantly
    cursor.execute("DROP TABLE IF EXISTS documents")
    cursor.execute("DROP TABLE IF EXISTS chunks") 
    cursor.execute("DROP TABLE IF EXISTS relationships")
    cursor.execute("DROP TABLE IF EXISTS entities")
    
    cursor.execute('''
    CREATE TABLE documents (
        id TEXT PRIMARY KEY,
        hash TEXT,
        filename TEXT,
        path TEXT,
        topic TEXT,
        author TEXT,
        period TEXT,
        size INTEGER,
        created_at DATETIME,
        enriched INTEGER DEFAULT 0
    )
    ''') 
    cursor.execute('''
    CREATE TABLE chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id TEXT,
        text_content TEXT,
        FOREIGN KEY(doc_id) REFERENCES documents(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        type TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE relationships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id TEXT,
        target_id INTEGER,
        type TEXT,
        FOREIGN KEY(target_id) REFERENCES entities(id)
    )
    ''')
    conn.commit()

def extract_text_silent(filepath, max_pages=3):
    if not HAS_PYPDF: return ""
    try:
        reader = pypdf.PdfReader(filepath)
        text = ""
        for i in range(min(len(reader.pages), max_pages)):
            try:
                page_text = reader.pages[i].extract_text()
                if page_text: text += page_text + " "
            except: continue
        return text.strip()
    except:
        return ""

def mine_names_heuristic(text):
    pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b'
    matches = re.findall(pattern, text)
    denylist = {"The Table", "Table Of", "Contents", "Chapter", "Index", "Introduction", "Preface", "Bibliography", "Appendix"}
    return [m for m in matches if m not in denylist and len(m) > 5]

def scan_and_ingest(conn, root_dir, enrich=False):
    cursor = conn.cursor()
    target_path = os.path.normpath(root_dir)
    print(f"Target: {target_path}")
    file_count = 0
    enriched_count = 0
    
    for dirpath, dirnames, filenames in os.walk(target_path):
        # RELATIVE skip to allow folder names like 'brain' if they are in the library
        # Only skip if it's a hidden folder or the system 'docs' folder
        if ".git" in dirpath or "\\docs" in dirpath or "/docs" in dirpath:
             continue
            
        rel_path = os.path.relpath(dirpath, target_path)
        movement = rel_path.split(os.sep)[0] if rel_path != "." else "General"

        for filename in filenames:
            if filename.lower().endswith(".pdf"):
                filepath = os.path.join(dirpath, filename)
                try:
                    stats = os.stat(filepath)
                    doc_id = hashlib.md5(f"{filename}{stats.st_size}".encode()).hexdigest()[:12]
                    
                    author = "Unknown"
                    if " - " in filename: author = filename.split(" - ", 1)[0].strip()

                    period = "Modern"
                    p_lower = dirpath.lower()
                    if "ancient" in p_lower or "antique" in p_lower: period = "Late Antique"
                    elif "medieval" in p_lower: period = "Medieval"
                    elif "renaissance" in p_lower: period = "Renaissance"
                    elif "enlightenment" in p_lower: period = "Early Modern"

                    cursor.execute('''
                    INSERT OR REPLACE INTO documents (id, filename, path, topic, author, period, size, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (doc_id, filename, filepath, movement, author, period, stats.st_size, datetime.fromtimestamp(stats.st_ctime).isoformat()))

                    if enrich:
                        text = extract_text_silent(filepath)
                        if text:
                            cursor.execute("INSERT INTO chunks (doc_id, text_content) VALUES (?, ?)", (doc_id, text[:2000]))
                            names = mine_names_heuristic(text)
                            for name in names:
                                cursor.execute("INSERT OR IGNORE INTO entities (name, type) VALUES (?, ?)", (name, "Entity"))
                                cursor.execute("SELECT id FROM entities WHERE name = ?", (name,))
                                ent_id = cursor.fetchone()[0]
                                cursor.execute("INSERT OR IGNORE INTO relationships (source_id, target_id, type) VALUES (?, ?, ?)", (doc_id, ent_id, "MENTIONS"))
                            cursor.execute("UPDATE documents SET enriched = 1 WHERE id = ?", (doc_id,))
                            enriched_count += 1

                    file_count += 1
                    if file_count % 100 == 0:
                        print(f"  Processed {file_count} files...")
                        if enrich: print(f"  Enriched {enriched_count} files...")
                        conn.commit()
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
                    continue

    print(f"Scan complete. Cataloged: {file_count}. Enriched: {enriched_count}.")
    conn.commit()

def export_json(conn, export_path):
    cursor = conn.cursor()
    os.makedirs(export_path, exist_ok=True)
    
    cursor.execute("SELECT id, filename, topic, author, period, size, created_at, path FROM documents")
    docs = [{"id": r[0], "filename": r[1], "topic": r[2], "author": r[3], "period": r[4], "size": r[5], "created_at": r[6], "path": r[7]} for r in cursor.fetchall()]
    with open(os.path.join(export_path, "docs.json"), "w") as f:
        json.dump(docs, f, indent=2)

    cursor.execute("SELECT topic, COUNT(*) FROM documents GROUP BY topic")
    topic_counts = [{"label": row[0], "value": row[1]} for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT author FROM documents WHERE author != 'Unknown' ORDER BY author")
    authors = [r[0] for r in cursor.fetchall()]

    stats = { 
        "topics": topic_counts, 
        "authors": authors,
        "total_docs": len(docs),
        "generated_at": datetime.now().isoformat()
    }
    with open(os.path.join(export_path, "stats.json"), "w") as f:
        json.dump(stats, f, indent=2)

    cursor.execute('''
        SELECT e.name, COUNT(r.id) as freq 
        FROM entities e 
        JOIN relationships r ON e.id = r.target_id 
        GROUP BY e.name 
        ORDER BY freq DESC 
        LIMIT 200
    ''')
    all_entities = cursor.fetchall()
    
    scholars, figures = [], []
    for name, freq in all_entities:
        if any(k in name.lower() for k in ["professor", "university", "editor", "journal"]):
            scholars.append(name)
        else:
            figures.append(name)

    lists = {
        "figures": figures[:50] or ["Ramon Llull", "Giordano Bruno", "Albertus Magnus"],
        "scholars": scholars[:50] or ["Wouter Hanegraaff", "Frances Yates"],
        "texts": ["Ars Magna", "De Umbris Idearum", "Atalanta Fugiens"]
    }
    with open(os.path.join(export_path, "lists.json"), "w") as f:
        json.dump(lists, f, indent=2)

    search_index = {}
    cursor.execute("SELECT doc_id, text_content FROM chunks")
    for row in cursor.fetchall():
        search_index[row[0]] = row[1]
    with open(os.path.join(export_path, "search.json"), "w") as f:
        json.dump(search_index, f)

    with open(os.path.join(export_path, "config.json"), "w") as f:
        json.dump({"features": {"search": len(search_index) > 0, "graph": False, "chat": False}, "status": "Enriched Ready"}, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".")
    parser.add_argument("--enrich", action="store_true")
    args = parser.parse_args()
    
    conn = sqlite3.connect(DB_NAME)
    init_db(conn)
    scan_and_ingest(conn, args.dir, enrich=args.enrich)
    export_json(conn, EXPORT_DIR)
    conn.close()
