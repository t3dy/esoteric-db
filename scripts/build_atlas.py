import json
import os
import re

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
SNAPSHOT_DIR = os.path.join(BASE_DIR, "data", "snapshots")

# The Hermetic Atlas (Lat, Lon)
# Focused on the "Mediterranean to Northern Europe" drift
ATLAS = {
    "Alexandria": {"coords": [31.2001, 29.9187], "era": "Antiquity", "region": "Egypt"},
    "Athens": {"coords": [37.9838, 23.7275], "era": "Antiquity", "region": "Greece"},
    "Rome": {"coords": [41.9028, 12.4964], "era": "Antiquity", "region": "Italy"},
    "Florence": {"coords": [43.7696, 11.2558], "era": "Renaissance", "region": "Italy"},
    "Venice": {"coords": [45.4408, 12.3155], "era": "Renaissance", "region": "Italy"},
    "Prague": {"coords": [50.0755, 14.4378], "era": "Renaissance", "region": "Bohemia"},
    "Heidelberg": {"coords": [49.3988, 8.6724], "era": "Renaissance", "region": "Germany"},
    "Amsterdam": {"coords": [52.3676, 4.9041], "era": "Enlightenment", "region": "Netherlands"},
    "London": {"coords": [51.5074, -0.1278], "era": "Enlightenment", "region": "UK"},
    "Paris": {"coords": [48.8566, 2.3522], "era": "Enlightenment", "region": "France"},
    "Constantinople": {"coords": [41.0082, 28.9784], "era": "Medieval", "region": "Turkey"},
    "Baghdad": {"coords": [33.3152, 44.3661], "era": "Medieval", "region": "Iraq"},
    "Toledo": {"coords": [39.8628, -4.0273], "era": "Medieval", "region": "Spain"},
    "Oxford": {"coords": [51.7520, -1.2577], "era": "Enlightenment", "region": "UK"},
    "Basel": {"coords": [47.5596, 7.5886], "era": "Renaissance", "region": "Switzerland"}
}

def build_atlas():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    
    # Load docs
    with open(os.path.join(DOCS_DIR, "docs.json"), "r") as f:
        docs = json.load(f)

    # Initialize Places
    places = {}
    for city, data in ATLAS.items():
        places[city] = {
            "name": city,
            "coords": data["coords"],
            "era": data["era"],
            "region": data["region"],
            "mentions": 0,
            "associated_docs": [],
            "score": 0
        }

    # Scan Corpus
    print(f"Scanning {len(docs)} documents for geographical mentions...")
    for doc in docs:
        text_dump = ((doc.get("title") or "") + " " + (doc.get("topic") or "") + " " + (doc.get("summary") or "")).lower()
        
        for city in ATLAS.keys():
            if city.lower() in text_dump:
                places[city]["mentions"] += 1
                places[city]["associated_docs"].append({
                    "id": doc["id"],
                    "title": doc.get("title") or doc.get("filename"),
                    "year": doc.get("year")
                })

    # Calculate "Spirit Level" (Score)
    features = []
    for city, data in places.items():
        # Base score of 10 for key cities, plus mentions
        data["score"] = 10 + (data["mentions"] * 5)
        
        # GeoJSON Feature
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [data["coords"][1], data["coords"][0]] # GeoJSON is Lon, Lat
            },
            "properties": {
                "name": city,
                "era": data["era"],
                "score": data["score"],
                "mentions": data["mentions"],
                "region": data["region"],
                "docs": data["associated_docs"][:5] # Top 5 docs
            }
        })

    # Output GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    output_path = os.path.join(DOCS_DIR, "places.json")
    with open(output_path, "w") as f:
        json.dump(geojson, f, indent=2)
        
    print(f"Atlas built. Mapped {len(features)} esoteric centers to {output_path}.")

if __name__ == "__main__":
    build_atlas()
