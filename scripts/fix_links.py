import json
import os

# ---------------------------------------------------------
# V11: The Link Fixer
# ---------------------------------------------------------
# Scans docs.json and verifies that every "path" actually
# exists on disk. If not, it tries to find the file or
# marks it as broken (so the UI can disable the button).
# ---------------------------------------------------------

DOCS_FILE = 'docs/docs.json'

def main():
    print("🔧 Starting Link Repair...")
    
    if not os.path.exists(DOCS_FILE):
        print("❌ docs.json not found.")
        return

    with open(DOCS_FILE, 'r', encoding='utf-8') as f:
        docs = json.load(f)

    # 1. Scan Corpus for Real Files
    real_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pdf'):
                real_files.append(os.path.join(root, file))
    
    print(f"📂 Found {len(real_files)} real PDF files on disk.")

    fixed_count = 0
    broken_count = 0

    for doc in docs:
        current_path = doc.get('path', '')
        
        # Check integrity
        if not os.path.exists(current_path):
            # Try to fix
            filename = os.path.basename(current_path)
            # Find in real_files
            match = next((f for f in real_files if os.path.basename(f) == filename), None)
            
            if match:
                doc['path'] = match
                # fixed_count += 1
                # print(f"  Fixed: {filename} -> {match}")
            else:
                doc['path'] = None # Mark as broken/missing
                doc['broken_link'] = True
                broken_count += 1
                # print(f"  Broken: {filename}")
        else:
            # Path is good
            pass

    # Save
    with open(DOCS_FILE, 'w', encoding='utf-8') as f:
        json.dump(docs, f, indent=2)

    print(f"✅ Audit Complete.")
    print(f"  - Verified: {len(docs) - broken_count}")
    print(f"  - Broken: {broken_count} (Links removed to prevent 404s)")

if __name__ == "__main__":
    main()
