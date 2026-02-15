class Graph:
    def __init__(self):
        self.nodes = {}              # key -> Node
        self.relations = set()       # (from, to, type)

    def add_node(self, node):
        key = (node.id, node.type, node.language)
        if key not in self.nodes:
            self.nodes[key] = node

    def add_relation(self, relation):
        key = (relation.source, relation.target, relation.type)
        self.relations.add(key)

    def export(self):
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "relations": [
                {
                    "from": src,
                    "to": tgt,
                    "type": typ
                }
                for (src, tgt, typ) in self.relations
            ]
        }
