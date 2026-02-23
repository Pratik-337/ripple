from collections import deque

# ------------------------------------------------------------------------------
# Graph Representation
# ------------------------------------------------------------------------------

def build_adjacency(graph):
    """
    Builds an adjacency list representation of the graph from its relations.
    Each node maps to a list of (neighbor, relation_type) tuples.
    """
    adjacency = {}
    for rel_tuple in graph.relations: # Iterate over the (source, target, type) tuples
        caller = rel_tuple[0]  # Access source by index
        callee = rel_tuple[1]  # Access target by index
        rel_type = rel_tuple[2] # Access type by index

        if caller not in adjacency:
            adjacency[caller] = []
        if callee not in adjacency: # Ensure all nodes are in adjacency map
            adjacency[callee] = []

        # Representing edge as (callee, type) to distinguish relation types
        adjacency[caller].append((callee, rel_type))
    return adjacency

# ------------------------------------------------------------------------------
# Impact Propagation
# ------------------------------------------------------------------------------

def propagate_impact(graph, start_node_id, max_depth=5):
    """
    Propagates impact from a start node through the graph using BFS.
    Returns a dictionary of impacted nodes with their depth and the relation type that led to them.
    """
    adjacency = build_adjacency(graph)
    impacted_nodes = {} # node_id -> {depth, via_relation_type}
    queue = deque([(start_node_id, 0, "START")]) # (node_id, depth, via_relation_type)

    if start_node_id not in adjacency:
        # If start_node_id is not in adjacency, it might be an isolated node
        # or a node that only has incoming relations.
        # We should still include it as impacted.
        impacted_nodes[start_node_id] = {"depth": 0, "via": "START"}
        # If it has no outgoing edges, BFS won't proceed, which is correct.
        # If it has incoming edges, we'd need a reverse adjacency list for reverse impact.
        # For now, we proceed with forward impact.

    while queue:
        current_node_id, depth, via_relation = queue.popleft()

        if current_node_id in impacted_nodes and impacted_nodes[current_node_id]["depth"] <= depth:
            continue # Already visited at a shallower or equal depth

        impacted_nodes[current_node_id] = {"depth": depth, "via": via_relation}

        if depth >= max_depth:
            continue

        # Propagate to neighbors
        for neighbor_id, rel_type in adjacency.get(current_node_id, []):
            if neighbor_id not in impacted_nodes or impacted_nodes[neighbor_id]["depth"] > depth + 1:
                queue.append((neighbor_id, depth + 1, rel_type))

    return impacted_nodes