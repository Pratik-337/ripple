from collections import deque

def build_reverse_adjacency(graph):
    rev_adj = {}
    for rel in graph.relations:
        caller, callee, rel_type = rel[0], rel[1], rel[2]
        if callee not in rev_adj:
            rev_adj[callee] = []
        if caller not in rev_adj:
            rev_adj[caller] = []
        rev_adj[callee].append((caller, rel_type))
    return rev_adj

def propagate_impact(graph, start_node_id, max_depth=5):
    rev_adj = build_reverse_adjacency(graph)
    impacted_nodes = {}
    
    # queue: (node_id, depth, via_relation_type)
    queue = deque([(start_node_id, 0, 'CHANGE')])

    while queue:
        curr_id, depth, via = queue.popleft()
        print(f"   [Impact] Visiting: {curr_id} (via {via}, depth {depth})")
        
        # If we already saw this node at a shallower depth, skip
        if curr_id in impacted_nodes and impacted_nodes[curr_id]['depth'] <= depth:
            # But if the current path is behavioral (CALLS) and the old one was structural (CONTAINS), 
            # we might want to keep the behavioral one? For now, depth is primary.
            continue

        impacted_nodes[curr_id] = {'depth': depth, 'via': via}
        
        if depth < max_depth:
            for caller_id, rel_type in rev_adj.get(curr_id, []):

                
                queue.append((caller_id, depth + 1, rel_type))
                
    return impacted_nodes
