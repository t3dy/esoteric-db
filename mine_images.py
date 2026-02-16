import os
import fitz  # PyMuPDF
import sqlite3
import hashlib
import json

DB_NAME = "esoteric.db"
OUTPUT_DIR = "docs/vault"
MIN_WIDTH = 50
MIN_HEIGHT = 50

def mine_images(db_path, root_dir):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all documents
    cursor.execute("SELECT id, path, topic FROM documents")
    docs = cursor.fetchall()
    
    image_count = 0
    
    for doc_id, doc_path, topic in docs:
        if not os.path.exists(doc_path):
            continue
            
        print(f"Mining images from: {os.path.basename(doc_path)}...")
        try:
            doc = fitz.open(doc_path)
            for page_index in range(len(doc)):
                page = doc[page_index]
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    ext = base_image["ext"]
                    
                    # Basic size filter to avoid icons/UI elements
                    if base_image["width"] < MIN_WIDTH or base_image["height"] < MIN_HEIGHT:
                        continue
                        
                    img_hash = hashlib.sha256(image_bytes).hexdigest()
                    img_id = img_hash[:16]
                    img_filename = f"{img_id}.{ext}"
                    img_save_path = os.path.join(OUTPUT_DIR, img_filename)
                    
                    # Save to vault
                    if not os.path.exists(img_save_path):
                        with open(img_save_path, "wb") as f:
                            f.write(image_bytes)
                    
                    # Link in database
                    cursor.execute('''
                        INSERT OR REPLACE INTO images (id, doc_id, page_number, path, sha256, domain)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (img_id, doc_id, page_index + 1, f"vault/{img_filename}", img_hash, topic))
                    
                    image_count += 1
                    
            doc.close()
        except Exception as e:
            # print(f"  Error mining {doc_path}: {e}")
            continue
            
    conn.commit()
    conn.close()
    print(f"Mining complete. Extracted {image_count} images.")

if __name__ == "__main__":
    mine_images(DB_NAME, ".")
