import json
import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
SNAPSHOT_DIR = os.path.join(BASE_DIR, "data", "snapshots")

def build_recommendations():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    
    # Load data
    docs_path = os.path.join(DOCS_DIR, "docs.json")
    dict_path = os.path.join(DOCS_DIR, "dictionary.json")
    
    if not os.path.exists(docs_path) or not os.path.exists(dict_path):
        print("Required data files missing.")
        return

    with open(docs_path, "r") as f:
        docs = json.load(f)
    with open(dict_path, "r") as f:
        entries = json.load(f)

    recs = {}

    for entry in entries:
        headword = entry.get("headword", "").lower()
        slug = entry.get("slug") or headword.replace(" ", "-")
        
        # Recommendation 1: Related Docs
        related_docs = []
        for doc in docs:
            title = (doc.get("title") or "").lower()
            topic = (doc.get("topic") or "").lower()
            summary = (doc.get("summary") or "").lower()
            
            if headword in title or headword in topic or headword in summary:
                related_docs.append({
                    "doc_id": doc["id"],
                    "title": doc.get("title") or doc.get("filename"),
                    "reason": "Primary mentions in text" if headword in title else "High thematic density"
                })
        
        # Recommendation 2: Related Entries (Simple sibling logic for now)
        related_entries = [
            {"slug": e.get("slug") or e.get("headword", "").lower().replace(" ", "-"), "headword": e["headword"]}
            for e in entries if e["headword"] != entry["headword"] and e.get("domain") == entry.get("domain")
        ][:3] # Cap at 3 for UI stability

        recs[slug] = {
            "recommended_docs": related_docs[:5], # Cap at 5
            "recommended_entries": related_entries
        }

    output_path = os.path.join(SNAPSHOT_DIR, "recommendations.json")
    with open(output_path, "w") as f:
        json.dump(recs, f, indent=2)
        
    print(f"Recommendations built for {len(recs)} dictionary entries.")

if __name__ == "__main__":
    build_recommendations()
