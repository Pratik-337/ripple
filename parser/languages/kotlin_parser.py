from core.node import Node
from core.relation import Relation
from core.traversal import traverse
from core.util import normalize_call_name

def parse_kotlin(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes, relations = [], []
    src = source_code.encode("utf8")

    # ===============================
    # IMPORTS
    # ===============================
    for child in root.children:
        if child.type == "import_header":
            text = src[child.start_byte:child.end_byte].decode("utf8")
            module = text.replace("import", "").strip()
            nodes.append(Node(module, "IMPORT", "KOTLIN"))
            symbol_table.add_import(filename, module)

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

            nodes.append(Node(class_name, "CLASS", "KOTLIN"))
            symbol_table.add_class(filename, class_name)

            body = child.child_by_field_name("body")
            if not body:
                continue

            for member in body.children:
                if member.type == "function_declaration":
                    fn_node = member.child_by_field_name("name")
                    if not fn_node:
                        continue

                    fn = src[
                        fn_node.start_byte:fn_node.end_byte
                    ].decode("utf8")

                    fn_id = f"{class_name}.{fn}"

                    nodes.append(Node(fn_id, "METHOD", "KOTLIN"))
                    relations.append(
                        Relation(class_name, fn_id, "HAS_METHOD")
                    )

                    symbol_table.add_method(class_name, fn)

                    # method calls
                    for node in traverse(member):
                        if node.type == "call_expression":
                            callee = node.child_by_field_name("callee")
                            if callee:
                                raw_called = src[node.start_byte:node.end_byte].decode("utf8")
                                called = normalize_call_name(raw_called)
                                resolved = symbol_table.resolve(filename, called)
                                relations.append(Relation(method_id, called, "CALLS"))

    return nodes, relations
