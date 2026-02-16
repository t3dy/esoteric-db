import os
import sqlite3
import hashlib
import json
import argparse
from datetime import datetime

# Try importing pypdf for text extraction
try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False
    print("Warning: pypdf not installed. Text extraction skipped.")

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

def extract_text_from_pdf(filepath, max_pages=2):
    """Extracts text from the first N pages of a PDF."""
    if not HAS_PYPDF:
        return []
    
    chunks = []
    try:
        reader = pypdf.PdfReader(filepath)
        num_pages = len(reader.pages)
        for i in range(min(num_pages, max_pages)):
            page = reader.pages[i]
            text = page.extract_text()
            if text:
                chunks.append((i + 1, text.strip()))
    except Exception as e:
        print(f"  Error extracting text from {os.path.basename(filepath)}: {e}")
    return chunks

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
                    
                    # Upsert Document
                    cursor.execute('''
                    INSERT INTO documents (id, hash, filename, path, topic, size, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(hash) DO UPDATE SET
                        path=excluded.path,
                        topic=excluded.topic
                    ''', (doc_id, file_hash, filename, filepath, topic, size, created))
                    
                    # Extract & Insert Chunks (Text)
                    # Optimization: Only extract if we haven't already for this doc_id
                    cursor.execute("SELECT COUNT(*) FROM chunks WHERE doc_id = ?", (doc_id,))
                    if cursor.fetchone()[0] == 0:
                        chunks = extract_text_from_pdf(filepath)
                        for page_num, text in chunks:
                            cursor.execute('''
                            INSERT INTO chunks (doc_id, page_num, text_content)
                            VALUES (?, ?, ?)
                            ''', (doc_id, page_num, text))

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
    docs = []
    for row in cursor.fetchall():
        docs.append(dict(zip(columns, row)))
    
    with open(os.path.join(export_path, "docs.json"), "w") as f:
        json.dump(docs, f, indent=2)
        
    # 2. Stats (stats.json)
    cursor.execute("SELECT topic, COUNT(*) as count FROM documents GROUP BY topic ORDER BY count DESC")
    stats = [{"label": row[0], "value": row[1]} for row in cursor.fetchall()]

    with open(os.path.join(export_path, "stats.json"), "w") as f:
        json.dump(stats, f, indent=2)

    # 3. Search Index (search.json) - Lightweight!
    # We export: doc_id -> combined text of first few pages (truncated)
    print("Building search index...")
    cursor.execute("SELECT doc_id, text_content FROM chunks")
    search_index = {}
    for doc_id, text in cursor.fetchall():
        if doc_id not in search_index:
            search_index[doc_id] = ""
        # Limit total text per doc to ~1KB to keep JSON size manageable for static site
        if len(search_index[doc_id]) < 1000: 
            search_index[doc_id] += " " + text
            
    # Clean up whitespace
    for k in search_index:
        search_index[k] = " ".join(search_index[k].split())[:1000]

    with open(os.path.join(export_path, "search.json"), "w") as f:
        json.dump(search_index, f)

    # 4. Config (config.json)
    config = {
        "features": {
            "search": True,  # ENABLED!
            "graph": False, 
            "chat": False
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
    export_json(conn, EXPORT_DIR)
    conn.close()
