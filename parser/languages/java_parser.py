from core.node import Node
from core.relation import Relation
from core.traversal import traverse
from core.util import normalize_call_name

SPRING_ANNOTATIONS = {
    "GetMapping",
    "PostMapping",
    "PutMapping",
    "DeleteMapping",
    "RequestMapping"
}


def parse_java(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes = []
    relations = []

    src = source_code.encode("utf8")

    current_class = None

    # ===============================
    # IMPORTS
    # ===============================
    for child in root.children:
        if child.type == "import_declaration":
            import_text = src[
                child.start_byte:child.end_byte
            ].decode("utf8").replace("import", "").replace(";", "").strip()

            nodes.append(Node(import_text, "IMPORT", "JAVA"))
            symbol_table.add_import("java", import_text)

    # ===============================
    # CLASSES
    # ===============================
    for child in root.children:
        if child.type == "class_declaration":
            name_node = child.child_by_field_name("name")
            if not name_node:
                continue

            class_name = src[
                name_node.start_byte:name_node.end_byte
            ].decode("utf8")

            current_class = class_name
            nodes.append(Node(class_name, "CLASS", "JAVA"))
            symbol_table.add_class(filename,class_name)

            # ===============================
            # CLASS BODY
            # ===============================
            body = child.child_by_field_name("body")
            if not body:
                continue

            for member in body.children:

                # -------------------------------
                # METHODS
                # -------------------------------
                if member.type == "method_declaration":
                    method_name_node = member.child_by_field_name("name")
                    if not method_name_node:
                        continue

                    method_name = src[
                        method_name_node.start_byte:method_name_node.end_byte
                    ].decode("utf8")

                    method_id = f"{class_name}.{method_name}"

                    nodes.append(Node(method_id, "METHOD", "JAVA"))
                    relations.append(
                        Relation(class_name, method_id, "HAS_METHOD")
                    )

                    symbol_table.add_method(class_name, method_name)

                    # -------------------------------
                    # METHOD ANNOTATIONS
                    # -------------------------------
                    for n in traverse(member):
                        if n.type == "annotation":
                            ann_text = src[
                                n.start_byte:n.end_byte
                            ].decode("utf8")

                            for spring_ann in SPRING_ANNOTATIONS:
                                if spring_ann in ann_text:
                                    relations.append(
                                        Relation(ann_text, method_id, "ANNOTATED_WITH")
                                    )
                    # -------------------------------
                    # METHOD CALLS
                    # -------------------------------
                    for node in traverse(member):
                        if node.type == "method_invocation":
                            call_node = node.child_by_field_name("name")
                            if call_node:
                                raw_called = src[
                                    call_node.start_byte:call_node.end_byte
                                ].decode("utf8")

                                called = normalize_call_name(raw_called)

                                resolved = symbol_table.resolve(
                                    current_class=class_name,
                                    current_file=filename,
                                    call_name=called
                                )

                                relations.append(
                                    Relation(method_id, resolved, "CALLS")
                                )
    return nodes, relations
