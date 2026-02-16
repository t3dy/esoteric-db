import json
import os

# ---------------------------------------------------------
# V12: The Similarity Matrix
# ---------------------------------------------------------
# This script builds a graph of "Similar Texts" based on
# metadata overlap (Topic, Period, Author).
# It enables the "Recommended Reading" feature in the UI.
# ---------------------------------------------------------

DOCS_FILE = 'docs/docs.json'
OUTPUT_FILE = 'docs/recommendations.json'

def calculate_score(doc_a, doc_b):
    score = 0
    if doc_a.get('topic') == doc_b.get('topic'): score += 3
    if doc_a.get('period') == doc_b.get('period'): score += 2
    if doc_a.get('author') == doc_b.get('author') and doc_a.get('author') != "Unknown": score += 5
    if doc_a.get('century') == doc_b.get('century'): score += 1
    return score

def main():
    print("🕸 Building Similarity Matrix...")
    
    if not os.path.exists(DOCS_FILE):
        print("❌ docs.json not found.")
        return

    with open(DOCS_FILE, 'r', encoding='utf-8') as f:
        docs = json.load(f)

    # Filter only valid docs (with IDs)
    docs = [d for d in docs if d.get('id')]
    
    matrix = {}
    
    print(f"  Analyzing {len(docs)} documents...")

    for i, doc in enumerate(docs):
        my_id = doc['id']
        candidates = []
        
        for other in docs:
            if other['id'] == my_id: continue
            
            score = calculate_score(doc, other)
            if score > 0:
                candidates.append({
                    "doc_id": other['id'],
                    "title": other.get('title', other.get('filename')),
                    "period": other.get('period'),
                    "score": score
                })
        
        # Sort by score descending
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Keep top 3
        matrix[my_id] = candidates[:3]
        
        if i % 100 == 0:
            print(f"  Processed {i}/{len(docs)}...")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(matrix, f, indent=2)

    print(f"✅ Matrix Complete. Mapped relationships for {len(matrix)} documents.")
    print(f"💾 Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
