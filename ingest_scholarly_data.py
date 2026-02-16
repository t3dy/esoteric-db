import sqlite3
import re
import os
import uuid

DB_PATH = "esoteric_v5.db"
# Use absolute path relative to this script
COMPENDIUM_MD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scholarly_compendium.md"))

SOURCES = [
    {
        "id": "src_obrist_2012",
        "short_name": "Obrist 2012",
        "citation": "Obrist, Barbara. 'Visualization in Medieval Alchemy'. Hylae, 2012.",
        "source_type": "Secondary",
        "domain": "Alchemy",
        "year": 2012
    },
    {
        "id": "src_mahe_ipm40",
        "short_name": "Mahé IPM 40",
        "citation": "Mahé, Jean-Pierre. 'Hermès en Haute-Égypte'. IPM 40, 1982.",
        "source_type": "Secondary",
        "domain": "Hermeticism",
        "year": 1982
    },
     {
        "id": "src_abraham_1998",
        "short_name": "Abraham 1998",
        "citation": "Abraham, Lyndy. 'A Dictionary of Alchemical Imagery'. Cambridge University Press, 1998.",
        "source_type": "Secondary",
        "domain": "Alchemy",
        "year": 1998
    }
]

def ingest_scholarly_data():
    if not os.path.exists(COMPENDIUM_MD):
        print(f"File not found: {COMPENDIUM_MD}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear existing Reference Data (idempotent)
    cursor.execute("DELETE FROM reference_sources")
    cursor.execute("DELETE FROM reference_notes")
    # cursor.execute("DELETE FROM evidence_spans") 

    print("Inserting Reference Sources...")
    for src in SOURCES:
        cursor.execute('''
            INSERT OR REPLACE INTO reference_sources (id, short_name, citation, source_type, domain, year)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (src['id'], src['short_name'], src['citation'], src['source_type'], src['domain'], src['year']))

    # Load Entities for Linking
    # We need a robust map.
    cursor.execute("SELECT id, name FROM entities")
    entities_map = {}
    for row in cursor.fetchall():
        ent_id = row[0]
        name = row[1]
        entities_map[name.lower()] = ent_id
    
    print(f"Loaded {len(entities_map)} entities for linking.")

    with open(COMPENDIUM_MD, "r", encoding="utf-8") as f:
        content = f.read()

    # Define processing logic
    def process_text_block(block_text, source_id):
        # Naive sentence splitting
        sentences = [s.strip() for s in block_text.split('. ') if len(s.strip()) > 20]
        
        count = 0
        for sent in sentences:
            # Check for entity mentions
            linked_ids = []
            sent_lower = sent.lower()
            for name, eid in entities_map.items():
                if name in sent_lower:
                     linked_ids.append(eid)
            
            # If entities found, creating specific notes
            if linked_ids:
                for eid in linked_ids:
                    note_id = str(uuid.uuid4())
                    cursor.execute('''
                        INSERT INTO reference_notes (id, source_id, subject_type, subject_id, claim_text, stance, confidence)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (note_id, source_id, "entity", eid, sent, "Analyzes", 0.85))
                    count += 1
        return count

    # 1. Obrist Analysis
    obrist_match = re.search(r'## 1\. Alchemical Imagery \(Obrist Analysis\)(.*?)---', content, re.S)
    if obrist_match:
        c = process_text_block(obrist_match.group(1), "src_obrist_2012")
        print(f"  Obrist: Created {c} notes.")

    # 2. Mahé Analysis
    mahe_match = re.search(r'## 3\. Hermeticism \(Mahé Analysis\)(.*)', content, re.S)
    if mahe_match:
        c = process_text_block(mahe_match.group(1), "src_mahe_ipm40")
        print(f"  Mahé: Created {c} notes.")

    # 3. Abraham (Glossary Terms)
    # This is structured: Term: Definition
    core_terms_section = re.search(r'### Core Terms\n(.*?)\n\n', content, re.S)
    if core_terms_section:
        terms = re.findall(r'- \*\*(.*?)\*\*: (.*)', core_terms_section.group(1))
        c = 0
        for term, definition in terms:
            term_lower = term.lower().strip()
            if term_lower in entities_map:
                eid = entities_map[term_lower]
                note_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO reference_notes (id, source_id, subject_type, subject_id, claim_text, stance, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (note_id, "src_abraham_1998", "entity", eid, definition, "Defines", 1.0))
                c += 1
        print(f"  Abraham: Created {c} definitions.")

    conn.commit()
    conn.close()
    print("V8 Reference Layer Ingestion Complete.")

if __name__ == "__main__":
    ingest_scholarly_data()
