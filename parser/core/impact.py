from collections import deque, defaultdict

# Relations that propagate impact
IMPACT_EDGES = {
    "CALLS",
    "CALLS_API",
    "HAS_METHOD",
    "IMPORTS",
    "CROSS_LANG_EQUIVALENT",
    "REVERSE_CALLS_API",   # 🔥 ADD THIS
}


# Relations that should propagate impact backwards
REVERSE_EDGES = {
    "CALLS",
    "CALLS_API",
}

def build_adjacency(graph):
    """
    Build adjacency list with forward + selective reverse edges
    """
    adj = defaultdict(list)

    for src, dst, rel_type in graph.relations:
        if rel_type not in IMPACT_EDGES:
            continue

        # forward edge
        adj[src].append((dst, rel_type))

        # backward edge (for callers / API consumers)
        if rel_type in REVERSE_EDGES:
            adj[dst].append((src, f"REVERSE_{rel_type}"))

    return adj


def propagate_impact(graph, start_node_id, max_depth=10):
    """
    BFS-based impact propagation
    """
    adjacency = build_adjacency(graph)

    impacted = {}
    queue = deque()

    impacted[start_node_id] = {
        "depth": 0,
        "via": None
    }
    queue.append(start_node_id)

    while queue:
        current = queue.popleft()
        current_depth = impacted[current]["depth"]

        if current_depth >= max_depth:
            continue

        for neighbor, rel_type in adjacency.get(current, []):
            if neighbor not in impacted:
                impacted[neighbor] = {
                    "depth": current_depth + 1,
                    "via": rel_type
                }
                queue.append(neighbor)

    return impacted
