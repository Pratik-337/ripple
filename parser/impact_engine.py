# parser/impact_engine.py

from pipeline import run_pipeline   # or whatever your structural entry is
from rag.index_builder import build_index
from rag.retriever import retrieve_similar
from rag.code_extractor import extract_code

def run_impact(project_root, change_request):
    # 1️⃣ Run existing structural analysis
    structural_result = run_pipeline(project_root, change_request)

    graph = structural_result.graph
    changed_node = structural_result.changed_node

    # 2️⃣ Run semantic layer
    try:
        index = build_index(project_root, graph)
        changed_code = extract_code(project_root, changed_node)

        semantic_hits = retrieve_similar(index, changed_code)

        # 3️⃣ Merge structural + semantic
        final_result = merge(structural_result, semantic_hits)

        return final_result

    except Exception:
        return structural_result