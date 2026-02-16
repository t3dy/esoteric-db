import sqlite3

def init_metrics():
    conn = sqlite3.connect('esoteric.db')
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS metrics")
    cursor.execute('''
        CREATE TABLE metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            scholar_interest INTEGER,
            user_curiosity INTEGER,
            gap INTEGER
        )
    ''')
    
    # Seed data based on core themes
    seeds = [
        ("Hermeticism", 85, 92, 7),
        ("Alchemy", 78, 95, 17),
        ("Renaissance Magic", 65, 88, 23),
        ("Neoplatonism", 90, 70, -20),
        ("Rosicrucianism", 55, 82, 27),
        ("Tarot Archetypes", 40, 98, 58),
        ("Cabala", 72, 75, 3),
        ("Gnosticism", 82, 80, -2),
        ("Theurgy", 68, 85, 17),
        ("Astrology", 45, 96, 51)
    ]
    
    for name, si, uc, gap in seeds:
        cursor.execute("INSERT OR IGNORE INTO metrics (name, scholar_interest, user_curiosity, gap) VALUES (?, ?, ?, ?)", (name, si, uc, gap))
    
    conn.commit()
    conn.close()
    print("Metrics table initialized in esoteric.db")

if __name__ == "__main__":
    init_metrics()
