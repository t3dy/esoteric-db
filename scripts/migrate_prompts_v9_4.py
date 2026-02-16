import sqlite3
import os

def migrate_prompts(db_path):
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Checking prompts table schema...")
    
    # Check current columns
    cursor.execute("PRAGMA table_info(prompts)")
    columns = [c[1] for c in cursor.fetchall()]
    
    needed_columns = {
        "strategy_summary": "TEXT",
        "mentions_scholar_name": "TEXT",
        "mentions_text_name": "TEXT",
        "prompt_topic": "TEXT",
        "prompt_alchemist": "TEXT",
        "prompt_scholar": "TEXT",
        "prompt_text": "TEXT"
    }

    modified = False
    for col, ctype in needed_columns.items():
        if col not in columns:
            print(f"Adding column {col}...")
            cursor.execute(f"ALTER TABLE prompts ADD COLUMN {col} {ctype}")
            modified = True

    if modified:
        conn.commit()
        print("Migration complete.")
    else:
        print("Schema already up to date.")

    conn.close()

if __name__ == "__main__":
    migrate_prompts("esoteric.db")
