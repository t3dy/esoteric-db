import sqlite3
import json
import csv
import os

DB_NAME = "esoteric.db"
OUTPUT_FILE = "reports/metadata_richness_report.csv"

def calculate_grade(item, category):
    score = 0
    missing = []
    
    # Base Existence
    if item.get('name') or item.get('title') or item.get('filename'):
        score += 10
    else:
        missing.append("Name/Title")

    # Type/Topic
    if item.get('type') or item.get('topic'):
        score += 10
    else:
        missing.append("Type/Topic")

    # Period/Time
    # Some items might have it in attributes
    attrs = {}
    if item.get('attributes'):
        try:
            attrs = json.loads(item['attributes'])
        except:
            pass
            
    if item.get('period') or attrs.get('period') or item.get('year'):
        score += 20
    else:
        missing.append("Period")

    # Summary/Description
    summary = item.get('summary') or item.get('description') or attrs.get('description')
    if summary and len(str(summary)) > 50:
        score += 20
    elif summary:
        score += 10 # Partial points for short summary
    else:
        missing.append("Summary")

    # Rich Attributes
    if attrs and len(attrs.keys()) > 1:
        score += 20
    elif item.get('attributes'):
        score += 5
    else:
        missing.append("Attributes")

    # Specifics
    if category == 'Document':
        if item.get('author'):
            score += 20
        else:
            missing.append("Author")
    elif category == 'Entity':
        # Entities get points for having specific domain fields
        if attrs.get('domain') or attrs.get('category'):
            score += 20
        else:
            missing.append("Domain")

    # Grading Scale
    if score >= 90: grade = 'A (Rich)'
    elif score >= 80: grade = 'B (Good)'
    elif score >= 60: grade = 'C (Passable)'
    elif score >= 40: grade = 'D (Thin)'
    else: grade = 'F (Skeleton)'

    return score, grade, ", ".join(missing)

def audit():
    if not os.path.exists(DB_NAME):
        print(f"Error: Database {DB_NAME} not found.")
        return

    os.makedirs('reports', exist_ok=True)

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    results = []

    # 1. Scan Documents
    cursor.execute("SELECT * FROM documents")
    docs = cursor.fetchall()
    for d in docs:
        item = dict(d)
        score, grade, missing = calculate_grade(item, 'Document')
        results.append({
            'ID': f"DOC-{item['id']}",
            'Name': item.get('title') or item.get('filename'),
            'Category': 'Document',
            'Type': item.get('topic'),
            'Score': score,
            'Grade': grade,
            'Missing_Fields': missing
        })

    # 2. Scan Entities
    cursor.execute("SELECT * FROM entities")
    ents = cursor.fetchall()
    for e in ents:
        item = dict(e)
        score, grade, missing = calculate_grade(item, 'Entity')
        results.append({
            'ID': f"ENT-{item['id']}",
            'Name': item['name'],
            'Category': 'Entity',
            'Type': item.get('type'),
            'Score': score,
            'Grade': grade,
            'Missing_Fields': missing
        })

    # Sort by Score (Ascending) so we see the worst first
    results.sort(key=lambda x: x['Score'])

    # Export to CSV
    keys = ['ID', 'Name', 'Category', 'Type', 'Grade', 'Score', 'Missing_Fields']
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)

    print(f"Audit complete. Scanned {len(results)} items. Report saved to {OUTPUT_FILE}")
    conn.close()

if __name__ == "__main__":
    audit()
