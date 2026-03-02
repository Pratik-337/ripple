from .embedder import embed_text
from .index import VectorIndex
from .code_extractor import extract_code

def build_index(project_root, graph):
    # Get embedding dimension dynamically
    test_vector = embed_text("test", is_query=False)
    dim = len(test_vector)

    index = VectorIndex(dim)

    for (nid, ntype, nlang), node in graph.nodes.items():   
        if ntype not in ["FUNCTION", "METHOD", "CLASS"]:
            continue

        code = extract_code(project_root, node)
        if not code:
            continue

        embedding = embed_text(code, is_query=False)

        index.add(
            embedding,
            {
                "id": nid,
                "file": getattr(node, "file", ""),
                "type": ntype,
                "language": nlang,
                "code": code,
            }
        )
    return index
