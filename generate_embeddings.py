import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# === Configuration ===
KB_FOLDER = "kb"  # Folder containing .txt files
MODEL_NAME = "all-MiniLM-L6-v2"

# === Step 1: Read Knowledge Base ===
def read_knowledge_base():
    print("📁 Reading knowledge base...")
    texts = []
    for filename in os.listdir(KB_FOLDER):
        if filename.endswith(".txt"):
            with open(os.path.join(KB_FOLDER, filename), "r", encoding="utf-8") as f:
                content = f.read()
                texts.append(content)
    combined_text = "\n".join(texts)
    print(f"✅ Characters read: {len(combined_text)}")
    return combined_text

# === Step 2: Chunk Text ===
def chunk_text(text, max_tokens=500):
    print("✂️ Chunking text...")
    words = text.split()
    chunks = [" ".join(words[i:i+max_tokens]) for i in range(0, len(words), max_tokens)]
    print(f"📄 Total Chunks: {len(chunks)}")
    return chunks

# === Step 3: Generate Embeddings ===
def generate_embeddings(chunks):
    print(f"🤖 Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    vectors = model.encode(chunks, convert_to_numpy=True, show_progress_bar=True)
    print(f"✅ Generated {len(vectors)} embeddings of dimension {vectors.shape[1]}")
    return vectors

# === Step 4: Save FAISS Index + Metadata ===
def save_faiss_index(vectors, chunks):
    print("💾 Saving FAISS index and metadata...")
    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)

    os.makedirs(KB_FOLDER, exist_ok=True)
    faiss.write_index(index, os.path.join(KB_FOLDER, "faiss_index"))

    with open(os.path.join(KB_FOLDER, "embedding_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved FAISS index to {KB_FOLDER}/faiss_index")
    print(f"✅ Saved metadata to {KB_FOLDER}/embedding_metadata.json")

# === Main ===
if __name__ == "__main__":
    text = read_knowledge_base()
    chunks = chunk_text(text)
    vectors = generate_embeddings(chunks)
    save_faiss_index(vectors, chunks)
