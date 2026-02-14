from core.node import Node
from core.relation import Relation
from core.traversal import traverse
from core.util import normalize_call_name

def parse_rust(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes, relations = [], []
    src = source_code.encode("utf8")

    for child in root.children:
        if child.type == "use_declaration":
            module = src[child.start_byte:child.end_byte].decode("utf8")
            nodes.append(Node(module, "IMPORT", "RUST"))
            symbol_table.add_import(filename, module)

        if child.type == "function_item":
            name = child.child_by_field_name("name")
            if name:
                fn = src[name.start_byte:name.end_byte].decode("utf8")
                fn_id = f"{filename}.{fn}"
                symbol_table.add_function(filename, fn)
                nodes.append(Node(fn_id, "FUNCTION", "RUST"))

                for n in traverse(child):
                    if n.type == "call_expression":
                        raw_called = src[n.start_byte:n.end_byte].decode("utf8")
                        called = normalize_call_name(raw_called)
                        relations.append(Relation(fn_id, called, "CALLS"))
    return nodes, relations
