import os
import sqlite3
import hashlib
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup

def init_chats_db(conn):
    """Adds chat-related tables to the schema."""
    cursor = conn.cursor()
    # For development/refinement, we drop to ensure schema matches
    cursor.execute("DROP TABLE IF EXISTS chats")
    cursor.execute("DROP TABLE IF EXISTS chat_messages")
    cursor.execute("DROP TABLE IF EXISTS questions")
    cursor.execute("DROP TABLE IF EXISTS tables")
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        id TEXT PRIMARY KEY,
        title TEXT,
        created_at DATETIME,
        updated_at DATETIME,
        path TEXT,
        topic TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT,
        role TEXT,
        content TEXT,
        order_index INTEGER,
        FOREIGN KEY(chat_id) REFERENCES chats(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT,
        text TEXT,
        move_type TEXT,
        opus_stage TEXT,
        order_index INTEGER,
        FOREIGN KEY(chat_id) REFERENCES chats(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT,
        content TEXT,
        topic TEXT,
        FOREIGN KEY(chat_id) REFERENCES chats(id)
    )
    ''')
    conn.commit()

def parse_chat_html(filepath):
    """Parses a single chat index.html file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    title = soup.find('h1').text if soup.find('h1') else "Untitled Chat"
    
    # Extract meta dates
    meta_div = soup.find('div', class_='meta')
    created_at = None
    if meta_div:
        meta_text = meta_div.text
        # Example: Created: November 11, 2024 01:28 PM
        created_match = re.search(r'Created: (.*?) &bull;', meta_text)
        if created_match:
            try:
                created_at = datetime.strptime(created_match.group(1), '%B %d, %Y %I:%M %p').isoformat()
            except: pass

    messages = []
    msg_divs = soup.find_all('div', class_='msg')
    for i, div in enumerate(msg_divs):
        role_div = div.find('div', class_='role')
        role = role_div.text.lower() if role_div else "unknown"
        # Content is the text after the role div
        content = div.get_text(strip=True, separator='\n')
        # Clean up role prefix in content if necessary
        if role_div:
            content = content.replace(role_div.text, "", 1).strip()
        messages.append({
            "role": role,
            "content": content,
            "index": i
        })

    return {
        "title": title,
        "created_at": created_at,
        "messages": messages
    }

def extract_questions(messages):
    """Extracts questions and categorizes 'move types'."""
    questions = []
    for msg in messages:
        if msg['role'] == 'you' or msg['role'] == 'user':
            lines = msg['content'].split('\n')
            for line in lines:
                if '?' in line:
                    q_text = line.strip()
                    # Basic move type heuristic
                    move = "Investigate"
                    l_lower = q_text.lower()
                    if "summarize" in l_lower: move = "Summarize"
                    elif "table" in l_lower: move = "Tabulate"
                    elif "link" in l_lower or "compare" in l_lower or "relationship" in l_lower: move = "Cross-Reference"
                    elif "critique" in l_lower or "evaluate" in l_lower or "bias" in l_lower: move = "Critique"
                    
                    # Opus Stage Heuristic (V8)
                    stage = "Nigredo" # Default starting point
                    if any(w in l_lower for w in ["white", "purif", "clean", "silver", "moon"]): stage = "Albedo"
                    elif any(w in l_lower for w in ["yellow", "gold", "sun", "solar", "citrin"]): stage = "Citrinitas"
                    elif any(w in l_lower for w in ["red", "blood", "stone", "fire", "king", "rubedo"]): stage = "Rubedo"
                    
                    questions.append({
                        "text": q_text,
                        "move": move,
                        "opus_stage": stage,
                        "index": msg['index']
                    })
    return questions

def ingest_all_chats(db_path, chats_dir):
    conn = sqlite3.connect(db_path)
    init_chats_db(conn)
    cursor = conn.cursor()
    
    # Get existing scholars for linking
    cursor.execute("SELECT id, name FROM entities WHERE type='Entity'")
    scholars_map = {r[1]: r[0] for r in cursor.fetchall()}
    scholars = list(scholars_map.keys())

    # Pre-compile scholar search regex
    scholar_regex = None
    if scholars:
        scholar_regex = re.compile(r'\b(' + '|'.join(re.escape(s) for s in scholars) + r')\b', re.IGNORECASE)

    chat_count = 0
    q_count = 0
    
    print(f"Walking {chats_dir}...")
    all_indices = []
    for dirpath, dirnames, filenames in os.walk(chats_dir):
        if "index.html" in filenames:
            all_indices.append(os.path.join(dirpath, "index.html"))
    
    print(f"Found {len(all_indices)} chat sessions. Processing...")
    
    for html_file in all_indices:
        dirpath = os.path.dirname(html_file)
        foldername = os.path.basename(dirpath)
        
        try:
            chat_data = parse_chat_html(html_file)
            chat_id = hashlib.md5(html_file.encode()).hexdigest()[:12]
            
            topic = "General"
            topic_match = re.search(r'__(.*?)__', html_file)
            if topic_match:
                topic = topic_match.group(1).replace("-", " ")
            elif "_" in foldername:
                parts = foldername.split("_")
                if len(parts) > 1: topic = parts[1].replace("-", " ")

            cursor.execute('''
            INSERT OR REPLACE INTO chats (id, title, created_at, path, topic)
            VALUES (?, ?, ?, ?, ?)
            ''', (chat_id, chat_data['title'], chat_data['created_at'], html_file, topic))
            
            cursor.execute("DELETE FROM chat_messages WHERE chat_id = ?", (chat_id,))
            cursor.execute("DELETE FROM tables WHERE chat_id = ?", (chat_id,))
            for msg in chat_data['messages']:
                cursor.execute('''
                INSERT INTO chat_messages (chat_id, role, content, order_index)
                VALUES (?, ?, ?, ?)
                ''', (chat_id, msg['role'], msg['content'], msg['index']))
                
                # --- [NEW] Table Mining (V5) ---
                if "|" in msg['content'] and "---" in msg['content']:
                    # More permissive regex for typical markdown tables
                    table_matches = re.findall(r'(\|.*\|.*\n\|[\s|:-]+\n(?:\|.*\|.*\n)+)', msg['content'])
                    for full_table in table_matches:
                        cursor.execute('''
                            INSERT INTO tables (chat_id, content, topic)
                            VALUES (?, ?, ?)
                        ''', (chat_id, full_table, topic))

                # Scholar Linking (Optimized)
                if scholar_regex:
                    matches = set(scholar_regex.findall(msg['content']))
                    for scholar_name in matches:
                        # Find original case name from map
                        # This works because scholars_map contains the key in its original case
                        # but our regex is case-insensitive. We need the original key.
                        # For simplicity, we can just find the key that matches case-insensitively.
                        orig_name = next((s for s in scholars if s.lower() == scholar_name.lower()), scholar_name)
                        ent_id = scholars_map.get(orig_name)
                        if ent_id:
                            cursor.execute("INSERT OR IGNORE INTO relationships (source_id, target_id, type) VALUES (?, ?, ?)", (chat_id, ent_id, "DISCUSSED"))

            cursor.execute("DELETE FROM questions WHERE chat_id = ?", (chat_id,))
            questions = extract_questions(chat_data['messages'])
            for q in questions:
                cursor.execute('''
                INSERT INTO questions (chat_id, text, move_type, opus_stage, order_index)
                VALUES (?, ?, ?, ?, ?)
                ''', (chat_id, q['text'], q['move'], q['opus_stage'], q['index']))
                q_count += 1

            chat_count += 1
            if chat_count % 50 == 0:
                print(f"  Ingested {chat_count} chats...")
                conn.commit()
                
        except Exception as e:
            # print(f"Error ingesting {foldername}: {e}")
            continue

    conn.commit()
    conn.close()
    print(f"Ingestion complete. Chats: {chat_count}. Questions: {q_count}.")

if __name__ == "__main__":
    DB_PATH = "esoteric.db"
    CHATS_DIR = r"e:\pdf\esoteric studies chats"
    
    print(f"Checking path: {CHATS_DIR}")
    if os.path.exists(CHATS_DIR):
        print("Path exists! Starting walk...")
        ingest_all_chats(DB_PATH, CHATS_DIR)
    else:
        print(f"Chats directory not found: {CHATS_DIR}")
        # Try alternate path
        ALT_DIR = "/pdf/esoteric studies chats"
        print(f"Checking alt path: {ALT_DIR}")
        if os.path.exists(ALT_DIR):
            ingest_all_chats(DB_PATH, ALT_DIR)
