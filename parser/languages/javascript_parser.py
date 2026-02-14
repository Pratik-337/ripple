from core.node import Node
from core.relation import Relation
from core.traversal import traverse
from core.util import normalize_call_name


def parse_javascript(tree, source_code, filename, symbol_table):
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
                    module = src[sub.start_byte:sub.end_byte] \
                        .decode("utf8") \
                        .strip('"\'')
                    nodes.append(Node(module, "IMPORT", "JAVASCRIPT"))
                    symbol_table.add_import(filename, module)

    # ===============================
    # FUNCTIONS
    # ===============================
    for child in root.children:
        if child.type != "function_declaration":
            continue

        name_node = child.child_by_field_name("name")
        if not name_node:
            continue

        fn_name = src[name_node.start_byte:name_node.end_byte].decode("utf8")
        fn_id = f"{filename}.{fn_name}"

        nodes.append(Node(fn_id, "FUNCTION", "JAVASCRIPT"))
        symbol_table.add_function(filename, fn_name)

        for n in traverse(child):
            if n.type != "call_expression":
                continue

            call_text = src[n.start_byte:n.end_byte].decode("utf8")
            called = normalize_call_name(call_text)

            relations.append(Relation(fn_id, called, "CALLS"))

            # ✅ Option B: minimal API path capture
            if "fetch(" in call_text:
                for sub in traverse(n):
                    if sub.type == "string":
                        path = src[sub.start_byte:sub.end_byte] \
                            .decode("utf8") \
                            .strip("\"'")
                        relations.append(
                            Relation(fn_id, path, "USES_API_PATH")
                        )
                        break

    # ===============================
    # CLASSES
    # ===============================
    for child in root.children:
        if child.type != "class_declaration":
            continue

        name_node = child.child_by_field_name("name")
        if not name_node:
            continue

        class_name = src[name_node.start_byte:name_node.end_byte].decode("utf8")
        nodes.append(Node(class_name, "CLASS", "JAVASCRIPT"))
        symbol_table.add_class(filename, class_name)

        body = child.child_by_field_name("body")
        if not body:
            continue

        for member in body.children:
            if member.type != "method_definition":
                continue

            method_node = member.child_by_field_name("name")
            if not method_node:
                continue

            method = src[method_node.start_byte:method_node.end_byte].decode("utf8")
            method_id = f"{class_name}.{method}"

            nodes.append(Node(method_id, "METHOD", "JAVASCRIPT"))
            relations.append(Relation(class_name, method_id, "HAS_METHOD"))
            symbol_table.add_function(filename, method)

            for n in traverse(member):
                if n.type != "call_expression":
                    continue

                call_text = src[n.start_byte:n.end_byte].decode("utf8")
                called = normalize_call_name(call_text)

                relations.append(Relation(method_id, called, "CALLS"))

                # ✅ API path capture (same logic)
                if "fetch(" in call_text:
                    for sub in traverse(n):
                        if sub.type == "string":
                            path = src[sub.start_byte:sub.end_byte] \
                                .decode("utf8") \
                                .strip("\"'")
                            relations.append(
                                Relation(method_id, path, "USES_API_PATH")
                            )
                            break

    return nodes, relations
