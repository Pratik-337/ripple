from core.node import Node
from core.relation import Relation
from core.traversal import traverse
from core.util import normalize_call_name

def parse_c(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes, relations = [], []
    src = source_code.encode("utf8")

    # -------- IMPORTS --------
    for child in root.children:
        if child.type == "preproc_include":
            include_text = src[child.start_byte:child.end_byte].decode("utf8")
            nodes.append(Node(include_text, "IMPORT", "C"))
            symbol_table.add_import(filename, include_text)

    # -------- FUNCTIONS --------
    for child in root.children:
        if child.type == "function_definition":
            declarator = child.child_by_field_name("declarator")
            if not declarator:
                continue

            name_node = declarator.child_by_field_name("declarator")
            if not name_node:
                continue

            fn_name = src[name_node.start_byte:name_node.end_byte].decode("utf8")
            fn_id = f"{filename}.{fn_name}"

            nodes.append(Node(fn_id, "FUNCTION", "C"))
            symbol_table.add_function(filename, fn_name)

            # -------- FUNCTION CALLS --------
            for node in traverse(child):
                if node.type == "call_expression":
                    fn = node.child_by_field_name("function")
                    if fn:
                        raw = src[fn.start_byte:fn.end_byte].decode("utf8")
                        called = normalize_call_name(raw)

                        resolved = symbol_table.resolve(
                            current_class=None,
                            current_file=filename,
                            call_name=called
                        )

                        relations.append(Relation(fn_id, resolved, "CALLS"))

    return nodes, relations
