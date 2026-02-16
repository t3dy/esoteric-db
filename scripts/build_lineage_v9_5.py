import sqlite3
import json
import os

DB_NAME = "esoteric.db"
OUTPUT_DIR = "esoteric_seed/data/snapshots"
OUTPUT_FILE = "hermetic_lineage.json"

def build_lineage():
    # If using relative path for db, make sure it's correct
    # The script is in scripts/ -> db is in parent
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), DB_NAME)
    
    if not os.path.exists(db_path):
        print(f"Error: Database {db_path} not found.")
        return

    # Ensure output dir
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "snapshots")
    os.makedirs(out_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Fetch Hermetic Figures
    cursor.execute("SELECT id, name, type, attributes FROM entities")
    rows = cursor.fetchall()
    
    nodes = []
    
    for r in rows:
        attrs = {}
        try:
            attrs = json.loads(r['attributes']) if r['attributes'] else {}
        except: pass
            
        is_hermetic = False
        if r['type'] and "Hermetic" in r['type']: is_hermetic = True
        if attrs.get('domain') == 'Hermeticism': is_hermetic = True
        if "Trismegistus" in r['name'] or "Ficino" in r['name'] or "Bruno" in r['name']: is_hermetic = True
        
        if is_hermetic:
            nodes.append({
                "id": str(r['id']),
                "label": r['name'],
                "period": attrs.get('period', 'Unknown Epoch'),
                "type": r['type']
            })

    # Default if empty
    if not nodes:
        print("Warning: No Hermetic figures found in DB. Seeding defaults.")
        nodes = [
            {"id": "h1", "label": "Hermes Trismegistus", "period": "Late Antiquity", "type": "Figure"},
            {"id": "h2", "label": "Marsilio Ficino", "period": "Renaissance", "type": "Figure"},
            {"id": "h3", "label": "Giordano Bruno", "period": "Renaissance", "type": "Figure"},
            {"id": "h4", "label": "Thoth", "period": "Ancient Egypt", "type": "Figure"},
            {"id": "h5", "label": "Cornelius Agrippa", "period": "Renaissance", "type": "Figure"}
        ]

    # 2. Construct Epochs
    epochs = [
        {
            "range": "1st - 3rd Century CE",
            "label": "The Prisca Theologia",
            "banner": "The foundational texts of the Corpus Hermeticum are written in Alexandria, synthesizing Greek philosophy with Egyptian theology.",
            "themes": ["Gnosis", "Mind (Nous)", "Regeneration"]
        },
        {
            "range": "1460 - 1600 CE",
            "label": "The Renaissance Restoration",
            "banner": "The Corpus is brought to Florence. Ficino translates it, sparking a wildfire of magical humanism across Europe.",
            "themes": ["Natural Magic", "Cabala", "prisca theologia"]
        }
    ]

    # 3. Construct Edges
    edges = [
        {"source": "h1", "target": "h2"},
        {"source": "h2", "target": "h3"},
        {"source": "h4", "target": "h1"}
    ]

    data = {
        "epochs": epochs,
        "nodes": nodes,
        "edges": edges
    }

    output_path = os.path.join(out_dir, OUTPUT_FILE)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Generated {output_path} with {len(nodes)} nodes.")
    conn.close()

if __name__ == "__main__":
    build_lineage()
