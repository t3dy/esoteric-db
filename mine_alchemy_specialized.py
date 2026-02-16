import os
import sqlite3
import json
import re

# Try importing pypdf
try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

# Configuration
DB_PATH = "esoteric_v5.db"
ALCHEMY_DIR = r"e:\pdf\alchemy"

# Seed Lists (Extendable)
MATERIALS = [
    "mercury", "sulfur", "salt", "antimony", "vitriol", "gold", "silver", "lead", 
    "iron", "copper", "tin", "quicksilver", "cinnabar", "azoth", "alkahest", 
    "philosophical mercury", "philosophical sulfur", "aqua regia", "aqua fortis",
    "spirit of wine", "vinegar", "sal ammoniac", "saltpeter", "tartar"
]

EQUIPMENT = [
    "alembic", "cucurbit", "athanor", "retort", "crucible", "pelican", "bain-marie", 
    "sand bath", "reverberatory furnace", "cupel", "beaker", "phial", "flask", 
    "receiver", "condenser", "pestle", "mortar", "bellows"
]

DEKNAMEN = [
    "green lion", "red king", "white queen", "red dragon", "black crow", "raven", 
    "peacock's tail", "cauda pavonis", "white eagle", "doves of diana", "serpent", 
    "ouroboros", "toad", "basilisk", "philosophical child", "rebis"
]

def extract_text(filepath, max_pages=10):
    if not HAS_PYPDF: return ""
    try:
        reader = pypdf.PdfReader(filepath)
        text = ""
        for i in range(min(len(reader.pages), max_pages)):
            try:
                page_text = reader.pages[i].extract_text()
                if page_text: text += page_text + " "
            except: continue
        return text.lower()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return ""

def mine_alchemy(db_path, scan_dir):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Mining Alchemy Specialized Data from: {scan_dir}")
    
    # Ensure tables exist (redundant check)
    cursor.execute("CREATE TABLE IF NOT EXISTS entities (id INTEGER PRIMARY KEY, name TEXT UNIQUE, type TEXT, attributes TEXT)")
    
    count = 0
    file_list = []
    for root, dirs, files in os.walk(scan_dir):
        for file in files:
            if file.lower().endswith(".pdf"):
                file_list.append(os.path.join(root, file))

    print(f"Found {len(file_list)} PDFs.")

    for filepath in file_list:
        text = extract_text(filepath)
        if not text: continue
        
        filename = os.path.basename(filepath)
        print(f"Scanning: {filename}...")

        # Scan for Materials
        for item in MATERIALS:
            if re.search(r'\b' + re.escape(item) + r'\b', text):
                attr = json.dumps({"source": filename, "category": "material"})
                try:
                    cursor.execute("INSERT OR IGNORE INTO entities (name, type, attributes) VALUES (?, ?, ?)", 
                                   (item.title(), "Alchemy Material", attr))
                except: pass

        # Scan for Equipment
        for item in EQUIPMENT:
            if re.search(r'\b' + re.escape(item) + r'\b', text):
                attr = json.dumps({"source": filename, "category": "equipment"})
                try:
                    cursor.execute("INSERT OR IGNORE INTO entities (name, type, attributes) VALUES (?, ?, ?)", 
                                   (item.title(), "Alchemy Equipment", attr))
                except: pass

        # Scan for Deknamen
        for item in DEKNAMEN:
            if re.search(r'\b' + re.escape(item) + r'\b', text):
                attr = json.dumps({"source": filename, "category": "symbol"})
                try:
                    cursor.execute("INSERT OR IGNORE INTO entities (name, type, attributes) VALUES (?, ?, ?)", 
                                   (item.title(), "Alchemy Symbol", attr))
                except: pass
        
        count += 1
        if count % 10 == 0: conn.commit()

    conn.commit()
    conn.close()
    print("Alchemy Mining Complete.")

if __name__ == "__main__":
    if os.path.exists(ALCHEMY_DIR):
        mine_alchemy(DB_PATH, ALCHEMY_DIR)
    else:
        print(f"Directory not found: {ALCHEMY_DIR}")
