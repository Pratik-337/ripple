from collections import deque

def get_neighborhood_nodes(graph, start_node_id, max_hops=2, direction='undirected', include_peers=True, max_size=50):
    """
    Returns a dictionary of {node_id: relationship_type} 
    within N hops, with a safety cap.
    """
    # Map of node_id -> relationship string
    neighborhood = {start_node_id: 'SELF'}
    adj = {}
    
    # 1. Build adjacency with relationship metadata
    for src, tgt, rel_type in graph.relations:
        if direction in ['undirected', 'forward']:
            if src not in adj: adj[src] = []
            adj[src].append((tgt, rel_type))
        if direction in ['undirected', 'reverse']:
            if tgt not in adj: adj[tgt] = []
            adj[tgt].append((src, f'REVERSE_{rel_type}'))

    # 2. BFS with Hard Cap
    queue = deque([(start_node_id, 0)])
    visited = {start_node_id}
    
    while queue:
        if len(visited) >= max_size:
            break
            
        curr_id, dist = queue.popleft()
        if dist < max_hops:
            for neighbor, rel in adj.get(curr_id, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    neighborhood[neighbor] = rel
                    queue.append((neighbor, dist + 1))
                    if len(visited) >= max_size: break
                    
    # 3. Class-Peer Expansion
    if include_peers and len(visited) < max_size:
        for node_id in list(neighborhood.keys()):
            if '::' in node_id:
                parent_class = node_id.rsplit('::', 1)[0]
                for (nid, ntype, nlang) in graph.nodes.keys():
                    if nid.startswith(parent_class) and nid not in neighborhood:
                        neighborhood[nid] = 'CLASS_PEER'
                        if len(neighborhood) >= max_size: break
                if len(neighborhood) >= max_size: break

    # 4. Registry Guard
    registered_ids = set(nid for (nid, ntype, nlang) in graph.nodes.keys())
    return {nid: rel for nid, rel in neighborhood.items() if nid in registered_ids}

def traverse(node):
    cursor = node.walk()
    visited_children = False
    while True:
        if not visited_children:
            yield cursor.node
            if cursor.goto_first_child():
                visited_children = False
                continue
            visited_children = True
        if cursor.goto_next_sibling():
            visited_children = False
            continue
        if not cursor.goto_parent():
            break
