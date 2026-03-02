from .embedder import embed_text

def retrieve_similar(index, changed_code, k=5):
    # Use the query prefix
    query_vector = embed_text(changed_code, is_query=True)
    results = index.search(query_vector, k=k)

    formatted = []
    for meta, score in results:
        # Score is now direct Cosine Similarity (0.0 to 1.0)
        formatted.append({
            "meta": meta,
            "similarity": float(score)
        })

    return formatted
