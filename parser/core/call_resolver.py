from parser.core.relation import Relation


def resolve_calls(graph, symbol_table):
    """
    Resolve CALLS edges to fully-qualified method names.
    Ensures all relations are normalized to Relation objects.
    """

    normalized_relations = set()

    # --- Step 0: normalize all relations ---
    for rel in graph.relations:
        if isinstance(rel, Relation):
            normalized_relations.add(rel)
        else:
            src, tgt, typ = rel
            normalized_relations.add(Relation(src, tgt, typ))

    resolved_relations = set()

    # --- Step 1: resolve CALLS ---
    for rel in normalized_relations:
        if rel.type != "CALLS":
            resolved_relations.add(rel)
            continue

        src = rel.source
        tgt = rel.target

        # Already resolved
        if "." in tgt:
            resolved_relations.add(rel)
            continue

        # Invalid source
        if "." not in src:
            resolved_relations.add(rel)
            continue

        caller_class = src.split(".", 1)[0]

        caller_owner = src.split(".", 1)[0]

        # CASE 1 — True class method
        if caller_owner in symbol_table.methods:
            resolved_target = symbol_table.resolve_method_call(
                current_class=caller_owner,
                call_name=tgt
            )

        # CASE 2 — Top-level file function
        else:
            resolved_target = symbol_table.resolve(
                current_class=None,
                current_file=caller_owner,
                call_name=tgt
            )

        resolved_relations.add(
            Relation(src, resolved_target, "CALLS")
        )

    graph.relations = resolved_relations
    return graph
