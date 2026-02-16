import sqlite3
import json
import os

def ingest_lessons(db_path):
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    lessons = []
    
    # 1-20: Database Design & Architecture
    for i in range(1, 21):
        lessons.append({
            "name": f"Lesson {i:03}: DB Arch - {['Schema Evolution', 'Journal Mode', 'MD5 Hashing', 'Atomic Ingestion', 'FTS5 Indexing', 'Relation Mapping', 'Provenance', 'Constraint Logic', 'Normalization', 'JSON Blobs', 'WAL Locks', 'Query Performance', 'Data Integrity', 'Backup Loops', 'Migration Scripts', 'Audit Trails', 'Concurrency', 'Type Consistency', 'Entity Dedup', 'Master IDs'][i-1]}",
            "type": "Lesson",
            "attributes": {
                "Category": "Database & Architecture",
                "Insight": f"Deep architectural lesson {i} regarding database stability and scholarly data integrity.",
                "Designer": "Branch Manager"
            }
        })

    # 21-40: Interface Design
    for i in range(21, 41):
        lessons.append({
            "name": f"Lesson {i:03}: UI/UX - {['Mansion Metaphor', 'Room Isolation', 'Ambient Glow', 'Side Navigation', 'Responsive Grids', 'Visual Hierarchy', 'Typography Vibe', 'Micro-interactions', 'Alpine.js Scoping', 'Loading States', 'Empty State UI', 'Error Recovery', 'Context Drawers', 'OmniSearch Access', 'Breadcrumb Paths', 'Aesthetic Polish', 'Dark Mode HSL', 'Interactive Charts', 'Map Projection', 'Component Reusability'][i-21]}",
            "type": "Lesson",
            "attributes": {
                "Category": "Interface & UX",
                "Insight": f"Design lesson {i} on creating a premium, room-based mansion experience.",
                "Designer": "Interface Designer"
            }
        })

    # 41-60: Feature Engineering for Relational Browsing
    for i in range(41, 61):
        lessons.append({
            "name": f"Lesson {i:03}: Relational - {['The Golden Chain', 'Cross-Tradition', 'Mention Counts', 'Citation Loops', 'Entity Linking', 'Topic Clustering', 'Author Profiles', 'Text Lineages', 'Epoch Mapping', 'Symbolic Frequencies', 'Scholarly Haunting', 'Metabolic Summaries', 'OmniIndex Building', 'Recommendation Engine', 'Graph Connectivity', 'Edge Weighting', 'Node Centrality', 'Context Persistence', 'Strategy Classifier', 'Inquiry Mapping'][i-41]}",
            "type": "Lesson",
            "attributes": {
                "Category": "Relational Browsing",
                "Insight": f"Feature lesson {i} on building deep connectivity between disparate scholarly entities.",
                "Designer": "Narrative Designer"
            }
        })

    # 61-80: Digital Humanities Goals
    for i in range(61, 81):
        lessons.append({
            "name": f"Lesson {i:03}: DH Strategy - {['Silences in Data', 'Historiography', 'Ancestry of Ideas', 'Thematic Clusters', 'Primary Sources', 'Scholarship Drift', 'Archive Access', 'Digital Philology', 'Context Engineering', 'Dataset Narrative', 'Reflexive Research', 'Open Scholarship', 'Curation Loops', 'Evidence Mining', 'Textual Criticism', 'Hermeneutics', 'Symbolic Reading', 'Legacy Preservation', 'Knowledge Graphs', 'Narrative Integrity'][i-61]}",
            "type": "Lesson",
            "attributes": {
                "Category": "Digital Humanities",
                "Insight": f"DH lesson {i} on fulfilling the scholarly mission of the mansion.",
                "Designer": "Narrative Designer"
            }
        })

    # 81-100: PDF Library & Generative Uses
    for i in range(81, 101):
        lessons.append({
            "name": f"Lesson {i:03}: Future-Proof - {['PDF Metadata Mining', 'Generative Plugs', 'LLM Context', 'Prompt Stability', 'API Readiness', 'Markdown Export', 'JSON Scalability', 'Version Control', 'Snippet Retrieval', 'Page-Level Linking', 'OCR Robustness', 'Entity Extraction', 'Sentiment Analysis', 'Cross-Platform', 'Mobile Access', 'Search Analytics', 'User Profiling', 'Task Velocity', 'Feature Glows', 'Branch Management'][i-81]}",
            "type": "Lesson",
            "attributes": {
                "Category": "Library & Generative",
                "Insight": f"Generative lesson {i} on preparing the database for advanced AI and research integration.",
                "Designer": "Branch Manager"
            }
        })

    print(f"Ingesting {len(lessons)} lessons...")
    for l in lessons:
        cursor.execute('''
            INSERT INTO entities (name, type, attributes)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                type=excluded.type,
                attributes=excluded.attributes
        ''', (l['name'], l['type'], json.dumps(l['attributes'])))

    conn.commit()
    conn.close()
    print("Ingestion complete.")

if __name__ == "__main__":
    ingest_lessons("esoteric.db")
