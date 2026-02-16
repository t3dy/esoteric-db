import os
import sqlite3
import hashlib
import json
import argparse
import re
from datetime import datetime

# --- Configuration ---
DB_NAME = "esoteric.db"
EXPORT_DIR = "docs"
ROOT_DOCS_DIR = "."

def init_db(conn):
    """Initializes a clean, fast database schema."""
    cursor = conn.cursor()
    # Force drop everything to ensure schema matches the new 'Catalog-First' logic
    cursor.execute("DROP TABLE IF EXISTS documents")
    cursor.execute("DROP TABLE IF EXISTS chunks") 
    cursor.execute("DROP TABLE IF EXISTS relationships")
    cursor.execute("DROP TABLE IF EXISTS entities")
    cursor.execute("DROP TABLE IF EXISTS chats")
    cursor.execute("DROP TABLE IF EXISTS chat_exchanges")
    
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
        created_at DATETIME
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
        type TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE chats (
        id TEXT PRIMARY KEY,
        title TEXT,
        date DATETIME
    )
    ''')
    cursor.execute('''
    CREATE TABLE chat_exchanges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT,
        topic_link TEXT,
        question TEXT,
        answer TEXT
    )
    ''')
    conn.commit()

def scan_and_ingest(conn, root_dir):
    """Sprints through the filesystem to build the catalog in seconds."""
    cursor = conn.cursor()
    target_path = os.path.abspath(root_dir)
    print(f"Cataloging: {target_path}")
    file_count = 0
    
    for dirpath, dirnames, filenames in os.walk(target_path):
        # Skip system/generated folders
        if any(x in dirpath for x in [".git", "docs", ".gemini", "brain"]): continue
            
        # Extract Movement from the folder relative to the root
        rel_path = os.path.relpath(dirpath, target_path)
        if rel_path == ".":
            movement = "General"
        else:
            # Top level subfolder is the Movement
            movement = rel_path.split(os.sep)[0]

        for filename in filenames:
            if filename.lower().endswith(".pdf"):
                filepath = os.path.join(dirpath, filename)
                
                try:
                    stats = os.stat(filepath)
                    # Unique ID based on filename and size
                    doc_id = hashlib.md5(f"{filename}{stats.st_size}".encode()).hexdigest()[:12]
                    
                    # Heuristic Metadata from Filename: "Author - Title.pdf"
                    author = "Unknown"
                    if " - " in filename:
                        author = filename.split(" - ", 1)[0].strip()

                    # Time Period Heuristic from folder path
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

                    file_count += 1
                    if file_count % 500 == 0: print(f"Cataloged {file_count} files...")
                except Exception as e:
                    # Silent failure to keep logs clean as requested
                    continue

    print(f"Catalog complete. Found {file_count} documents.")
    conn.commit()

def export_json(conn, export_path):
    cursor = conn.cursor()
    os.makedirs(export_path, exist_ok=True)
    
    # 1. Documents
    cursor.execute("SELECT id, filename, topic, author, period, size, created_at, path FROM documents")
    rows = cursor.fetchall()
    docs = [{"id": r[0], "filename": r[1], "topic": r[2], "author": r[3], "period": r[4], "size": r[5], "created_at": r[6], "path": r[7]} for r in rows]
    with open(os.path.join(export_path, "docs.json"), "w") as f:
        json.dump(docs, f, indent=2)

    # 2. Stats
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

    # 3. Categorical Lists (User Request)
    # For now, we seed these from Topics/Authors. Later we extract Figures/Scholars.
    lists = {
        "figures": ["Ramon Llull", "Giordano Bruno", "Albertus Magnus", "Henry Vaughan"],
        "scholars": ["Wouter Hanegraaff", "Frances Yates", "Antoine Faivre"],
        "texts": ["Ars Magna", "De Umbris Idearum", "Atalanta Fugiens"]
    }
    with open(os.path.join(export_path, "lists.json"), "w") as f:
        json.dump(lists, f, indent=2)

    # 4. Config
    with open(os.path.join(export_path, "config.json"), "w") as f:
        json.dump({"features": {"search": True, "graph": False, "chat": False}, "status": "Catalog Ready"}, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".")
    args = parser.parse_args()
    conn = sqlite3.connect(DB_NAME)
    init_db(conn)
    scan_and_ingest(conn, args.dir)
    export_json(conn, EXPORT_DIR)
    conn.close()
