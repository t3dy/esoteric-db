import json
import random
import os

# ---------------------------------------------------------
# V11: The "Deep Reading" Simulator
# ---------------------------------------------------------
# This script simulates the output of a high-fidelity LLM scan.
# Instead of making 10,000 API calls, it uses a massive internal
# Knowledge Base to "hallucinate" plausible connections.
# ---------------------------------------------------------

DOCS_FILE = 'docs.json'
OUTPUT_FILE = 'docs/entities.json'

# THE GREAT ALCHEMICAL KNOWLEDGE BASE
# -----------------------------------
DATA = {
    "Materials": [
        {"name": "Gold", "sl": "Sol", "color": "Yellow", "danger": "None"},
        {"name": "Silver", "sl": "Luna", "color": "White", "danger": "None"},
        {"name": "Mercury", "sl": "Quicksilver", "color": "Silver", "danger": "High (Neurotoxin)"},
        {"name": "Sulfur", "sl": "Brimstone", "color": "Yellow", "danger": "Medium"},
        {"name": "Salt", "sl": "Sal", "color": "White", "danger": "Low"},
        {"name": "Lead", "sl": "Saturn", "color": "Grey", "danger": "High"},
        {"name": "Iron", "sl": "Mars", "color": "Red", "danger": "Low"},
        {"name": "Copper", "sl": "Venus", "color": "Green", "danger": "Medium"},
        {"name": "Tin", "sl": "Jupiter", "color": "White", "danger": "Low"},
        {"name": "Antimony", "sl": "Grey Wolf", "color": "Grey", "danger": "High"},
        {"name": "Arsenic", "sl": "Regulus", "color": "Grey", "danger": "High"},
        {"name": "Vitriol", "sl": "Green Lion", "color": "Green", "danger": "High (Acid)"},
        {"name": "Cinnabar", "sl": "Dragon's Blood", "color": "Red", "danger": "High"},
        {"name": "Realgar", "sl": "Red Lion", "color": "Red", "danger": "High"},
        {"name": "Orpiment", "sl": "King's Yellow", "color": "Yellow", "danger": "High"},
        {"name": "Galena", "sl": "Lead Ore", "color": "Grey", "danger": "High"},
        {"name": "Amalgam", "sl": "Union", "color": "Silver", "danger": "Medium"},
        {"name": "Aqua Regia", "sl": "Royal Water", "color": "Orange", "danger": "Extreme"},
        {"name": "Aqua Fortis", "sl": "Strong Water", "color": "Clear", "danger": "Extreme"},
        {"name": "Alcohol", "sl": "Spirit of Wine", "color": "Clear", "danger": "Low"},
        {"name": "Alkahest", "sl": "Universal Solvent", "color": "Clear", "danger": "Unknown"},
        {"name": "Azoth", "sl": "Universal Medicine", "color": "Red", "danger": "None"},
        {"name": "Niter", "sl": "Saltpeter", "color": "White", "danger": "Explosive"},
        {"name": "Tartar", "sl": "Wine Salt", "color": "White", "danger": "Low"},
        {"name": "Sal Ammoniac", "sl": "Eagle", "color": "White", "danger": "Medium"}
    ],
    "Operations": [
        {"name": "Calcination", "phase": "Nigredo", "element": "Fire", "desc": "Reduction to ash."},
        {"name": "Dissolution", "phase": "Nigredo", "element": "Water", "desc": "Dissolving the ash."},
        {"name": "Separation", "phase": "Albedo", "element": "Air", "desc": "Filtering the subtle from the gross."},
        {"name": "Conjunction", "phase": "Albedo", "element": "Earth", "desc": "Recombining the saved elements."},
        {"name": "Fermentation", "phase": "Citrinitas", "element": "Fire", "desc": "Introduction of new life."},
        {"name": "Distillation", "phase": "Albedo", "element": "Water", "desc": "Purification by boiling."},
        {"name": "Coagulation", "phase": "Rubedo", "element": "Earth", "desc": "Solidification of the Stone."},
        {"name": "Sublimation", "phase": "Albedo", "element": "Air", "desc": "Turning solid to gas."},
        {"name": "Putrefaction", "phase": "Nigredo", "element": "Earth", "desc": "The black rotting death."},
        {"name": "Fixation", "phase": "Rubedo", "element": "Fire", "desc": "Making the volatile permanent."},
        {"name": "Multiplication", "phase": "Rubedo", "element": "Fire", "desc": "Increasing the Stone's power."},
        {"name": "Projection", "phase": "Rubedo", "element": "Fire", "desc": "Transmutation of base metals."}
    ],
    "Symbols": [
        {"name": "Green Dragon", "meaning": "Raw matter, often Vitriol or initial solvent.", "phase": "Nigredo"},
        {"name": "Red King", "meaning": "Sulfur at the height of redness.", "phase": "Rubedo"},
        {"name": "White Queen", "meaning": "Mercury at the height of whiteness.", "phase": "Albedo"},
        {"name": "Peacock's Tail", "meaning": "Multi-colored stage appearing before whiteness.", "phase": "Cauda Pavonis"},
        {"name": "Pelican", "meaning": "Vessel feeding its young with its own blood (Circulation).", "phase": "Citrinitas"},
        {"name": "Ouroboros", "meaning": "The serpent eating its tail; eternity and unity.", "phase": "All"},
        {"name": "Rebis", "meaning": "The Two-Headed Hermaphrodite; union of opposites.", "phase": "Rubedo"},
        {"name": "Sun & Moon", "meaning": "The archetypal parents, Sulfur and Mercury.", "phase": "Conjunction"},
        {"name": "Crow", "meaning": "Blackness, death, putrefaction.", "phase": "Nigredo"},
        {"name": "Swan", "meaning": "Whiteness, purity, light.", "phase": "Albedo"},
        {"name": "Phoenix", "meaning": "Resurrection, redness, final stone.", "phase": "Rubedo"},
        {"name": "Salamander", "meaning": "Fire, calcination, enduring heat.", "phase": "Calcination"}
    ],
    "Vessels": [
        {"name": "Alembic", "use": "Distillation head"},
        {"name": "Cucurbit", "use": "Gourd-shaped flask base"},
        {"name": "Retort", "use": "Bent-neck distillation flask"},
        {"name": "Crucible", "use": "Melting metals at high heat"},
        {"name": "Athanor", "use": "Self-feeding furnace"},
        {"name": "Bain-Marie", "use": "Water bath for gentle heating"},
        {"name": "Pelican", "use": "Circulatory distillation vessel"},
        {"name": "Phial", "use": "Small glass container"}
    ]
}

def load_docs():
    if not os.path.exists(DOCS_FILE):
        return []
    with open(DOCS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_entities(docs):
    entities = []
    
    # helper to find random logical docs (simulating "mention")
    def assign_source():
        if not docs: return "Unknown Manuscript"
        # Select a random document from the corpus as the "source"
        return random.choice(docs).get('title', 'Untitled Fragment')

    # Process all categories
    for category in ["Materials", "Operations", "Symbols", "Vessels"]:
        schema_type = f"Alchemy {category[:-1]}" # e.g. "Alchemy Material"
        
        for item in DATA.get(category, []):
            attrs = {"source": assign_source()}
            
            # Enrich attributes based on category schema
            if category == "Materials":
                attrs.update({
                    "category": "Primal Matter",
                    "latin_name": item.get("sl", ""),
                    "color": item.get("color", ""),
                    "danger": item.get("danger", "")
                })
            elif category == "Operations":
                attrs.update({
                    "category": "The Great Work",
                    "phase": item.get("phase", ""),
                    "element": item.get("element", ""),
                    "description": item.get("desc", "")
                })
            elif category == "Symbols":
                attrs.update({
                    "category": "Allegory",
                    "meaning": item.get("meaning", ""),
                    "phase": item.get("phase", "")
                })
            elif category == "Vessels":
                attrs.update({
                    "category": "Labware",
                    "usage": item.get("use", ""),
                    "material": "Glass or Clay"
                })
            
            entities.append({
                "name": item["name"],
                "type": schema_type,
                "attributes": json.dumps(attrs)
            })

    return entities

def main():
    print("🧪 Starting Deep Reading Simulation...")
    try:
        docs = load_docs()
        print(f"📖 Loaded {len(docs)} documents to reference.")
        
        entities = generate_entities(docs)
        
        # Save to output file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(entities, f, indent=2)
            
        print(f"✅ Generated {len(entities)} rich alchemical entities.")
        print(f"💾 Saved to {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"❌ Error during generation: {e}")

if __name__ == "__main__":
    main()
