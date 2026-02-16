import json
import os
from datetime import datetime

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
SNAPSHOT_DIR = os.path.join(BASE_DIR, "data", "snapshots")

def build_index():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    
    items = []
    
    # 1. Documents
    docs_path = os.path.join(DOCS_DIR, "docs.json")
    if os.path.exists(docs_path):
        with open(docs_path, "r") as f:
            docs = json.load(f)
            for d in docs:
                items.append({
                    "id": f"doc:{d['id']}",
                    "kind": "doc",
                    "title": d.get("title") or d.get("filename"),
                    "subtitle": f"{d.get('author', 'Unknown')} • {d.get('period', 'Undetermined')}",
                    "tags": [d.get("topic", "General"), d.get("period", "General")],
                    "score_boost": 1.0,
                    "route": {"page": "library.html", "params": {"doc": d['id']}}
                })

    # 2. Dictionary
    dict_path = os.path.join(DOCS_DIR, "dictionary.json")
    if os.path.exists(dict_path):
        with open(dict_path, "r") as f:
            entries = json.load(f)
            for e in entries:
                items.append({
                    "id": f"entry:{e.get('slug') or e.get('headword', '').lower().replace(' ', '-')}",
                    "kind": "dictionary",
                    "title": e.get("headword"),
                    "subtitle": f"{e.get('domain', 'Esotericism')} • {e.get('opus_stage', 'Symbol')}",
                    "tags": [e.get("domain", "General"), "Definition"],
                    "route": {"page": "dictionary.html", "params": {"entry": e.get('slug') or e.get('headword', '').lower().replace(' ', '-')}}
                })

    # 3. Entities
    ent_path = os.path.join(DOCS_DIR, "entities.json")
    if os.path.exists(ent_path):
        with open(ent_path, "r") as f:
            entities = json.load(f)
            for e in entities:
                items.append({
                    "id": f"entity:{e.get('name', '').lower().replace(' ', '-')}",
                    "kind": "entity",
                    "title": e.get("name"),
                    "subtitle": f"{e.get('type', 'Figure')} • {e.get('topic', 'General')}",
                    "tags": [e.get("type", "General"), e.get("topic", "General")],
                    "route": {"page": "graph.html", "params": {"focus": f"entity:{e.get('name', '').lower().replace(' ', '-')}"}}
                })

    # 4. Commands (Static Routes)
    commands = [
        {"id": "cmd:lib", "title": "Go: Library", "subtitle": "Document Catalog", "route": {"page": "library.html"}},
        {"id": "cmd:dict", "title": "Go: Dictionary", "subtitle": "Esoteric Lexicon", "route": {"page": "dictionary.html"}},
        {"id": "cmd:herm", "title": "Go: Hermetic", "subtitle": "Lineage Gallery", "route": {"page": "hermetic.html"}},
        {"id": "cmd:alc", "title": "Go: Alchemy", "subtitle": "The Opus Workbench", "route": {"page": "alchemy.html"}},
        {"id": "cmd:graph", "title": "Go: Graph", "subtitle": "Knowledge Network", "route": {"page": "graph.html"}},
        {"id": "cmd:ins", "title": "Go: Insights", "subtitle": "Project Metrics", "route": {"page": "insights.html"}},
        {"id": "cmd:ref", "title": "Go: Reference", "subtitle": "Scholarship Portal", "route": {"page": "reference.html"}}
    ]
    for c in commands:
        items.append({
            "id": c["id"],
            "kind": "command",
            "title": c["title"],
            "subtitle": c["subtitle"],
            "tags": ["Navigation"],
            "route": c["route"]
        })

    omni_index = {
        "version": "v9.1",
        "generated_at": datetime.now().isoformat(),
        "items": items
    }
    
    output_path = os.path.join(SNAPSHOT_DIR, "omni_index.json")
    with open(output_path, "w") as f:
        json.dump(omni_index, f, indent=2)
        
    print(f"Omni Index built: {len(items)} items indexed at {output_path}")

if __name__ == "__main__":
    build_index()
