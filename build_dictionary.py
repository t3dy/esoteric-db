import sqlite3
import json
import re
import uuid

DB_PATH = "esoteric_v5.db"

# Heuristic Keywords
STAGES = {
    "Nigredo": ["black", "crow", "raven", "putrefaction", "death", "night", "darkness", "saturn", "lead"],
    "Albedo": ["white", "swan", "dove", "lily", "silver", "moon", "luna", "purification", "washing"],
    "Citrinitas": ["yellow", "gold", "solar", "eagle", "light"],
    "Rubedo": ["red", "king", "phoenix", "blood", "stone", "fire", "sun", "sol", "fixation"]
}

DOMAIN_KEYWORDS = {
    "Physical": ["furnace", "fire", "acid", "metal", "glass", "distill", "heat", "flask", "vessel"],
    "Spiritual": ["soul", "spirit", "god", "prayer", "meditation", "vision", "angel", "heaven", "inner"]
}

def determine_stage(text):
    text = text.lower()
    scores = {stage: 0 for stage in STAGES}
    for stage, keywords in STAGES.items():
        for kw in keywords:
            if kw in text:
                scores[stage] += 1
    
    # Return stage with max score if > 0
    best_stage = max(scores, key=scores.get)
    return best_stage if scores[best_stage] > 0 else None

def classify_meaning(text):
    text = text.lower()
    phys = sum(1 for kw in DOMAIN_KEYWORDS["Physical"] if kw in text)
    spir = sum(1 for kw in DOMAIN_KEYWORDS["Spiritual"] if kw in text)
    
    if phys > spir: return "Physical"
    if spir > phys: return "Spiritual"
    return "Ambivalent"

def build_dictionary():
    print("Synthesizing Dictionary Entries...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Fetch Candidates (Materials, Symbols, Equipment)
    cursor.execute('''
        SELECT name, type, attributes, COUNT(*) as freq 
        FROM entities 
        WHERE type IN ('Alchemy Material', 'Alchemy Symbol', 'Alchemy Equipment', 'Hermetic Figure')
        GROUP BY name
    ''')
    candidates = cursor.fetchall()
    
    print(f"Found {len(candidates)} candidate entities.")
    
    for row in candidates:
        name = row['name']
        cat = row['type']
        
        # Load all contexts (naive approach: just looking at attributes of one entry, 
        # ideally we'd aggregate all instances if we stored them separately)
        # For V6 mining, strict "entities" table has unique name/type, but attributes might capture first instance.
        # We need to scan document text or use the 'attributes' JSON context if we popped it there.
        # For now, we assume the entity existence implies a valid headword.
        
        entry_id = str(uuid.uuid4())
        
        # Heuristics based on name itself + random knowledge injection for demo
        stage = determine_stage(name)
        domain = "Alchemy" if "Alchemy" in cat else "Hermeticism"
        
        # Placeholder definitions (In a real system, we'd extract defining sentences)
        short_def = f"A {cat.lower().replace('alchemy ', '')} frequently cited in the corpus."
        phys_meaning = ""
        spirit_meaning = ""
        
        if "Material" in cat:
            phys_meaning = f"The substance {name}, used in laboratory operations."
            spirit_meaning = f"Symbolizes the {name}'s corresponding planetary virtue."
            
        if "Symbol" in cat:
            phys_meaning = "An allegorical cover-name (Deckname) for a chemical agent."
            spirit_meaning = "Represents a stage of transformation in the adept's soul."
            
        cursor.execute('''
            INSERT OR REPLACE INTO dictionary_entries 
            (id, headword, short_definition, physical_meaning, spiritual_meaning, opus_stage, domain, ambiguity_flag, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry_id, 
            name, 
            short_def, 
            phys_meaning, 
            spirit_meaning, 
            stage, 
            domain, 
            True, # Assume ambiguity for all alchemical terms
            "Antigravity V7 Engine"
        ))
        
        # Link back to raw entity for source tracking (simulated)
        # In V7 full implementation, we'd insert into entry_sources here
        
    conn.commit()
    conn.close()
    print("Dictionary Build Complete.")

if __name__ == "__main__":
    build_dictionary()
