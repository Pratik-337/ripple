import faiss
import numpy as np

class VectorIndex:
    def __init__(self, dim):
        # Inner Product index (Cosine similarity on normalized vectors)
        self.index = faiss.IndexFlatIP(dim)
        self.metadata = []

    def add(self, embedding, meta):
        self.index.add(np.array([embedding]).astype("float32"))
        self.metadata.append(meta)

    def search(self, embedding, k=5):
        # D here will be the Cosine Similarity scores
        D, I = self.index.search(
            np.array([embedding]).astype("float32"),
            k
        )
        return [(self.metadata[i], float(D[0][pos])) for pos, i in enumerate(I[0])]
