from core.node import Node
from core.relation import Relation
from core.traversal import traverse
from core.util import normalize_call_name

def parse_typescript(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes = []
    relations = []

    src = source_code.encode("utf8")

    # ===============================
    # IMPORTS
    # ===============================
    for child in root.children:
        if child.type == "import_statement":
            for sub in child.children:
                if sub.type == "string":
                    module = src[
                        sub.start_byte:sub.end_byte
                    ].decode("utf8").strip('"\'')
                    nodes.append(Node(module, "IMPORT", "TYPESCRIPT"))
                    symbol_table.add_import(filename, module)
                    break

    # ===============================
    # FUNCTIONS
    # ===============================
    for child in root.children:
        if child.type == "function_declaration":
            name_node = child.child_by_field_name("name")
            if not name_node:
                continue

            fn = src[
                name_node.start_byte:name_node.end_byte
            ].decode("utf8")

            fn_id = f"{filename}.{fn}"
            nodes.append(Node(fn_id, "FUNCTION", "TYPESCRIPT"))
            symbol_table.add_function(filename, fn)

            for n in traverse(child):
                if n.type == "call_expression":
                    call = n.child_by_field_name("function")
                    if call:
                        called = src[
                            call.start_byte:call.end_byte
                        ].decode("utf8")
                        resolved = symbol_table.resolve(current_class=None,current_file=filename,call_name=called)
                        relations.append(
                            Relation(fn_id, resolved, "CALLS")
                        )

    # ===============================
    # CLASSES + METHODS
    # ===============================
    for child in root.children:
        if child.type == "class_declaration":
            name_node = child.child_by_field_name("name")
            if not name_node:
                continue

            class_name = src[
                name_node.start_byte:name_node.end_byte
            ].decode("utf8")

            nodes.append(Node(class_name, "CLASS", "TYPESCRIPT"))
            symbol_table.add_class(filename, class_name)

            body = child.child_by_field_name("body")
            if not body:
                continue

            for member in body.children:
                if member.type == "method_definition":
                    method_node = member.child_by_field_name("name")
                    if not method_node:
                        continue

                    method = src[
                        method_node.start_byte:method_node.end_byte
                    ].decode("utf8")

                    method_id = f"{class_name}.{method}"
                    nodes.append(Node(method_id, "METHOD", "TYPESCRIPT"))
                    relations.append(
                        Relation(class_name, method_id, "HAS_METHOD")
                    )

                    symbol_table.add_function(filename, method)

                    for n in traverse(member):
                        if n.type == "call_expression":
                            call = n.child_by_field_name("function")
                            if call:
                                raw_called = src[call.start_byte:call.end_byte].decode("utf8")
                                called = normalize_call_name(raw_called)
                                relations.append(Relation(fn_id, called, "CALLS"))
    return nodes, relations
