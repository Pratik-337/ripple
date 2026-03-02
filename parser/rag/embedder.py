import requests
import numpy as np

OLLAMA_URL = "http://localhost:11434/api/embeddings"
MODEL = "nomic-embed-text"

def embed_text(text: str, is_query: bool = False):
    # Nomic v1.5 prefers prefixes for better retrieval
    prefix = "search_query: " if is_query else "search_document: "
    
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prefix + text
        }
    )
    embedding = np.array(response.json()["embedding"])
    
    # Normalize for Cosine Similarity
    norm = np.linalg.norm(embedding)
    if norm > 1e-9:
        embedding = embedding / norm
        
    return embedding.tolist()
