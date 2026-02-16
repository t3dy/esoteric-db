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
    # PREVENT DATA LOSS: Only create if not exists
    # cursor.execute("DROP TABLE IF EXISTS prompts")
    # cursor.execute("DROP TABLE IF EXISTS tables")
    
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
    CREATE TABLE IF NOT EXISTS prompts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT,
        text TEXT,
        move_type TEXT,
        opus_stage TEXT,
        mentions_topic TEXT,
        mentions_figure TEXT,
        mentions_text TEXT,
        mentions_scholar TEXT,
        strategy_summary TEXT,
        prompt_topic TEXT,
        prompt_alchemist TEXT,
        prompt_scholar TEXT,
        prompt_text TEXT,
        order_index INTEGER,
        FOREIGN KEY(chat_id) REFERENCES chats(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT,
        content TEXT,
        prompt TEXT,
        title TEXT,
        topic TEXT,
        FOREIGN KEY(chat_id) REFERENCES chats(id)
    )
    ''')
    conn.commit()

def html_table_to_markdown(soup_table):
    """Crude conversion of BS4 table tag to Markdown."""
    rows = soup_table.find_all('tr')
    if not rows: return None
    
    md_rows = []
    for i, row in enumerate(rows):
        cols = row.find_all(['td', 'th'])
        # Clean text
        row_data = [c.get_text(strip=True).replace("|", "\\|") for c in cols]
        if not row_data: continue
        
        md_rows.append("| " + " | ".join(row_data) + " |")
        
        # Add separator after header
        if i == 0:
            md_rows.append("| " + " | ".join(["---"] * len(row_data)) + " |")
            
    return "\n".join(md_rows)

def save_table(cursor, chat_id, content, msg, chat_data, topic):
    """Helper to save table to DB."""
    prompt = ""
    # Capture prompt from previous message if it exists
    if msg['index'] > 0:
        prev_msg = next((m for m in chat_data['messages'] if m['index'] == msg['index']-1), None)
        if prev_msg: prompt = prev_msg['content']
    
    # Fallback: if table is in the middle of a message, the first part is the "prompt"
    if not prompt and len(msg['content'].split(content[:20])[0]) > 5:
        prompt = msg['content'].split(content[:20])[0].strip()

    title = "Scholarly Data Table"
    if prompt:
        title_line = prompt.split("\n")[0].strip()
        if len(title_line) > 50: title_line = title_line[:47] + "..."
        title = title_line

    cursor.execute('''
        INSERT INTO tables (chat_id, content, prompt, title, topic)
        VALUES (?, ?, ?, ?, ?)
    ''', (chat_id, content, prompt[:500], title, topic))

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
        role = role_div.get_text(strip=True).lower() if role_div else "unknown"
        
        # Look for bubble content
        bubble = div.find('div', class_='bubble')
        if bubble:
            # We want to preserve the HTML tables if they exist
            # but for general mining, we get the text content
            content = bubble.get_text(strip=True, separator='\n')
            # However, for the 'content' field in messages, we'll store everything except the role
            msg_html = str(bubble)
        else:
            content = div.get_text(strip=True, separator='\n')
            if role_div:
                content = content.replace(role_div.text, "", 1).strip()
            msg_html = str(div)

        messages.append({
            "role": role,
            "content": content,
            "html": msg_html,
            "index": i
        })

    return {
        "title": title,
        "created_at": created_at,
        "messages": messages
    }

def extract_prompts(messages, scholars, current_topic):
    """Extracts user prompts and categorizes them with nuanced metadata."""
    prompts = []
    # Key figures/texts markers
    text_keywords = ["ms", "manuscript", "text", "book", "codex", "treatise"]
    
    for msg in messages:
        # Foolproof user input detection: only 'you' or 'user'
        if msg['role'] in ['you', 'user']:
            content = msg['content']
            # We treat the entire user message as a potential prompt if it's substantial
            # or extract sentence-level if multiple disparate inquiries exist.
            # For this master-list, we'll use the whole message block to preserve nuance.
            
            p_text = content.strip()
            if len(p_text) < 5: continue

            l_lower = p_text.lower()
            
            # --- Move Type Categorization ---
            move = "Investigate"
            if "summarize" in l_lower: move = "Summarize"
            elif "table" in l_lower: move = "Tabulate"
            elif any(w in l_lower for w in ["link", "compare", "relationship", "connect"]): move = "Cross-Reference"
            elif any(w in l_lower for w in ["critique", "evaluate", "bias", "accuracy"]): move = "Critique"
            
            # --- Opus Stage Heuristic ---
            stage = "Nigredo"
            if any(w in l_lower for w in ["white", "purif", "clean", "silver", "moon"]): stage = "Albedo"
            elif any(w in l_lower for w in ["yellow", "gold", "sun", "solar", "citrin"]): stage = "Citrinitas"
            elif any(w in l_lower for w in ["red", "blood", "stone", "fire", "king", "rubedo"]): stage = "Rubedo"
            
            # --- Nuanced Mentions Mining ---
            mentions_topic = current_topic if current_topic in l_lower or "this topic" in l_lower else None
            
            # Mentioned figures (from corpus entities)
            found_figures = [s for s in scholars if s.lower() in l_lower]
            mentions_figure = ", ".join(found_figures) if found_figures else None
            
            # Mentions scholarship/scholars specifically
            is_scholarly = any(w in l_lower for w in ["scholar", "researcher", "historian", "academic", "literature"])
            mentions_scholar = "Yes" if is_scholarly or found_figures else "No"
            
            # Mentions texts
            mentions_text = "Yes" if any(w in l_lower for w in text_keywords) else "No"

            prompts.append({
                "text": p_text,
                "move": move,
                "opus_stage": stage,
                "mentions_topic": mentions_topic,
                "mentions_figure": mentions_figure,
                "mentions_text": mentions_text,
                "mentions_scholar": mentions_scholar,
                "index": msg['index']
            })
    return prompts

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
                
                # --- [NEW] Table Mining (V5/V9.3) ---
                has_extracted_table = False
                
                # 1. Markdown Table Mining
                if "|" in msg['content'] and "---" in msg['content']:
                    table_matches = re.findall(r'(\|.*\|.*\n\|[\s|:-]+\n(?:\|.*\|.*\n)+)', msg['content'])
                    for full_table in table_matches:
                        has_extracted_table = True
                        save_table(cursor, chat_id, full_table, msg, chat_data, topic)

                # 2. HTML Table Mining (V9.3)
                if not has_extracted_table and "<table>" in msg.get('html', ''):
                    temp_soup = BeautifulSoup(msg['html'], 'html.parser')
                    html_tables = temp_soup.find_all('table')
                    for table_tag in html_tables:
                        # Convert HTML table back to Markdown for consistency in the Lab
                        md_table = html_table_to_markdown(table_tag)
                        if md_table:
                            save_table(cursor, chat_id, md_table, msg, chat_data, topic)

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

            cursor.execute("DELETE FROM prompts WHERE chat_id = ?")
            prompts = extract_prompts(chat_data['messages'], scholars, topic)
            for p in prompts:
                cursor.execute('''
                INSERT INTO prompts (chat_id, text, move_type, opus_stage, mentions_topic, mentions_figure, mentions_text, mentions_scholar, order_index)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (chat_id, p['text'], p['move'], p['opus_stage'], p['mentions_topic'], p['mentions_figure'], p['mentions_text'], p['mentions_scholar'], p['index']))
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
    print(f"Ingestion complete. Chats: {chat_count}. Prompts: {q_count}.")

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
