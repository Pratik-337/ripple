from core.node import Node
from core.relation import Relation
from core.traversal import traverse
from core.util import normalize_call_name

def parse_go(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes, relations = [], []
    src = source_code.encode("utf8")

    # -------- IMPORTS --------
    for child in root.children:
        if child.type == "import_declaration":
            for node in traverse(child):
                if node.type == "interpreted_string_literal":
                    module = src[node.start_byte:node.end_byte].decode("utf8").strip('"')
                    nodes.append(Node(module, "IMPORT", "GO"))
                    symbol_table.add_import(filename, module)

    # -------- FUNCTIONS --------
    for child in root.children:
        if child.type == "function_declaration":
            name_node = child.child_by_field_name("name")
            if not name_node:
                continue

            fn = src[name_node.start_byte:name_node.end_byte].decode("utf8")
            fn_id = f"{filename}.{fn}"

            nodes.append(Node(fn_id, "FUNCTION", "GO"))
            symbol_table.add_function(filename, fn)

            for node in traverse(child):
                if node.type == "call_expression":
                    fn_node = node.child_by_field_name("function")
                    if fn_node:
                        raw = src[fn_node.start_byte:fn_node.end_byte].decode("utf8")
                        called = normalize_call_name(raw)

                        resolved = symbol_table.resolve(
                            None, filename, called
                        )

                        relations.append(Relation(fn_id, resolved, "CALLS"))

    return nodes, relations
