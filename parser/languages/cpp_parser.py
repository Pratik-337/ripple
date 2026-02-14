from core.node import Node
from core.relation import Relation
from core.traversal import traverse
from core.util import normalize_call_name
def parse_cpp(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes, relations = [], []
    src = source_code.encode("utf8")

    # -------- IMPORTS (#include) --------
    for child in root.children:
        if child.type == "preproc_include":
            include_text = src[child.start_byte:child.end_byte].decode("utf8")
            nodes.append(Node(include_text, "IMPORT", "CPP"))
            symbol_table.add_import(filename, include_text)

    # -------- FUNCTIONS (free functions like main) --------
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

            nodes.append(Node(fn_id, "FUNCTION", "CPP"))
            symbol_table.add_function(filename, fn_name)

            for node in traverse(child):
                if node.type == "call_expression":
                    fn = node.child_by_field_name("function")
                    if fn:
                        called = src[fn.start_byte:fn.end_byte].decode("utf8")
                        relations.append(Relation(fn_id, called, "CALLS"))

    # -------- CLASSES + METHODS --------
    for child in root.children:
        if child.type == "class_specifier":
            name_node = child.child_by_field_name("name")
            if not name_node:
                continue

            class_name = src[name_node.start_byte:name_node.end_byte].decode("utf8")
            nodes.append(Node(class_name, "CLASS", "CPP"))
            symbol_table.add_class(filename, class_name)

            body = child.child_by_field_name("body")
            if not body:
                continue

            for member in body.children:
                if member.type == "function_definition":
                    declarator = member.child_by_field_name("declarator")
                    if not declarator:
                        continue

                    method_name_node = declarator.child_by_field_name("declarator")
                    if not method_name_node:
                        continue

                    method = src[
                        method_name_node.start_byte:method_name_node.end_byte
                    ].decode("utf8")

                    method_id = f"{class_name}.{method}"

                    nodes.append(Node(method_id, "METHOD", "CPP"))
                    relations.append(Relation(class_name, method_id, "HAS_METHOD"))

                    for n in traverse(member):
                        if n.type == "call_expression":
                            fn = n.child_by_field_name("function")
                            if fn:
                                raw = src[fn.start_byte:fn.end_byte].decode("utf8")
                                called = normalize_call_name(raw)
                                relations.append(Relation(fn_id, called, "CALLS"))

    return nodes, relations
