from parser.core.graph import Graph
from parser.core.node import Node
from parser.core.relation import Relation


EDGE_MAP = {
    "HAS_METHOD": "CONTAINS",
    "CALLS": "CALLS",
    "ANNOTATED_WITH": "ANNOTATED_WITH"
}


class GraphBuilder:
    """
    Formal graph construction layer.
    Parsers do NOT touch Graph directly anymore.
    """

    def __init__(self):
        self.graph = Graph()

    def add_node(self, node: Node):
        # Central place to validate node identity later
        self.graph.add_node(node)

    def add_relation(self, relation: Relation):
        edge_type = EDGE_MAP.get(relation.type, relation.type)

        normalized = Relation(
            relation.source,
            relation.target,
            edge_type
        )


        self.graph.add_relation(normalized)

    def build(self) -> Graph:
        return self.graph
