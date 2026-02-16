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
HERMETIC_DIR = r"e:\pdf\hermetic"

# Period Lists & Key Figures
PERIODS = {
    "Late Antiquity": ["Hermes Trismegistus", "Corpus Hermeticum", "Asclepius", "Stobaeus", "Zosimos", "Lactantius", "Poimandres"],
    "Medieval": ["Albertus Magnus", "Tabula Smaragdina", "Emerald Tablet", "Picatrix", "Liber de Causis"],
    "Renaissance": ["Marsilio Ficino", "Giovanni Pico della Mirandola", "Giordano Bruno", "John Dee", "Cornelius Agrippa", "Paracelsus"],
    "Enlightenment": ["Isaac Newton", "Robert Boyle", "Elias Ashmole", "Freemasonry", "Rosicrucian"],
    "Contemporary": ["Golden Dawn", "Aleister Crowley", "Julius Evola", "Rene Guenon", "Manly P. Hall", "Frances Yates"]
}

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

def mine_hermetic(db_path, scan_dir):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Mining Hermetic Lineages from: {scan_dir}")
    
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

        found_periods = set()

        for period, figures in PERIODS.items():
            for figure in figures:
                if re.search(r'\b' + re.escape(figure.lower()) + r'\b', text):
                    found_periods.add(period)
                    attr = json.dumps({"source": filename, "period": period, "category": "figure"})
                    try:
                        cursor.execute("INSERT OR IGNORE INTO entities (name, type, attributes) VALUES (?, ?, ?)", 
                                       (figure.title(), "Hermetic Figure", attr))
                    except: pass
        
        # Determine likely period of the text itself
        if found_periods:
            # Simple heuristic: most frequent period or just list all?
            # For now, we just tag the document implicitly by the entities found.
            # We could insert a "Document" entity but we have a documents table.
            # Let's just finish the entity mining.
            pass

        count += 1
        if count % 10 == 0: conn.commit()

    conn.commit()
    conn.close()
    print("Hermetic Mining Complete.")

if __name__ == "__main__":
    if os.path.exists(HERMETIC_DIR):
        mine_hermetic(DB_PATH, HERMETIC_DIR)
    else:
        print(f"Directory not found: {HERMETIC_DIR}")
