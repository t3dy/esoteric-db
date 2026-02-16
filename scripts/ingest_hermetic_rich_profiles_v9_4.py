import sqlite3
import json
import os

def ingest_rich_profiles(db_path):
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    entities = [
        # --- I. HISTORICAL TEXTS (The Abstract Works) ---
        {"name": "Corpus Hermeticum", "type": "Text", "attributes": {"Origin": "2nd-3rd c CE", "Language": "Greek", "Themes": "Soteriology, Cosmology, Gnosis"}},
        {"name": "CH I - Poimandres", "type": "Text", "attributes": {"Origin": "2nd-3rd c CE", "Themes": "Creation, Nous, Anthropogenesis"}},
        {"name": "CH II - To Asclepius", "type": "Text", "attributes": {"Themes": "God as Circle, Transcendence"}},
        {"name": "CH III - Sacred Discourse", "type": "Text", "attributes": {"Themes": "Cosmic Order"}},
        {"name": "CH IV - The Mixing Bowl", "type": "Text", "attributes": {"Themes": "Intellect, Baptism"}},
        {"name": "CH V - God is Invisible", "type": "Text", "attributes": {"Themes": "Immanence, Manifestation"}},
        {"name": "CH VI - In God Alone is Good", "type": "Text", "attributes": {"Themes": "Goodness, Ontology"}},
        {"name": "CH VII - Ignorance is Evil", "type": "Text", "attributes": {"Themes": "Gnosis, Salvation"}},
        {"name": "CH VIII - No Perishing", "type": "Text", "attributes": {"Themes": "Transformation, Metamorphosis"}},
        {"name": "CH IX - Thought and Sense", "type": "Text", "attributes": {"Themes": "Epistemology, Mind"}},
        {"name": "CH X - The Key", "type": "Text", "attributes": {"Themes": "Metaphysical Unity"}},
        {"name": "CH XI - Mind to Hermes", "type": "Text", "attributes": {"Themes": "Divine Instruction"}},
        {"name": "CH XII - On the Common Mind", "type": "Text", "attributes": {"Themes": "Universal Mind"}},
        {"name": "CH XIII - On Rebirth", "type": "Text", "attributes": {"Themes": "Regeneration, Silence, Initiation"}},
        {"name": "CH XIV - Letter to Asclepius", "type": "Text", "attributes": {"Themes": "Divine Essence"}},
        {"name": "CH XV - Cosmic Unity", "type": "Text", "attributes": {"Themes": "All is One"}},
        {"name": "CH XVI - Definitions to Asclepius", "type": "Text", "attributes": {"Themes": "Theology, Polemic"}},
        {"name": "CH XVII - To Asclepius", "type": "Text", "attributes": {"Themes": "Statues, Presence"}},
        {"name": "CH XVIII - Letter to Ammon", "type": "Text", "attributes": {"Themes": "Kingship, Praise"}},
        {"name": "Asclepius", "type": "Text", "attributes": {"Origin": "Late Antique", "Language": "Latin", "Themes": "Theurgy, Statues, Fatality"}},
        {"name": "Nag Hammadi VI - Ogdoad and Ennead", "type": "Text", "attributes": {"Origin": "4th c CE", "Language": "Coptic", "Themes": "Ascent, Mystery"}},
        {"name": "Liber XXIV philosophorum", "type": "Text", "attributes": {"Origin": "12th c", "Language": "Latin", "Themes": "Apophaticism, 24 Definitions"}},
        {"name": "Picatrix", "type": "Text", "attributes": {"Origin": "11th c", "Language": "Arabic/Latin", "Themes": "Astral Magic, Talismans"}},
        {"name": "De sex rerum principiis", "type": "Text", "attributes": {"Origin": "12th c", "Language": "Latin", "Themes": "Metaphysics"}},
        {"name": "Atalanta Fugiens", "type": "Text", "attributes": {"Origin": "1617", "Author": "Michael Maier", "Themes": "Emblems, Music, Alchemy"}},

        # --- II. FIGURES (Ancient & Renaissance) ---
        {"name": "Hermes Trismegistus", "type": "Figure", "attributes": {"Biography": "Legendary Hellenistic sage, merger of Hermes and Thoth.", "Tradition": "Hermetism"}},
        {"name": "Tat", "type": "Figure", "attributes": {"Biography": "Disciple/Son of Hermes in the dialogues.", "Tradition": "Hermetism"}},
        {"name": "Ammon", "type": "Figure", "attributes": {"Biography": "Royal student of Hermes.", "Tradition": "Hermetism"}},
        {"name": "Marsilio Ficino", "type": "Figure", "attributes": {"Biography": "Renaissance translator of the CH (1463).", "Tradition": "Renaissance Platonism"}},
        {"name": "Giovanni Pico della Mirandola", "type": "Figure", "attributes": {"Biography": "Architect of Christian Cabala.", "Tradition": "Humanism"}},
        {"name": "Lodovico Lazzarelli", "type": "Figure", "attributes": {"Biography": "Hermetic poet, disciple of Correggio.", "Tradition": "Hermetism"}},
        {"name": "Giordano Bruno", "type": "Figure", "attributes": {"Biography": "Infinite universe theorist, Hermetic martyr.", "Tradition": "Hermetic Cosmology"}},
        {"name": "John Dee", "type": "Figure", "attributes": {"Biography": "English polymath, Enochian magician.", "Tradition": "Occult Philosophy"}},
        {"name": "Isaac Newton", "type": "Figure", "attributes": {"Biography": "Natural philosopher with deep alchemical interests.", "Tradition": "Alchemical Natural Philosophy"}},
        {"name": "Paracelsus", "type": "Figure", "attributes": {"Biography": "Reformer of medicine via Iatrochemistry.", "Tradition": "Spagyrics"}},

        # --- III. SCHOLARS (Modern) ---
        {"name": "Jean-Pierre Mahé", "type": "Scholar", "attributes": {"Bio": "French philologist, editor of Coptic Hermetica."}},
        {"name": "André-Jean Festugière", "type": "Scholar", "attributes": {"Bio": "Editor of the Greek CH, focused on philosophical context."}},
        {"name": "Paolo Lucentini", "type": "Scholar", "attributes": {"Bio": "Editor of 'Hermes Latinus', focused on medieval transmission."}},
        {"name": "Garth Fowden", "type": "Scholar", "attributes": {"Bio": "Author of 'The Egyptian Hermes', focused on late antique context."}},
        {"name": "Frances Yates", "type": "Scholar", "attributes": {"Bio": "Pioneer of the 'Hermetic Tradition' in the Renaissance."}}
    ]

    print(f"Infusing {len(entities)} master profiles into esoteric.db...")
    for ent in entities:
        cursor.execute('''
            INSERT INTO entities (name, type, attributes)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                type=excluded.type,
                attributes=excluded.attributes
        ''', (ent['name'], ent['type'], json.dumps(ent['attributes'])))

    conn.commit()
    conn.close()
    print("Infusion complete.")

if __name__ == "__main__":
    ingest_rich_profiles("esoteric.db")
