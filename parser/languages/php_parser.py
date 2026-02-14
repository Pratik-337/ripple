from core.node import Node
from core.relation import Relation
from core.traversal import traverse
from core.util import normalize_call_name   

def parse_php(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes, relations = [], []
    src = source_code.encode("utf8")

    # ===============================
    # IMPORTS (require / include)
    # ===============================
    for node in traverse(root):
        if node.type in ("require_expression", "include_expression"):
            arg = node.child_by_field_name("argument")
            if arg:
                module = src[arg.start_byte:arg.end_byte].decode("utf8").strip('"\'')
                nodes.append(Node(module, "IMPORT", "PHP"))
                symbol_table.add_import(filename, module)

    # ===============================
    # FUNCTIONS
    # ===============================
    for child in root.children:
        if child.type == "function_definition":
            name_node = child.child_by_field_name("name")
            if not name_node:
                continue

            fn = src[name_node.start_byte:name_node.end_byte].decode("utf8")
            fn_id = f"{filename}.{fn}"

            nodes.append(Node(fn_id, "FUNCTION", "PHP"))
            symbol_table.add_function(filename, fn)

            for n in traverse(child):
                if n.type == "function_call_expression":
                    call_node = n.child_by_field_name("function")
                    if call_node:
                        raw = src[call_node.start_byte:call_node.end_byte].decode("utf8")
                        called = normalize_call_name(raw)

                        resolved = symbol_table.resolve(
                            None, filename, called
                        )

                        relations.append(Relation(fn_id, resolved, "CALLS"))

    # ===============================
    # CLASSES + METHODS
    # ===============================
    for child in root.children:
        if child.type == "class_declaration":
            name_node = child.child_by_field_name("name")
            if not name_node:
                continue

            class_name = src[name_node.start_byte:name_node.end_byte].decode("utf8")
            nodes.append(Node(class_name, "CLASS", "PHP"))
            symbol_table.add_class(filename, class_name)

            body = child.child_by_field_name("body")
            if not body:
                continue

            for member in body.children:
                if member.type == "method_declaration":
                    mname = member.child_by_field_name("name")
                    if not mname:
                        continue

                    method = src[mname.start_byte:mname.end_byte].decode("utf8")
                    method_id = f"{class_name}.{method}"

                    nodes.append(Node(method_id, "METHOD", "PHP"))
                    relations.append(Relation(class_name, method_id, "HAS_METHOD"))
                    symbol_table.add_method(class_name, method)

                    for n in traverse(member):
                        if n.type == "function_call_expression":
                            call = n.child_by_field_name("name")
                            if call:
                                raw_called = src[call.start_byte:call.end_byte].decode("utf8")
                                called = normalize_call_name(raw_called)
                                relations.append(Relation(method_id, called, "CALLS"))
    return nodes, relations
