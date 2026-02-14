def resolve_calls(graph, symbol_table):
    """
    Resolves ambiguous CALLS like:
    helper -> test.helper or Class.helper
    """
    resolved_relations = set()

    for (src, tgt, typ) in graph.relations:
        if typ != "CALLS":
            resolved_relations.add((src, tgt, typ))
            continue

        # Already resolved
        if "." in tgt:
            resolved_relations.add((src, tgt, typ))
            continue

        caller_file = src.split(".")[0]
        caller_class = src.split(".")[0] if "." in src else None

        resolved = symbol_table.resolve(
            current_class=caller_class,
            current_file=caller_file,
            call_name=tgt
        )

        resolved_relations.add((src, resolved, typ))

    graph.relations = resolved_relations
    return graph
