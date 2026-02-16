import sqlite3
import os
import re
import hashlib
from datetime import datetime

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

DB_NAME = "esoteric.db"

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
        return text.strip()
    except: return ""

def mine():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find Hermetic documents
    cursor.execute("SELECT id, filename, path, topic FROM documents WHERE topic = 'hermetic' OR path LIKE '%hermetic%'")
    docs = cursor.fetchall()
    
    print(f"Found {len(docs)} Hermetic documents for deep scan.")

    for doc in docs:
        doc_id = doc['id']
        path = doc['path']
        
        if not os.path.exists(path):
            print(f"Skipping missing file: {path}")
            continue
            
        print(f"Deep scanning: {doc['filename']}...")
        text = extract_text(path, max_pages=10)
        text_lower = text.lower()
        
        # Heuristics for Figures, Lineage, and Concepts
        figures = []
        if any(w in text_lower for w in ["hermes", "trismegistus"]): figures.append("Hermes Trismegistus")
        if "ficino" in text_lower: figures.append("Marsilio Ficino")
        if "bruno" in text_lower: figures.append("Giordano Bruno")
        if "lazzarelli" in text_lower: figures.append("Lodovico Lazzarelli")
        if "agrippa" in text_lower: figures.append("Cornelius Agrippa")
        if "hanegraaff" in text_lower: figures.append("Wouter Hanegraaff")

        lineage = "General Hermeticism"
        if any(w in text_lower for w in ["prisca theologia", "chain of gold", "aglaophamus"]):
            lineage = "Prisca Theologia"
        elif any(w in text_lower for w in ["gnostic", "papyri", "pgm"]):
            lineage = "Technical Hermetica"
        elif any(w in text_lower for w in ["philosophy", "asclepius", "corpus hermeticum"]):
            lineage = "Philosophical Hermetica"
            
        concepts = []
        if "nous" in text_lower: concepts.append("Nous")
        if "monas" in text_lower: concepts.append("Monad")
        if "regeneration" in text_lower: concepts.append("Regeneration")
        if "microcosm" in text_lower or "macrocosm" in text_lower: concepts.append("Microcosm/Macrocosm")

        # Update attributes or summary
        summary = f"Lineage: {lineage}. Figures: {', '.join(figures)}. Key Concepts: {', '.join(concepts)}."
        
        # We can store this in the summary field or a JSON block in attributes if we had one
        # For now, let's update summary and period if detected
        cursor.execute("""
            UPDATE documents 
            SET summary = ?, 
                topic = 'hermetic'
            WHERE id = ?
        """, (summary, doc_id))

    conn.commit()
    print("Deep scan complete.")
    conn.close()

if __name__ == "__main__":
    mine()
