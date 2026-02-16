import json
import random
import os

# ---------------------------------------------------------
# V11: The "Lineage Network" Simulator
# ---------------------------------------------------------
# This script simulates a "Network Analysis" agent that has
# read the entire corpus and mapped the "Golden Chain".
# ---------------------------------------------------------

OUTPUT_FILE = 'docs/hermetic_lineage.json'

# THE GOLDEN CHAIN KNOWLEDGE BASE
# -------------------------------
ERAS = [
    {"label": "Prisca Theologia", "range": "-3000 to 0", "theme": ["Wisdom", "Egypt", "Origins"]},
    {"label": "Late Antiquity", "range": "100 to 500", "theme": ["Gnosis", "Alexandria", "Theurgy"]},
    {"label": "Medieval", "range": "500 to 1400", "theme": ["Alchemy", "Arabia", "Preservation"]},
    {"label": "Renaissance", "range": "1400 to 1600", "theme": ["Rebirth", "Florence", "Magic"]},
    {"label": "Enlightenment", "range": "1600 to 1800", "theme": ["Rosicrucian", "Science", "Masonry"]},
    {"label": "Modern", "range": "1800 to Present", "theme": ["Occult Revival", "Psychology", "Technology"]}
]

NODES = [
    # ANTIQUITY
    {"id": "Thoth", "label": "Thoth", "period": "Prisca Theologia", "quote": "The lips of wisdom are closed, except to the ears of Understanding."},
    {"id": "Hermes", "label": "Hermes Trismegistus", "period": "Late Antiquity", "quote": "As above, so below."},
    {"id": "Plato", "label": "Plato", "period": "Antiquity", "quote": "Time is the moving image of eternity."},
    {"id": "Plotinus", "label": "Plotinus", "period": "Late Antiquity", "quote": "Withdraw into yourself and look."},
    {"id": "Iamblichus", "label": "Iamblichus", "period": "Late Antiquity", "quote": "Theurgy is the signature of the gods."},
    {"id": "Zosimos", "label": "Zosimos of Panopolis", "period": "Late Antiquity", "quote": "The composition of waters."},
    
    # MEDIEVAL
    {"id": "Jabir", "label": "Jabir ibn Hayyan", "period": "Medieval", "quote": "He who has not studied has not reached the goal."},
    {"id": "Avicenna", "label": "Ibn Sina", "period": "Medieval", "quote": "The knowledge of anything, since all things have causes, is not acquired or complete unless it is known by its causes."},
    {"id": "Albertus", "label": "Albertus Magnus", "period": "Medieval", "quote": "Experiment is the only safe guide in such investigations."},
    {"id": "RogerBacon", "label": "Roger Bacon", "period": "Medieval", "quote": "For the things of this world cannot be made known without a knowledge of mathematics."},
    
    # RENAISSANCE
    {"id": "Ficino", "label": "Marsilio Ficino", "period": "Renaissance", "quote": "Love is the knot and link of the world."},
    {"id": "Pico", "label": "Giovanni Pico della Mirandola", "period": "Renaissance", "quote": "I have read in the records of the Arabians..."},
    {"id": "Agrippa", "label": "Heinrich Cornelius Agrippa", "period": "Renaissance", "quote": "All things in the world are connected."},
    {"id": "Paracelsus", "label": "Paracelsus", "period": "Renaissance", "quote": "The dose makes the poison."},
    {"id": "Bruno", "label": "Giordano Bruno", "period": "Renaissance", "quote": "The universe is infinite."},
    {"id": "Dee", "label": "John Dee", "period": "Renaissance", "quote": "The visible world is created by the invisible."},
    {"id": "Khunrath", "label": "Heinrich Khunrath", "period": "Renaissance", "quote": "What good is a torch specifically for the blind?"},
    
    # ENLIGHTENMENT / ROSICRUCIAN
    {"id": "Maier", "label": "Michael Maier", "period": "Enlightenment", "quote": "Like a Phoenix from the ashes."},
    {"id": "Fludd", "label": "Robert Fludd", "period": "Enlightenment", "quote": "The macrocosm and the microcosm are one."},
    {"id": "Boehme", "label": "Jakob Boehme", "period": "Enlightenment", "quote": "In the water lives the fish, in the fire the salamander."},
    {"id": "Newton", "label": "Isaac Newton", "period": "Enlightenment", "quote": "Truth is the offspring of silence and meditation."},
    {"id": "Vaughan", "label": "Thomas Vaughan", "period": "Enlightenment", "quote": "Magic is nothing but the wisdom of the Creator revealed and planted in the creature."},
    
    # MODERN
    {"id": "Levi", "label": "Eliphas Levi", "period": "Modern", "quote": "To know, to dare, to will, to keep silent."},
    {"id": "Jung", "label": "Carl Jung", "period": "Modern", "quote": "Who looks outside, dreams; who looks inside, awakes."}
]

EDGES = [
    # Transmission Lines
    {"source": "Thoth", "target": "Hermes", "type": "Mythic Origin"},
    {"source": "Hermes", "target": "Plato", "type": "Inspiration"},
    {"source": "Plato", "target": "Plotinus", "type": "Neoplatonism"},
    {"source": "Plotinus", "target": "Iamblichus", "type": "Theurgy"},
    {"source": "Hermes", "target": "Zosimos", "type": "Alchemy"},
    
    {"source": "Zosimos", "target": "Jabir", "type": "Transmission"},
    {"source": "Jabir", "target": "Avicenna", "type": "Science"},
    {"source": "Avicenna", "target": "Albertus", "type": "Translation"},
    
    {"source": "Plato", "target": "Ficino", "type": "Translation"},
    {"source": "Hermes", "target": "Ficino", "type": "Corpus Hermeticum"},
    {"source": "Ficino", "target": "Pico", "type": "Teaching"},
    {"source": "Ficino", "target": "Agrippa", "type": "Influence"},
    {"source": "Ficino", "target": "Paracelsus", "type": "Reaction"},
    
    {"source": "Agrippa", "target": "Dee", "type": "Occult Philosophy"},
    {"source": "Paracelsus", "target": "Khunrath", "type": "Spagyrics"},
    {"source": "Dee", "target": "Fludd", "type": "Mathematics"},
    {"source": "Paracelsus", "target": "Boehme", "type": "Mysticism"},
    {"source": "Khunrath", "target": "Maier", "type": "Rosicrucianism"},
    {"source": "Maier", "target": "Newton", "type": "Alchemy"},
    {"source": "Boehme", "target": "Newton", "type": "Theology"},
    
    {"source": "Agrippa", "target": "Levi", "type": "Revival"},
    {"source": "Paracelsus", "target": "Jung", "type": "Psychology"}
]

def main():
    print("🕸 Weaving the Golden Chain...")
    
    # 1. Format Nodes
    final_nodes = []
    for n in NODES:
        final_nodes.append({
            "id": n["id"],
            "label": n["label"],
            "period": n["period"],
            "attributes": json.dumps({
               "quote": n["quote"],
               "role": "Magus"
            })
        })
        
    # 2. Format Edges
    final_edges = []
    for e in EDGES:
        final_edges.append({
            "source": e["source"],
            "target": e["target"],
            "label": e["type"]
        })

    data = {
        "metadata": {"version": "V11", "generator": "mine_lineage.py"},
        "epochs": [], # Dashboard handles static epoch list, or we can enrich here
        "nodes": final_nodes,
        "edges": final_edges
    }
    
    # Add rich epoch data for the banner
    for e in ERAS:
        data["epochs"].append({
            "label": e["label"],
            "range": e["range"],
            "themes": e["theme"],
            "banner": f"The era of {e['label']} saw the rise of {e['theme'][0]} and the preservation of the Tradition through {e['theme'][2]}."
        })

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
    print(f"✅ Mapped {len(final_nodes)} Magi and {len(final_edges)} Transmissions.")
    print(f"💾 Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
