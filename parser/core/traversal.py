from collections import deque

def get_neighborhood_nodes(graph, start_node_id, max_hops=2, direction='undirected', include_peers=True, max_size=50):
    """
    Returns a set of node IDs related within N hops, with a safety cap.
    """
    neighborhood = {start_node_id}
    adj = {}
    
    # 1. Build adjacency
    for src, tgt, rel_type in graph.relations:
        if direction in ['undirected', 'forward']:
            if src not in adj: adj[src] = []
            adj[src].append(tgt)
        if direction in ['undirected', 'reverse']:
            if tgt not in adj: adj[tgt] = []
            adj[tgt].append(src)

    # 2. BFS with Hard Cap (Explosion Guard)
    queue = deque([(start_node_id, 0)])
    visited = {start_node_id}
    
    while queue:
        # Pillar: Neighborhood Size Cap
        if len(visited) >= max_size:
            break
            
        curr_id, dist = queue.popleft()
        if dist < max_hops:
            for neighbor in adj.get(curr_id, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    neighborhood.add(neighbor)
                    queue.append((neighbor, dist + 1))
                    if len(visited) >= max_size:
                        break
                    
    # 3. Class-Peer Expansion (Still capped by registry)
    if include_peers and len(visited) < max_size:
        for node_id in list(neighborhood):
            if '::' in node_id:
                parent_class = node_id.rsplit('::', 1)[0]
                for (nid, ntype, nlang) in graph.nodes.keys():
                    if nid.startswith(parent_class):
                        if nid not in neighborhood:
                            neighborhood.add(nid)
                            if len(neighborhood) >= max_size: break
                if len(neighborhood) >= max_size: break

    # 4. Registry Guard
    registered_ids = set(nid for (nid, ntype, nlang) in graph.nodes.keys())
    return {nid for nid in neighborhood if nid in registered_ids}

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
