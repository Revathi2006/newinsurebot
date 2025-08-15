import json
import requests
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os

# Load .env variables
load_dotenv()

# Now get the key from environment
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Load embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Load FAISS index and metadata
try:
    faiss_index = faiss.read_index("kb/faiss_index")
    with open("kb/embedding_metadata.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)
except Exception:
    faiss_index = None
    metadata = []

def retrieve_context(query: str, k: int = 3) -> str:
    if not faiss_index or not metadata:
        return ""
    query_vec = embedding_model.encode([query])
    distances, indices = faiss_index.search(np.array(query_vec), k)
    return "\n".join([metadata[idx] for idx in indices[0] if idx < len(metadata)])

def ask_general(prompt: str) -> str:
    context = retrieve_context(prompt)

    if context:
        final_prompt = (
            "Use the following context to answer the user's insurance question.\n\n"
            f"Context:\n{context}\n\nQuestion: {prompt}"
        )
    else:
        final_prompt = prompt

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": "You are a helpful insurance assistant."},
            {"role": "user", "content": final_prompt}
        ]
    }

    try:
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip() or \
               "Sorry, couldn't fetch info."
    except Exception as e:
        return f"Error: {str(e)}"