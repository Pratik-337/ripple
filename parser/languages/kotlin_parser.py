from core.node import Node
from core.relation import Relation
from core.traversal import traverse
from core.util import normalize_call_name

def parse_kotlin(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes, relations = [], []
    src = source_code.encode("utf8")

    current_class = None

    for child in root.children:
        if child.type == "class_declaration":
            name_node = child.child_by_field_name("name")
            if not name_node:
                continue

            class_name = src[name_node.start_byte:name_node.end_byte].decode("utf8")
            current_class = class_name

            nodes.append(Node(class_name, "CLASS", "KOTLIN"))
            symbol_table.add_class(filename, class_name)

            body = child.child_by_field_name("body")
            if not body:
                continue

            for member in body.children:
                if member.type == "function_declaration":
                    name_node = member.child_by_field_name("name")
                    if not name_node:
                        continue

                    method = src[name_node.start_byte:name_node.end_byte].decode("utf8")
                    method_id = f"{class_name}.{method}"

                    nodes.append(Node(method_id, "METHOD", "KOTLIN"))
                    relations.append(Relation(class_name, method_id, "HAS_METHOD"))

                    symbol_table.add_function(filename, method)

                    for n in traverse(member):
                        if n.type == "call_expression":
                            fn = n.child_by_field_name("callee")
                            if fn:
                                raw = src[fn.start_byte:fn.end_byte].decode("utf8")
                                called = normalize_call_name(raw)

                                resolved = symbol_table.resolve(
                                    None, filename, called
                                )

                                relations.append(Relation(method_id, resolved, "CALLS"))

    return nodes, relations
