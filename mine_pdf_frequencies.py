import os
import sqlite3
import json
import re
from collections import Counter

# Try importing pypdf
try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

DB_NAME = "esoteric.db"
PATHS = {
    "Alchemy": r"e:\pdf\alchemy",
    "Hermetic": r"e:\pdf\hermetic"
}

STOPWORDS = {"the", "and", "that", "this", "from", "with", "which", "their", "they", "were", "been", "have", "would", "could", "should"}

def extract_text(filepath, max_pages=20):
    if not HAS_PYPDF: return ""
    try:
        reader = pypdf.PdfReader(filepath)
        text = ""
        for i in range(min(len(reader.pages), max_pages)):
            try:
                page_text = reader.pages[i].extract_text()
                if page_text: text += page_text + " "
            except: continue
        return text
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return ""

def mine():
    if not HAS_PYPDF:
        print("pypdf not installed. Aborting.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for domain, scan_dir in PATHS.items():
        if not os.path.exists(scan_dir):
            print(f"Path not found: {scan_dir}")
            continue

        print(f"Mining frequencies for {domain} in {scan_dir}...")
        word_counter = Counter()
        phrase_counter = Counter()

        file_list = []
        for root, dirs, files in os.walk(scan_dir):
            for file in files:
                if file.lower().endswith(".pdf"):
                    file_list.append(os.path.join(root, file))

        print(f"Found {len(file_list)} PDFs. Processing top 50 for depth...")
        for filepath in file_list[:50]:
            text = extract_text(filepath)
            if not text: continue
            
            # Clean and tokenize
            words = re.findall(r'\b[A-Z][a-z]{3,}\b|\b[a-z]{5,}\b', text)
            
            # Filter stopwords and lowercase small words
            cleaned_words = [w for w in words if w.lower() not in STOPWORDS]
            word_counter.update(cleaned_words)
            
            # Simple bigrams
            if len(cleaned_words) > 1:
                bigrams = [" ".join(cleaned_words[i:i+2]) for i in range(len(cleaned_words)-1)]
                phrase_counter.update(bigrams)

        # Insert Top Words (Names/Jargon)
        # We only take capitalized words as potential names/entities
        top_candidates = [w for w, count in word_counter.most_common(200) if w[0].isupper() and count > 10]
        
        added = 0
        for name in top_candidates:
            entity_type = f"{domain} Topic"
            attr = json.dumps({"source": "Frequency Mining", "frequency": word_counter[name]})
            try:
                cursor.execute("INSERT OR IGNORE INTO entities (name, type, attributes) VALUES (?, ?, ?)", 
                               (name, entity_type, attr))
                if cursor.rowcount > 0: added += 1
            except: pass
            
        print(f"Added {added} new entities for {domain}.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    mine()
