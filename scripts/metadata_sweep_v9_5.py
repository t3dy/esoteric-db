import sqlite3
import json
import os

def run_metadata_sweep(db_path):
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("--- [List Watcher] Starting Global Metadata Sweep (V9.5) ---")
    
    # 1. Inspect Entity Schema
    cursor.execute("SELECT id, name, type, attributes FROM entities")
    all_entities = cursor.fetchall()

    metrics = {
        "total": len(all_entities),
        "types": {},
        "thick_count": 0,
        "thin_count": 0,
        "mend_queue": []
    }

    mandatory_fields = {
        "Alchemist": ["Biography", "Contributions", "Tradition"],
        "Figure": ["Biography", "Tradition"],
        "Text": ["Origin", "Themes"],
        "Historical Text": ["Estimated Origin", "Key Themes", "Summary"],
        "Scholar": ["Biography", "Contributions"],
        "Lesson": ["Category", "Insight", "Designer"]
    }

    for eid, name, etype, attrs_raw in all_entities:
        metrics["types"][etype] = metrics["types"].get(etype, 0) + 1
        
        try:
            attrs = json.loads(attrs_raw) if attrs_raw else {}
        except:
            attrs = {}

        # Check richness
        required = mandatory_fields.get(etype, [])
        missing = [f for f in required if f not in attrs or not attrs[f]]
        
        is_thick = len(attrs.keys()) >= 3 and not missing
        
        if is_thick:
            metrics["thick_count"] += 1
        else:
            metrics["thin_count"] += 1
            metrics["mend_queue"].append({
                "id": eid,
                "name": name,
                "type": etype,
                "missing_fields": missing,
                "current_attr_count": len(attrs.keys())
            })

    # Save Mend Queue for UI enrichment portal
    with open("metadata_mend_queue.json", "w") as f:
        json.dump(metrics["mend_queue"], f, indent=4)

    print(f"Sweep Complete.")
    print(f"  Total Entities: {metrics['total']}")
    print(f"  Thick Profiles: {metrics['thick_count']}")
    print(f"  Thin Profiles:  {metrics['thin_count']}")
    print(f"  Mend Queue exported to 'metadata_mend_queue.json'")
    
    conn.close()

if __name__ == "__main__":
    run_metadata_sweep("esoteric.db")
