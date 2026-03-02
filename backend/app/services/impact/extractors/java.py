"""Java extractor — handles .java files."""
from __future__ import annotations

from tree_sitter import Node

from .base import BaseExtractor, Call, Definition, Export, Import


class JavaExtractor(BaseExtractor):
    language = "java"

    def extract_imports(self, root: Node, source_bytes: bytes) -> list[Import]:
        imports: list[Import] = []

        for node in self.walk_nodes(root, ["import_declaration"]):
            text = self.node_text(node, source_bytes)
            # Strip 'import' and ';'
            path = text.replace("import", "").replace(";", "").strip()
            is_wildcard = path.endswith(".*")
            if is_wildcard:
                path = path[:-2]

            parts = path.split(".")
            symbol = "*" if is_wildcard else parts[-1]
            package = ".".join(parts[:-1])

            imports.append(Import(
                source=package, symbols=[symbol],
                is_wildcard=is_wildcard,
                line=node.start_point[0] + 1,
            ))

        return imports

    def extract_exports(self, root: Node, source_bytes: bytes) -> list[Export]:
        exports: list[Export] = []

        for node in self.walk_nodes(root, ["class_declaration", "interface_declaration"]):
            mods = node.child_by_field_name("modifiers")
            if mods and "public" in self.node_text(mods, source_bytes):
                name_node = node.child_by_field_name("name")
                if name_node:
                    exports.append(Export(
                        name=self.node_text(name_node, source_bytes),
                        kind="class" if node.type == "class_declaration" else "type",
                        signature=self.node_text(name_node, source_bytes),
                        line=node.start_point[0] + 1,
                    ))

        for node in self.walk_nodes(root, ["method_declaration"]):
            mods = node.child_by_field_name("modifiers")
            if mods and "public" in self.node_text(mods, source_bytes):
                name_node = node.child_by_field_name("name")
                if name_node:
                    exports.append(Export(
                        name=self.node_text(name_node, source_bytes),
                        kind="function",
                        signature=self._method_sig(node, source_bytes),
                        line=node.start_point[0] + 1,
                    ))

        return exports

    def extract_definitions(self, root: Node, source_bytes: bytes) -> list[Definition]:
        defs: list[Definition] = []

        for node in self.walk_nodes(root, ["method_declaration", "constructor_declaration"]):
            name_node = node.child_by_field_name("name")
            if not name_node:
                continue
            parent = self._enclosing_class(node, source_bytes)
            defs.append(Definition(
                name=self.node_text(name_node, source_bytes),
                kind="method",
                signature=self._method_sig(node, source_bytes),
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                parent=parent,
            ))

        for node in self.walk_nodes(root, ["class_declaration", "interface_declaration"]):
            name_node = node.child_by_field_name("name")
            if name_node:
                defs.append(Definition(
                    name=self.node_text(name_node, source_bytes),
                    kind="class" if node.type == "class_declaration" else "interface",
                    signature=self.node_text(name_node, source_bytes),
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                ))

        return defs

    def extract_calls(self, root: Node, source_bytes: bytes) -> list[Call]:
        calls: list[Call] = []

        for node in self.walk_nodes(root, ["method_invocation"]):
            name_node = node.child_by_field_name("name")
            obj_node = node.child_by_field_name("object")
            if name_node:
                callee = self.node_text(name_node, source_bytes)
                if obj_node:
                    callee = f"{self.node_text(obj_node, source_bytes)}.{callee}"
                calls.append(Call(
                    callee=callee,
                    line=node.start_point[0] + 1,
                    parent_def=self.find_enclosing_function(node, source_bytes),
                ))

        return calls

    def _method_sig(self, node: Node, source_bytes: bytes) -> str:
        ret = node.child_by_field_name("type")
        name = node.child_by_field_name("name")
        params = node.child_by_field_name("formal_parameters")
        sig = ""
        if ret:
            sig += self.node_text(ret, source_bytes) + " "
        if name:
            sig += self.node_text(name, source_bytes)
        if params:
            sig += self.node_text(params, source_bytes)
        return sig

    def _enclosing_class(self, node: Node, source_bytes: bytes) -> str | None:
        current = node.parent
        while current:
            if current.type == "class_body":
                cls = current.parent
                if cls:
                    name = cls.child_by_field_name("name")
                    if name:
                        return self.node_text(name, source_bytes)
            current = current.parent
        return None
