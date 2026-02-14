from core.node import Node
from core.relation import Relation
from core.traversal import traverse
from core.util import normalize_call_name

def parse_python(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes = []
    relations = []

    src = source_code.encode("utf8")

    imports = []

    # -------- IMPORTS --------
    for child in root.children:
        if child.type == "import_statement":
            for name in child.children:
                if name.type == "dotted_name":
                    module = src[name.start_byte:name.end_byte].decode("utf8")
                    imports.append(module)
                    symbol_table.add_import(filename, module)
                    nodes.append(Node(module, "IMPORT", "PYTHON"))

        elif child.type == "import_from_statement":
            module_node = child.child_by_field_name("module")
            names_node = child.child_by_field_name("name")

            if module_node:
                imports.append(module)   # ← THIS LINE
                module = src[module_node.start_byte:module_node.end_byte].decode("utf8")
                symbol_table.add_import(filename, module)
                nodes.append(Node(module, "IMPORT", "PYTHON"))

                # NEW: track imported symbols
                for name in child.children:
                    if name.type == "identifier":
                        imported_fn = name.text.decode("utf8")
                        symbol_table.add_function(module, imported_fn)


    # -------- FUNCTIONS --------
    for child in root.children:
        if child.type != "function_definition":
            continue

        name_node = child.child_by_field_name("name")
        if not name_node:
            continue

        fn = src[name_node.start_byte:name_node.end_byte].decode("utf8")
        fn_id = f"{filename}.{fn}"

        symbol_table.add_function(f"{filename}", fn)

        nodes.append(Node(fn_id, "FUNCTION", "PYTHON"))

        # function → imports
        for imp in imports:
            relations.append(Relation(fn_id, imp, "IMPORTS"))

        # -------- FUNCTION CALLS --------
        for node in traverse(child):
            if node.type == "call":
                call_node = node.child_by_field_name("function")
                if call_node:
                    raw_called = src[node.start_byte:node.end_byte].decode("utf8")
                    called = normalize_call_name(raw_called)
                    resolved = symbol_table.resolve(
                        current_class=None,        # Python has no class here
                        current_file=filename,
                        call_name=called
                    )
                    relations.append(Relation(fn_id, resolved, "CALLS"))

    return nodes, relations
