from core.relation import Relation

SPRING_ANNOTATIONS = {
    "@GetMapping",
    "@PostMapping",
    "@PutMapping",
    "@DeleteMapping",
    "@RequestMapping"
}

def link_api_calls(graph):
    api_calls = []      # (caller, path)
    api_handlers = []   # (handler, path)

    # 1️⃣ Frontend API paths
    for src, tgt, rel_type in graph.relations:
        if rel_type == "USES_API_PATH":
            api_calls.append((src, tgt))

    # 2️⃣ Backend handlers (⚠️ FIXED DIRECTION)
    for src, tgt, rel_type in graph.relations:
        if rel_type != "ANNOTATED_WITH":
            continue

        annotation = src   # ← FIX IS HERE
        handler = tgt

        for ann in SPRING_ANNOTATIONS:
            if annotation.startswith(ann) and "(" in annotation:
                path = annotation[
                    annotation.find("(")+1 : annotation.find(")")
                ].strip('"')

                api_handlers.append((handler, path))

    # 3️⃣ Match
    count = 0
    for caller, path in api_calls:
        for handler, handler_path in api_handlers:
            if path == handler_path:
                graph.add_relation(
                    Relation(caller, handler, "CALLS_API")
                )
                count += 1

    print(f"API edges added: {count}")
    return graph
