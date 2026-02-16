import os
import sqlite3
import hashlib
import json
import argparse
from datetime import datetime

# --- Configuration ---
DB_NAME = "esoteric.db"
EXPORT_DIR = "docs" # GitHub Pages defaults to root or /docs
ROOT_DOCS_DIR = "." # Default to current dir, can be overridden

def get_file_hash(filepath):
    """Calculates SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def init_db(conn):
    """Initializes the database with Active tables and 'Nub' tables."""
    cursor = conn.cursor()

    # --- Active Tables ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        hash TEXT UNIQUE,
        filename TEXT,
        path TEXT,
        topic TEXT,
        size INTEGER,
        created_at DATETIME
    )
    ''')

    # --- Nub Tables (Future Features) ---
    # 1. Text Search / Chunking
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id TEXT,
        page_num INTEGER,
        text_content TEXT,
        FOREIGN KEY(doc_id) REFERENCES documents(id)
    )
    ''')

    # 2. Knowledge Graph (Entities)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        type TEXT,
        description TEXT
    )
    ''')
    
    # 2b. Knowledge Graph (Relationships)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS relationships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER,
        target_id INTEGER,
        type TEXT,
        weight REAL,
        chunk_id INTEGER
    )
    ''')

    # 3. Chat Logs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        id TEXT PRIMARY KEY,
        title TEXT,
        date DATETIME
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT,
        role TEXT,
        content TEXT,
        FOREIGN KEY(chat_id) REFERENCES chats(id)
    )
    ''')

    conn.commit()

def scan_and_ingest(conn, root_dir):
    """Scans directories and ingests files into SQLite."""
    cursor = conn.cursor()
    print(f"Scanning {root_dir}...")
    
    count = 0
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip hidden folders and the export directory
        if ".git" in dirpath or "docs" in dirpath:
            continue
            
        topic = os.path.basename(dirpath)
        if topic == ".": topic = "Unsorted"

        for filename in filenames:
            if filename.lower().endswith(".pdf"):
                filepath = os.path.join(dirpath, filename)
                
                # Basic metadata
                size = os.path.getsize(filepath)
                created = datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
                
                # Identity
                try:
                    with open(filepath, "rb") as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    doc_id = file_hash # Use hash as ID for now
                    
                    # Upsert (Insert or Ignore to avoid dupes)
                    cursor.execute('''
                    INSERT INTO documents (id, hash, filename, path, topic, size, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(hash) DO UPDATE SET
                        path=excluded.path,
                        topic=excluded.topic
                    ''', (doc_id, file_hash, filename, filepath, topic, size, created))
                    
                    count += 1
                    if count % 10 == 0:
                        print(f"Processed {count} files...", end="\r")
                        
                except Exception as e:
                    print(f"Error processing {filename}: {e}")

    conn.commit()
    print(f"\nScan complete. Processed {count} files.")

def export_json(conn, export_path):
    """Exports data to JSON for the static frontend."""
    if not os.path.exists(export_path):
        os.makedirs(export_path)
        
    cursor = conn.cursor()
    
    # 1. Catalog (docs.json)
    cursor.execute("SELECT id, filename, topic, size, created_at, path FROM documents")
    columns = [desc[0] for desc in cursor.description]
    # Simple dict comprehension for rows
    docs = []
    for row in cursor.fetchall():
        docs.append(dict(zip(columns, row)))
    
    with open(os.path.join(export_path, "docs.json"), "w") as f:
        json.dump(docs, f, indent=2)
        
    # 2. Stats (stats.json) - For the "Insights" tab
    cursor.execute("SELECT topic, COUNT(*) as count FROM documents GROUP BY topic ORDER BY count DESC")
    stats = [{"label": row[0], "value": row[1]} for row in cursor.fetchall()]

    with open(os.path.join(export_path, "stats.json"), "w") as f:
        json.dump(stats, f, indent=2)

    # 3. Config (config.json) - To toggle "Seed" vs "Full" features
    config = {
        "features": {
            "search": False, # Stub
            "graph": False,  # Stub
            "chat": False    # Stub
        },
        "generated_at": datetime.now().isoformat()
    }
    with open(os.path.join(export_path, "config.json"), "w") as f:
        json.dump(config, f, indent=2)
        
    print(f"Exported JSON artifacts to {export_path}/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Scanner")
    parser.add_argument("--dir", default=ROOT_DOCS_DIR, help="Directory to scan")
    args = parser.parse_args()
    
    conn = sqlite3.connect(DB_NAME)
    init_db(conn)
    scan_and_ingest(conn, args.dir)
    export_json(conn, EXPORT_DIR) # Export to docs/ folder for GitHub Pages
    conn.close()
