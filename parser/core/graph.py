class Graph:
    def __init__(self):
        self.nodes = {}
        self.relations = set()

    def add_node(self, node):
        key = (node.id, node.type, node.language)
        if key not in self.nodes:
            self.nodes[key] = node

    def add_relation(self, relation):
        self.relations.add((relation.source, relation.target, relation.type))

    def export(self):
        sorted_nodes = sorted(
            [n for n in self.nodes.values()],
            key=lambda n: (str(n.id), str(n.type), str(n.language))
        )
        sorted_relations = sorted(
            list(self.relations),
            key=lambda r: (str(r[0]), str(r[1]), str(r[2]))
        )
        return {
            'nodes': [
                {
                    'id': n.id, 
                    'type': n.type, 
                    'language': n.language, 
                    'file': n.file,
                    'start_line': n.start_line,
                    'end_line': n.end_line
                } 
                for n in sorted_nodes
            ],
            'relations': [
                {'from': r[0], 'to': r[1], 'type': r[2]} 
                for r in sorted_relations
            ]
        }
