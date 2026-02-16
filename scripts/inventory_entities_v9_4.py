import sqlite3
import json
import os

def inventory_data(db_path):
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    report = {
        "counts": {},
        "top_topics": [],
        "thin_entities": [],
        "rich_entities": []
    }

    # 1. Total Counts
    cursor.execute("SELECT COUNT(*) FROM chats")
    report["counts"]["chats"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM chat_messages")
    report["counts"]["messages"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tables")
    report["counts"]["tables"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT topic) FROM chats")
    report["counts"]["distinct_topics"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM entities")
    report["counts"]["total_entities"] = cursor.fetchone()[0]

    # 2. Top Topics
    cursor.execute("SELECT topic, COUNT(*) as count FROM chats GROUP BY topic ORDER BY count DESC LIMIT 10")
    report["top_topics"] = [{"topic": r[0], "count": r[1]} for r in cursor.fetchall()]

    # 3. Entity Breakdown by Type
    try:
        cursor.execute("SELECT type, COUNT(*) as count FROM entities GROUP BY type")
        report["counts"]["entities_by_type"] = {r[0]: r[1] for r in cursor.fetchall()}
    except Exception as e:
        report["counts"]["entities_by_type"] = f"Error: {e}"

    # 4. Identify "Thin" vs "Rich" Entities
    cursor.execute("SELECT name, type, attributes FROM entities")
    for name, etype, attr_json in cursor.fetchall():
        try:
            attrs = json.loads(attr_json) if attr_json else {}
            # Check for specific rich metadata keys
            rich_keys = ["Biography", "Contributions", "Author", "Period", "Summary"]
            has_rich = any(k in attrs for k in rich_keys)
            
            if has_rich:
                report["rich_entities"].append(name)
            else:
                report["thin_entities"].append(name)
        except:
            report["thin_entities"].append(name)

    # 5. Extract Unique Alchemists/Figures
    report["alchemist_candidates"] = []
    cursor.execute("SELECT name FROM entities WHERE type IN ('Entity', 'Figure', 'Alchemist')")
    report["alchemist_candidates"] = [r[0] for r in cursor.fetchall() if r[0]]

    conn.close()

    # Write report
    report_path = "inventory_report_v9_4.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"Inventory complete. Report saved to {report_path}")
    print(f"Total Chats: {report['counts']['chats']}")
    print(f"Total Messages: {report['counts']['messages']}")
    print(f"Total Tables: {report['counts']['tables']}")
    print(f"Total Entities: {report['counts']['total_entities']}")
    print(f"Thin Entities (Metadata Gaps): {len(report['thin_entities'])}")

if __name__ == "__main__":
    inventory_data("esoteric.db")
