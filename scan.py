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
    """Initializes the database schema if not exists."""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
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
    CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id TEXT,
        text_content TEXT,
        FOREIGN KEY(doc_id) REFERENCES documents(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        type TEXT,
        attributes TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS relationships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id TEXT,
        target_id INTEGER,
        type TEXT,
        FOREIGN KEY(target_id) REFERENCES entities(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
        id TEXT PRIMARY KEY,
        doc_id TEXT,
        page_number INTEGER,
        path TEXT,
        sha256 TEXT,
        domain TEXT,
        FOREIGN KEY(doc_id) REFERENCES documents(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS image_entity_links (
        image_id TEXT,
        entity_id INTEGER,
        link_type TEXT,
        confidence FLOAT,
        FOREIGN KEY(image_id) REFERENCES images(id),
        FOREIGN KEY(entity_id) REFERENCES entities(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        id TEXT PRIMARY KEY,
        title TEXT,
        topic TEXT,
        created_at TEXT,
        url TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT,
        sender TEXT,
        content TEXT,
        FOREIGN KEY(chat_id) REFERENCES chats(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT,
        text TEXT,
        type TEXT,
        topic TEXT,
        move_type TEXT,
        opus_stage TEXT,
        FOREIGN KEY(chat_id) REFERENCES chats(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reference_sources (
        id TEXT PRIMARY KEY,
        short_name TEXT,
        citation TEXT,
        source_type TEXT,
        domain TEXT,
        year INTEGER
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reference_notes (
        id TEXT PRIMARY KEY,
        source_id TEXT,
        subject_type TEXT,
        subject_id TEXT,
        claim_text TEXT,
        stance TEXT,
        confidence FLOAT,
        page_ref TEXT,
        FOREIGN KEY(source_id) REFERENCES reference_sources(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS evidence_spans (
        note_id TEXT,
        doc_id TEXT,
        page_index INTEGER,
        span_text TEXT,
        FOREIGN KEY(note_id) REFERENCES reference_notes(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS research_phases (
        id TEXT PRIMARY KEY,
        label TEXT,
        opus_stage TEXT,
        start_date TEXT,
        end_date TEXT,
        notes TEXT
    )
    ''')
    conn.commit()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT,
        content TEXT,
        topic TEXT,
        FOREIGN KEY(chat_id) REFERENCES chats(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS compendium (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        source TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS glossary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        term TEXT UNIQUE,
        definition TEXT,
        category TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dictionary_entries (
        id TEXT PRIMARY KEY,
        headword TEXT UNIQUE,
        short_definition TEXT,
        physical_meaning TEXT,
        spiritual_meaning TEXT,
        opus_stage TEXT,
        domain TEXT,
        etymology TEXT,
        ambiguity_flag BOOLEAN,
        confidence_score INTEGER,
        created_by TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS entry_synonyms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_id TEXT,
        synonym TEXT,
        FOREIGN KEY(entry_id) REFERENCES dictionary_entries(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS entry_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_id TEXT,
        doc_id TEXT,
        citation_text TEXT,
        page_reference TEXT,
        source_type TEXT,
        FOREIGN KEY(entry_id) REFERENCES dictionary_entries(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS entry_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_id TEXT,
        image_id TEXT,
        iconographic_role TEXT,
        FOREIGN KEY(entry_id) REFERENCES dictionary_entries(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS entry_relationships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_id TEXT,
        related_entry_id TEXT,
        relation_type TEXT,
        FOREIGN KEY(entry_id) REFERENCES dictionary_entries(id)
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
    # Filter out common starting words and short/junk phrases
    blacklist = {"The", "In", "Of", "And", "To", "A", "An", "This", "That", "It", "Is", "For", "By", "With"}
    pattern = r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b'
    matches = re.findall(pattern, text)
    denylist = {"The Table", "Table Of", "Contents", "Chapter", "Index", "Introduction", "Preface", "Bibliography", "Appendix"}
    entities = []
    for a, b in matches:
        full = f"{a} {b}"
        if a not in blacklist and full not in denylist and len(full) > 5:
            entities.append(full)
    return entities

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

def export_json(conn, export_path, static=False):
    cursor = conn.cursor()
    os.makedirs(export_path, exist_ok=True)
    
    # 1. Documents (Relative paths if static)
    cursor.execute("SELECT id, filename, topic, author, period, size, created_at, path, century, language, summary FROM documents")
    docs = []
    for r in cursor.fetchall():
        path = r[7]
        if static:
            path = os.path.basename(path) # Hide absolute local paths
        docs.append({
            "id": r[0], 
            "filename": r[1], 
            "topic": r[2], 
            "author": r[3], 
            "period": r[4], 
            "size": r[5], 
            "created_at": r[6], 
            "path": path,
            "century": r[8],
            "language": r[9],
            "summary": r[10]
        })
    
    with open(os.path.join(export_path, "docs.json"), "w") as f:
        json.dump(docs, f, indent=2)

    cursor.execute("SELECT topic, COUNT(*) FROM documents GROUP BY topic")
    topic_counts = [{"label": row[0], "value": row[1]} for row in cursor.fetchall()]
    
    cursor.execute("SELECT period, COUNT(*) FROM documents WHERE period IS NOT NULL GROUP BY period")
    period_counts = [{"label": row[0], "value": row[1]} for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT author FROM documents WHERE author != 'Unknown' ORDER BY author")
    authors = [r[0] for r in cursor.fetchall()]

    # Timeline
    cursor.execute("SELECT strftime('%Y-%m', created_at) as month, COUNT(*) FROM documents GROUP BY month ORDER BY month LIMIT 24")
    timeline = [{"label": row[0], "value": row[1]} for row in cursor.fetchall()]

    # Word Cloud (Top Entities)
    cursor.execute('''
        SELECT e.name, COUNT(r.id) as freq 
        FROM entities e 
        JOIN relationships r ON e.id = r.target_id 
        GROUP BY e.name 
        ORDER BY freq DESC 
        LIMIT 100
    ''')
    wordcloud = [{"word": row[0], "weight": row[1]} for row in cursor.fetchall()]

    # Metrics (Reference Portal)
    cursor.execute("SELECT name, scholar_interest, user_curiosity, gap FROM metrics")
    metrics_data = [{"name": r[0], "scholar_interest": r[1], "user_curiosity": r[2], "gap": r[3]} for r in cursor.fetchall()]

    cursor.execute("SELECT COUNT(*) FROM entities")
    total_entities = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM chats")
    total_chats = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM questions")
    total_questions = cursor.fetchone()[0]

    stats = { 
        "topics": topic_counts, 
        "authors": authors,
        "periods": period_counts,
        "timeline": timeline,
        "wordcloud": wordcloud,
        "metrics": metrics_data,
        "total_docs": len(docs),
        "total_entities": total_entities,
        "total_chats": total_chats,
        "total_questions": total_questions,
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

    # 4. Chat Intelligence (questions.json, tables.json)
    cursor.execute("SELECT q.text, q.move_type, q.opus_stage, c.title, c.topic FROM questions q JOIN chats c ON q.chat_id = c.id")
    questions = [{"text": r[0], "type": r[1], "stage": r[2], "chat": r[3], "topic": r[4]} for r in cursor.fetchall()]
    with open(os.path.join(export_path, "questions.json"), "w") as f:
        json.dump(questions, f, indent=2)

    cursor.execute("SELECT t.content, t.prompt, t.title, t.topic, c.title FROM tables t JOIN chats c ON t.chat_id = c.id")
    tables = [{"content": r[0], "prompt": r[1], "title": r[2], "topic": r[3], "chat": r[4]} for r in cursor.fetchall()]
    with open(os.path.join(export_path, "tables.json"), "w") as f:
        json.dump(tables, f, indent=2)

    # 5. Specialized Entities (entities.json)
    cursor.execute("SELECT name, type, attributes FROM entities")
    all_ent = [{"name": r[0], "type": r[1], "attributes": r[2]} for r in cursor.fetchall()]
    with open(os.path.join(export_path, "entities.json"), "w") as f:
        json.dump(all_ent, f, indent=2)

    # 6. Knowledge Graph (graph.json)
    nodes = []
    edges = []
    
    cursor.execute("SELECT topic, COUNT(*) FROM documents GROUP BY topic")
    topics = cursor.fetchall()
    for t_name, count in topics:
        nodes.append({"data": {"id": t_name, "label": t_name, "type": "topic", "size": min(60, 30 + (count/10))}})

    # Entities (Top 100)
    cursor.execute('''
        SELECT e.name, COUNT(r.id) as freq 
        FROM entities e 
        JOIN relationships r ON e.id = r.target_id 
        GROUP BY e.name 
        ORDER BY freq DESC 
        LIMIT 100
    ''')
    top_entities = cursor.fetchall()
    for e_name, freq in top_entities:
        nodes.append({"data": {"id": e_name, "label": e_name, "type": "entity", "size": min(45, 20 + (freq/5))}})

    # Chats (Top 50)
    cursor.execute("SELECT id, title, topic FROM chats LIMIT 50")
    recent_chats = cursor.fetchall()
    for c_id, c_title, c_topic in recent_chats:
        label = c_title[:20]+"..." if not static else "Session: " + hashlib.md5(c_id.encode()).hexdigest()[:6]
        nodes.append({"data": {"id": c_id, "label": label, "type": "chat", "size": 25}})
        # Edge to topic
        if c_topic and c_topic != "General":
            edges.append({"data": {"id": f"chat_topic_{c_id}", "source": c_id, "target": c_topic, "weight": 2}})

    # Edges: Document -> Topic
    cursor.execute('''
        SELECT d.topic, e.name, COUNT(*) as weight
        FROM documents d
        JOIN relationships r ON d.id = r.source_id
        JOIN entities e ON r.target_id = e.id
        WHERE e.name IN ({})
        GROUP BY d.topic, e.name
        HAVING weight > 0
    '''.format(','.join(['?'] * len(top_entities))), [x[0] for x in top_entities])
    
    for t_name, e_name, weight in cursor.fetchall():
        edges.append({"data": {
            "id": f"rel_{t_name}_{e_name}",
            "source": e_name,
            "target": t_name,
            "weight": weight
        }})

    # Edges: Chat -> Entity
    cursor.execute('''
        SELECT r.source_id, e.name
        FROM relationships r
        JOIN entities e ON r.target_id = e.id
        WHERE r.type = 'DISCUSSED' AND r.source_id IN ({})
    '''.format(','.join(['?'] * len(recent_chats))), [x[0] for x in recent_chats])
    for c_id, e_name in cursor.fetchall():
        edges.append({"data": {"id": f"chat_ent_{c_id}_{e_name}", "source": c_id, "target": e_name, "weight": 2 }})

    with open(os.path.join(export_path, "graph.json"), "w") as f:
        # graph.html expects { nodes: [], edges: [] } now due to my remapping fix
        json.dump({"nodes": nodes, "edges": edges}, f, indent=2)

    # 5. Chats and Questions
    cursor.execute("SELECT id, title, created_at, topic, path FROM chats")
    all_chats_raw = cursor.fetchall()
    all_chats = []
    for r in all_chats_raw:
        title = r[1]
        path = r[4]
        if static:
            title = "Research Session " + hashlib.md5(r[0].encode()).hexdigest()[:6]
            path = "internal://redacted"
        all_chats.append({"id": r[0], "title": title, "created_at": r[2], "topic": r[3], "path": path})
    
    with open(os.path.join(export_path, "chats.json"), "w") as f:
        json.dump(all_chats, f, indent=2)

    cursor.execute("SELECT chat_id, text, move_type FROM questions")
    all_questions = [{"chat_id": r[0], "text": r[1], "type": r[2]} for r in cursor.fetchall()]
    with open(os.path.join(export_path, "questions.json"), "w") as f:
        json.dump(all_questions, f, indent=2)

    cursor.execute("SELECT chat_id, role, content, order_index FROM chat_messages")
    all_messages = []
    for r in cursor.fetchall():
        content = r[2]
        if static:
            content = "[CONTENT REDACTED FOR PUBLIC EXHIBIT]"
        all_messages.append({"chat_id": r[0], "role": r[1], "content": content, "index": r[3]})
    
    with open(os.path.join(export_path, "messages.json"), "w") as f:
        json.dump(all_messages, f, indent=2)

    # 6. Search Snippets
    search_index = {}
    cursor.execute("SELECT doc_id, text_content FROM chunks")
    for row in cursor.fetchall():
        search_index[row[0]] = row[1]
    
    # Add Chat messages to search index (Redact if static)
    if not static:
        cursor.execute("SELECT chat_id, content FROM chat_messages")
        for row in cursor.fetchall():
            cid = f"chat_{row[0]}"
            if cid in search_index: search_index[cid] += " " + row[1]
            else: search_index[cid] = row[1]

    with open(os.path.join(export_path, "search.json"), "w") as f:
        json.dump(search_index, f)

    # --- V8: Reference Layer Exports ---
    
    # 1. Sources (Bibliography)
    cursor.execute("SELECT * FROM reference_sources")
    sources = [dict(row) for row in cursor.fetchall()]
    with open(os.path.join(export_path, "sources.json"), "w") as f:
        json.dump(sources, f, indent=2)

    # 2. Reference Notes (Claims & Evidence)
    cursor.execute("SELECT * FROM reference_notes")
    notes = [dict(row) for row in cursor.fetchall()]
    # Attach evidence spans
    for note in notes:
        cursor.execute("SELECT * FROM evidence_spans WHERE note_id=?", (note['id'],))
        note['evidence'] = [dict(r) for r in cursor.fetchall()]
        
    with open(os.path.join(export_path, "reference_notes.json"), "w") as f:
        json.dump(notes, f, indent=2)

    # 3. Image Links (Semantic Correlation)
    # Join image_entity_links -> entities -> reference_notes
    cursor.execute("""
        SELECT iel.image_id, iel.entity_id, e.name as entity_name, iel.link_type, iel.confidence, 
               rn.id as note_id, rn.claim_text, rn.source_id
        FROM image_entity_links iel
        LEFT JOIN entities e ON iel.entity_id = e.id
        LEFT JOIN reference_notes rn ON rn.subject_id = e.id AND rn.subject_type = 'entity'
    """)
    image_links = [dict(row) for row in cursor.fetchall()]
    with open(os.path.join(export_path, "image_links.json"), "w") as f:
        json.dump(image_links, f, indent=2)

    # 4. Metrics (Desire Gap Analysis)
    # Scholar Interest: Count of notes per entity
    cursor.execute("SELECT subject_id, COUNT(*) as count FROM reference_notes WHERE subject_type='entity' GROUP BY subject_id")
    scholar_interest = {row['subject_id']: row['count'] for row in cursor.fetchall()}
    
    # User Curiosity: Count of questions per topic (Mapping topic -> entity is fuzzy, strictly we need entity linking in questions)
    # For V8, we'll use topic-based aggregation as proxy or if we have question_entity_links (not yet). 
    # Fallback: Count questions matched to entity names via simple inclusion.
    
    # Fetch all questions
    cursor.execute("SELECT text, move_type FROM questions")
    questions = cursor.fetchall()
    
    # Fetch all entities
    cursor.execute("SELECT id, name FROM entities")
    entities = cursor.fetchall()
    
    user_curiosity = {}
    for q in questions:
        q_text = q['text'].lower()
        weight = 2.0 if q['move_type'] == 'Critique' else 1.0
        for ent in entities:
            if ent['name'].lower() in q_text:
                eid = ent['id']
                user_curiosity[eid] = user_curiosity.get(eid, 0) + weight

    # Compute Gap
    # Normalize (simple max-scaling)
    max_scholar = max(scholar_interest.values()) if scholar_interest else 1
    max_user = max(user_curiosity.values()) if user_curiosity else 1
    
    metrics = []
    for ent in entities:
        eid = ent['id']
        s_val = scholar_interest.get(eid, 0) / max_scholar
        u_val = user_curiosity.get(eid, 0) / max_user
        gap = u_val - s_val
        
        if s_val > 0 or u_val > 0:
            metrics.append({
                "entity_id": eid,
                "name": ent['name'],
                "scholar_interest": round(s_val, 2),
                "user_curiosity": round(u_val, 2),
                "gap": round(gap, 2)
            })
            
    with open(os.path.join(export_path, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    # 5. Graph (Scholar Network)
    # Nodes: Scholars (from reference_sources authors?), Entities
    # Edges: Notes connecting Source -> Entity
    graph = {"nodes": [], "edges": []}
    
    # Nodes from Sources
    for src in sources:
        graph["nodes"].append({"id": src['id'], "label": src['short_name'], "type": "Source"})
    
    # Nodes from Entities (only those connected)
    active_entity_ids = set([m['entity_id'] for m in metrics])
    for ent in entities:
        if ent['id'] in active_entity_ids:
            graph["nodes"].append({"id": str(ent['id']), "label": ent['name'], "type": "Entity"})

    # Edges from Notes
    node_ids = set([n['id'] for n in graph['nodes']])
    for note in notes:
        src_id = note['source_id']
        tgt_id = str(note['subject_id'])
        if src_id in node_ids and tgt_id in node_ids:
             graph["edges"].append({
                 "source": src_id,
                 "target": tgt_id,
                 "label": note['claim_text'][:30] + "..." if note['claim_text'] else "Analyzes",
                 "type": "analyzes"
             })

    with open(os.path.join(export_path, "scholar_graph.json"), "w") as f:
        json.dump(graph, f, indent=2)

    # 6. Documentation (V8.1)
    documentation_files = []
    # Files to include
    doc_files = [
        ("CHANGELOG.md", "Version History"),
        ("walkthrough_v8.md", "User Guide (V8)"),
        ("implementation_plan_v8.md", "Architecture (V8)"),
        ("ai_prompts.md", "AI Persona Prompts"),
        ("scholarly_compendium.md", "Scholarly Source Text")
    ]
    
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for fname, title in doc_files:
        fpath = os.path.join(root_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                documentation_files.append({
                    "id": fname,
                    "title": title,
                    "content": f.read(),
                    "type": "documentation"
                })
    
    # Merge with existing docs catalog from step 1
    # Note: 'docs' was defined at line 325. We need to persist it or re-fetch.
    # To be safe, let's re-fetch or just append documentation_files to the existing list.
    full_docs = docs + documentation_files
    
    with open(os.path.join(export_path, "docs.json"), "w") as f:
        json.dump(full_docs, f, indent=2)

    # 7. Project Metadata (Design Lab)
    # Parse task.md for stats
    task_md_path = os.path.join(root_dir, "task.md")
    project_stats = {
        "phases": [],
        "total_tasks": 0,
        "completed_tasks": 0,
        "current_focus": "Unknown"
    }
    
    if os.path.exists(task_md_path):
        with open(task_md_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            current_phase = None
            for line in lines:
                line = line.strip()
                if line.startswith("## Phase"):
                    current_phase = {"name": line.replace("## ", ""), "completed": 0, "total": 0}
                    project_stats["phases"].append(current_phase)
                    if "[IN PROGRESS]" in line:
                         project_stats["current_focus"] = current_phase["name"]
                elif line.startswith("- ["):
                    if current_phase:
                        current_phase["total"] += 1
                        project_stats["total_tasks"] += 1
                        if "- [x]" in line:
                            current_phase["completed"] += 1
                            project_stats["completed_tasks"] += 1
    
    with open(os.path.join(export_path, "project_meta.json"), "w") as f:
        json.dump(project_stats, f, indent=2)

    with open(os.path.join(export_path, "config.json"), "w") as f:
        json.dump({
            "features": {"search": True, "graph": True, "chat": True, "metrics": True}, 
            "status": "V5: Reflexive Scholar Active",
            "mode": "static" if static else "local"
        }, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".")
    parser.add_argument("--enrich", action="store_true")
    parser.add_argument("--static", action="store_true")
    args = parser.parse_args()
    
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    # Only ingest if not just exporting static
    if args.dir != EXPORT_DIR:
        scan_and_ingest(conn, args.dir, enrich=args.enrich)
    
    export_json(conn, EXPORT_DIR, static=args.static)
    conn.close()
