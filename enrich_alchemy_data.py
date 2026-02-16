import sqlite3
import json

DB_NAME = "esoteric.db"

ENTITIES = {
    "Alchemy Material": [
        "Mercury", "Sulfur", "Salt", "Antimony", "Vitriol", "Gold", "Silver", "Lead", "Iron", "Copper", "Tin",
        "Quicksilver", "Cinnabar", "Azoth", "Alkahest", "Philosophical Mercury", "Philosophical Sulfur",
        "Aqua Regia", "Aqua Fortis", "Spirit of Wine", "Vinegar", "Sal Ammoniac", "Saltpeter", "Tartar",
        "Orpiment", "Realgar", "Litharge", "Bismuth", "Magnesia", "Kohl", "Common Salt", "Potash"
    ],
    "Alchemist": [
        "Zosimos of Panopolis", "Geber (Jabir ibn Hayyan)", "Rhazes (Al-Razi)", "Albertus Magnus", "Roger Bacon",
        "Nicolas Flamel", "George Ripley", "Thomas Norton", "Paracelsus", "Edward Kelley", "John Dee",
        "Michael Maier", "Robert Fludd", "Heinrich Khunrath", "Jacob Boehme", "Eugenius Philalethes",
        "Ireneus Philalethes", "Basil Valentine", "Johann Isaac Hollandus", "Bernard of Treviso",
        "Arnald of Villanova", "Raymond Lull", "Mary the Jewess", "Kleopatra the Alchemist", "Ostanes",
        "Morienus", "Artephius", "Sendivogius", "Michael Sendivogius", "Alexander Sethon"
    ],
    "Alchemy Text": [
        "Corpus Hermeticum", "Emerald Tablet", "Emerald Table", "Picatrix", "Turba Philosophorum",
        "Splendor Solis", "Atalanta Fugiens", "Rosarium Philosophorum", "Mutus Liber", "Theatrum Chemicum",
        "Bibliotheca Chemica Curiosa", "Chemical Wedding of Christian Rosenkreutz", "Amphitheatrum Sapientiae Aeternae",
        "Secret of Secrets", "Aurora Consurgens", "De Re Metallica", "Triumphal Chariot of Antimony",
        "Twelve Keys of Basil Valentine", "Book of the Holy Trinity", "Donum Dei", "Compound of Alchemy"
    ],
    "Alchemy Symbol": [
        "Ouroboros", "Philosopher's Stone", "Homunculus", "Rebis", "Green Lion", "Red King", "White Queen",
        "Red Dragon", "Black Crow", "Raven", "Peacock's Tail", "Cauda Pavonis", "White Eagle", "Doves of Diana",
        "Serpent", "Toad", "Basilisk", "Philosophical Child", "Hermetic Seal", "Caduceus", "Uroborus",
        "Pelican", "Phoenix"
    ],
    "Alchemy Theory": [
        "Spagyrics", "Iatrochemistry", "Transmutation", "Chrysopoeia", "Panacea", "Universal Solvent",
        "Macrocosm and Microcosm", "Great Work", "Magnum Opus", "Nigredo", "Albedo", "Citrinitas", "Rubedo"
    ],
    "Alchemy Equipment": [
        "Alembic", "Cucurbit", "Athanor", "Retort", "Crucible", "Pelican", "Bain-Marie", "Sand Bath",
        "Reverberatory Furnace", "Cupel", "Beaker", "Phial", "Flask", "Receiver", "Condenser", "Pestle",
        "Mortar", "Bellows"
    ],
    "Allegorical Animal": [
        "Lion", "Eagle", "Serpent", "Dragon", "Crow", "Dove", "Toad", "Salamander", "Whale", "Unicorn",
        "Hart", "Wolf", "Beart", "Stag", "Swan", "Ram"
    ],
    "Alchemy Scholar": [
        "C.G. Jung", "Frances Yates", "Lawrence Principe", "William Newman", "Pamela Smith", "Bruce Moran",
        "Didier Kahn", "Sylvain Matton", "Wouter Hanegraaff", "Antoine Faivre", "Miran Bozovic"
    ]
}

def enrich():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Ensure tables exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            type TEXT,
            attributes TEXT
        )
    """)

    count = 0
    for entity_type, names in ENTITIES.items():
        for name in names:
            attr = json.dumps({"source": "Seed List", "category": entity_type.lower()})
            try:
                cursor.execute("INSERT OR IGNORE INTO entities (name, type, attributes) VALUES (?, ?, ?)", 
                               (name, entity_type, attr))
                if cursor.rowcount > 0:
                    count += 1
            except Exception as e:
                print(f"Error inserting {name}: {e}")

    conn.commit()
    conn.close()
    print(f"Enriched {count} new entities into {DB_NAME}.")

if __name__ == "__main__":
    enrich()
