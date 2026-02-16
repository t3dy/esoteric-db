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

import re

# ... (Previous imports)

def extract_entities_heuristic(text):
    """
    Simple heuristic: Extract capitalized phrases (2+ words) that might be entities.
    Excludes common stopwords and sentence starts (imperfect, but good for a seed).
    """
    # Regex for Title Case phrases of 2-4 words
    pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b'
    matches = re.findall(pattern, text)
    
    # Simple denylist to filter out common false positives
    denylist = {"The Table", "The Contents", "Chapter One", "Introduction To", "Table Of Contents"}
    entities = [m for m in matches if m not in denylist]
    
    # Return unique entities with a simple type "Concept"
    return list(set(entities))

def scan_and_ingest(conn, root_dir):
    """Scans directories and ingests files into SQLite."""
    cursor = conn.cursor()
    print(f"Scanning {root_dir}...")
    
    count = 0
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # ... (Previous loop logic)
        if ".git" in dirpath or "docs" in dirpath:
            continue
            
        topic = os.path.basename(dirpath)
        if topic == ".": topic = "Unsorted"

        for filename in filenames:
            if filename.lower().endswith(".pdf"):
                filepath = os.path.join(dirpath, filename)
                # ... (Previous metadata logic)
                size = os.path.getsize(filepath)
                created = datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
                
                try:
                    with open(filepath, "rb") as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    doc_id = file_hash
                    
                    # Upsert Document
                    # ... (Previous doc insert)
                    cursor.execute('''
                    INSERT INTO documents (id, hash, filename, path, topic, size, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(hash) DO UPDATE SET
                        path=excluded.path,
                        topic=excluded.topic
                    ''', (doc_id, file_hash, filename, filepath, topic, size, created))
                    
                    # Extract Text & Entities
                    # Optimization: Check if chunks exist
                    cursor.execute("SELECT COUNT(*) FROM chunks WHERE doc_id = ?", (doc_id,))
                    if cursor.fetchone()[0] == 0:
                        chunks = extract_text_from_pdf(filepath)
                        full_text = ""
                        for page_num, text in chunks:
                            cursor.execute('''
                            INSERT INTO chunks (doc_id, page_num, text_content)
                            VALUES (?, ?, ?)
                            ''', (doc_id, page_num, text))
                            full_text += text + " "
                        
                        # Extract Entities from the full extracted text
                        entities = extract_entities_heuristic(full_text)
                        for entity_name in entities:
                            # 1. Ensure Entity Exists
                            cursor.execute("INSERT OR IGNORE INTO entities (name, type) VALUES (?, ?)", (entity_name, "Concept"))
                            
                            # 2. Get Entity ID
                            cursor.execute("SELECT id FROM entities WHERE name = ?", (entity_name,))
                            entity_id = cursor.fetchone()[0]
                            
                            # 3. Create Relationship (Document -> Entity)
                            # We treat the Document as Source (using hash/rowid mapping would be better, but for now...)
                            # Actually, relationships table expects integer IDs. Let's map Doc Hash to an Integer if needed,
                            # OR just store the Doc Hash as source_id (SQLite is flexible, but cleaner to use dedicated ID).
                            # For the SEED: Let's simpler. We export graph.json directly from query.
                            # So we will just store the link in `relationships` using the TEXT hash as source? 
                            # limit: relationships defines source_id as INTEGER. 
                            # Let's fix the schema assumption or just use a junction table.
                            # For Speed: We will just export the "Graph" directly in export_json without persisting strict integer IDs for Docs yet.
                            # BUT to settle the "nub":
                            # Let's insert into `relationships` assuming source_id is the `rowid` of the document.
                            cursor.execute("SELECT rowid FROM documents WHERE id = ?", (doc_id,))
                            doc_rowid = cursor.fetchone()[0]
                            
                            cursor.execute('''
                            INSERT INTO relationships (source_id, target_id, type, weight)
                            VALUES (?, ?, ?, ?)
                            ''', (doc_rowid, entity_id, "MENTIONS", 1.0))

                    count += 1
                    if count % 10 == 0:
                        print(f"Processed {count} files...", end="\r")
                        
                except Exception as e:
                    print(f"  Error processing {filename}: {e}")

    conn.commit()
    print(f"\nScan complete. Processed {count} files.")

def export_json(conn, export_path):
    # ... (Previous export logic for docs/stats/search)
    if not os.path.exists(export_path):
        os.makedirs(export_path)
    
    cursor = conn.cursor()
    
    # 1. Docs
    cursor.execute("SELECT id, filename, topic, size, created_at, path FROM documents")
    columns = [desc[0] for desc in cursor.description]
    docs = [dict(zip(columns, row)) for row in cursor.fetchall()]
    with open(os.path.join(export_path, "docs.json"), "w") as f:
        json.dump(docs, f, indent=2)

    # 2. Stats (stats.json)
    # Counts by Topic
    print("Computing stats...")
    cursor.execute("SELECT topic, COUNT(*) FROM documents GROUP BY topic")
    topic_counts = [{"label": row[0], "value": row[1]} for row in cursor.fetchall()]

    # Timeline: Docs by Creation Date (Month)
    cursor.execute("SELECT strftime('%Y-%m', created_at) as month, COUNT(*) FROM documents GROUP BY month ORDER BY month")
    timeline_data = [{"label": row[0], "value": row[1]} for row in cursor.fetchall()]

    # Word Cloud: Top 100 Words
    # We'll do a simple heuristic on the `chunks` table.
    # Limiting to a sample of chunks to avoid OOM on large libraries.
    cursor.execute("SELECT text_content FROM chunks ORDER BY RANDOM() LIMIT 2000")
    
    word_freq = {}
    stopwords = {"the", "and", "of", "to", "in", "a", "is", "that", "for", "it", "as", "was", "with", "on", "by", "this", "are", "be", "from", "at", "or", "an", "not", "have", "which", "but", "can", "if", "their", "has", "will", "all", "so", "one", "no", "what", "more", "when", "there", "about", "they", "its", "up", "into", "out", "new", "some", "my", "we", "you", "he", "she", "his", "her", "had", "been", "would", "who", "them", "other", "than", "then", "now", "only", "first", "also", "two", "do", "any", "like", "our", "work", "after", "most", "time", "may", "these", "over", "see", "use", "make", "well", "way", "even", "because", "between", "through", "being", "much", "many", "how", "those", "where", "while", "during", "before", "own", "just", "very", "back", "still"}
    
    for row in cursor.fetchall():
        text = row[0].lower()
        words = re.findall(r'\b[a-z]{3,}\b', text) # Words with 3+ chars
        for w in words:
            if w not in stopwords:
                word_freq[w] = word_freq.get(w, 0) + 1
    
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:100]
    word_cloud_data = [{"word": w, "weight": c} for w, c in top_words]

    stats = {
        "topics": topic_counts,
        "timeline": timeline_data,
        "wordcloud": word_cloud_data
    }
    with open(os.path.join(export_path, "stats.json"), "w") as f:
        json.dump(stats, f, indent=2)
        
    # 3. Search (skipped for brevity in this replace block, assume it stays same)
    # ...

    # 4. Graph (graph.json)
    # We want a graph of: Topics -> Documents -> Entities
    # To keep it renderable, let's limit to Top Entities and their Docs.
    print("Building graph...")
    
    nodes = []
    links = []
    
    # Add Topics as Roots
    cursor.execute("SELECT DISTINCT topic FROM documents")
    topics = [r[0] for r in cursor.fetchall()]
    for i, topic in enumerate(topics):
        nodes.append({"id": f"topic_{i}", "label": topic, "type": "topic", "val": 10})
        
    # Add Docs (linked to Top Topics to keep graph sane? Or all?)
    # Let's limit to 100 docs for the viz to stay snappy
    cursor.execute("SELECT rowid, id, filename, topic FROM documents LIMIT 200")
    doc_rows = cursor.fetchall()
    doc_map = {} # rowid -> node_index
    
    for row in doc_rows:
        rowid, doc_id, filename, topic = row
        node_id = f"doc_{doc_id[:8]}"
        nodes.append({"id": node_id, "label": filename[:20]+"...", "type": "document", "val": 5})
        
        # Link to Topic
        try:
            topic_idx = topics.index(topic)
            links.append({"source": f"topic_{topic_idx}", "target": node_id})
        except: pass
        
        doc_map[rowid] = node_id

    # Add Top Entities (linked to these docs)
    # Get entities mentioned by these docs
    doc_rowids = list(doc_map.keys())
    if doc_rowids:
        placeholders = ','.join(['?'] * len(doc_rowids))
        cursor.execute(f'''
            SELECT r.source_id, e.name 
            FROM relationships r
            JOIN entities e ON r.target_id = e.id
            WHERE r.source_id IN ({placeholders})
            AND r.type = 'MENTIONS'
        ''', doc_rowids)
        
        rels = cursor.fetchall()
        
        # Filter: Only show entities connected to > 1 doc (to show connections)
        entity_counts = {}
        for _, name in rels:
            entity_counts[name] = entity_counts.get(name, 0) + 1
            
        top_entities = {name for name, count in entity_counts.items() if count > 1}
        
        # Add Entity Nodes and Links
        for source_rowid, name in rels:
            if name in top_entities:
                ent_id = f"ent_{hash(name)}"
                # Add node if not exists
                if not any(n['id'] == ent_id for n in nodes):
                    nodes.append({"id": ent_id, "label": name, "type": "entity", "val": 3})
                
                # Add Link
                doc_node_id = doc_map[source_rowid]
                links.append({"source": doc_node_id, "target": ent_id})

    graph_data = {"nodes": nodes, "links": links}
    with open(os.path.join(export_path, "graph.json"), "w") as f:
        json.dump(graph_data, f)

    # 5. Chats (chats.json) - Dummy Data for Seed
    # In a real version, we'd query the `chats` and `chat_messages` tables.
    print("Building chat index...")
    chats = [
        {
            "id": "chat_001",
            "title": "Welcome to Esoteric DB",
            "date": datetime.now().isoformat(),
            "messages": [
                {"role": "user", "content": "What is this database?", "ordinal": 1},
                {"role": "assistant", "content": "This is the Seed of your Esoteric Studies Database. It currently indexes your local PDFs.", "ordinal": 2},
                {"role": "user", "content": "What can I do here?", "ordinal": 3},
                {"role": "assistant", "content": "You can search for documents, visualize connections in the Graph tab, and eventually, I will be able to answer questions based on your library!", "ordinal": 4}
            ]
        },
        {
             "id": "chat_002",
             "title": "Sample Analysis: Alchemy",
             "date": datetime.now().isoformat(),
             "messages": [
                 {"role": "user", "content": "Find documents about Alchemy.", "ordinal": 1},
                 {"role": "assistant", "content": "I found several documents. Check the Library tab and filter by 'Alchemy'.", "ordinal": 2}
             ]
        }
    ]
    with open(os.path.join(export_path, "chats.json"), "w") as f:
        json.dump(chats, f, indent=2)

    # 6. Config
    config = {
        "features": {
            "search": True,
            "graph": True,
            "chat": True # ENABLED!
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
