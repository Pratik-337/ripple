"""Python extractor — handles .py files."""
from __future__ import annotations

from tree_sitter import Node

from .base import BaseExtractor, Call, Definition, Export, Import


class PythonExtractor(BaseExtractor):
    language = "python"

    def extract_imports(self, root: Node, source_bytes: bytes) -> list[Import]:
        imports: list[Import] = []

        # import os / import os.path as osp
        for node in self.walk_nodes(root, ["import_statement"]):
            for child in node.children:
                if child.type == "dotted_name":
                    imports.append(Import(
                        source=self.node_text(child, source_bytes).replace(".", "/"),
                        line=node.start_point[0] + 1,
                    ))
                elif child.type == "aliased_import":
                    name_node = child.child_by_field_name("name")
                    if name_node:
                        imports.append(Import(
                            source=self.node_text(name_node, source_bytes).replace(".", "/"),
                            line=node.start_point[0] + 1,
                        ))

        # from .auth import validateUser, AuthToken
        for node in self.walk_nodes(root, ["import_from_statement"]):
            module = node.child_by_field_name("module_name")
            path = self.node_text(module, source_bytes) if module else "."

            symbols: list[str] = []
            for child in node.children:
                if child.type in ("dotted_name", "identifier") and child != module:
                    symbols.append(self.node_text(child, source_bytes))
                elif child.type == "aliased_import":
                    name = child.child_by_field_name("name")
                    if name:
                        symbols.append(self.node_text(name, source_bytes))

            imports.append(Import(source=path, symbols=symbols, line=node.start_point[0] + 1))

        return imports

    def extract_exports(self, root: Node, source_bytes: bytes) -> list[Export]:
        # Python has no explicit exports — everything at module level is importable
        exports: list[Export] = []

        # Check __all__ first for explicit public API
        all_names: set[str] = set()
        for node in self.walk_nodes(root, ["assignment"]):
            left = node.child_by_field_name("left")
            if left and self.node_text(left, source_bytes) == "__all__":
                right = node.child_by_field_name("right")
                if right:
                    for s in self.children_of_type(right, "string"):
                        name = self.node_text(s, source_bytes).strip("'\"")
                        all_names.add(name)

        for node in self.walk_nodes(root, ["function_definition"]):
            if node.parent and node.parent.type == "module":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = self.node_text(name_node, source_bytes)
                    if not all_names or name in all_names:
                        exports.append(Export(
                            name=name, kind="function",
                            signature=self._func_sig(node, source_bytes),
                            line=node.start_point[0] + 1,
                        ))

        for node in self.walk_nodes(root, ["class_definition"]):
            if node.parent and node.parent.type == "module":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = self.node_text(name_node, source_bytes)
                    if not all_names or name in all_names:
                        exports.append(Export(
                            name=name, kind="class",
                            signature=name,
                            line=node.start_point[0] + 1,
                        ))

        return exports

    def extract_definitions(self, root: Node, source_bytes: bytes) -> list[Definition]:
        defs: list[Definition] = []

        for node in self.walk_nodes(root, ["function_definition"]):
            name_node = node.child_by_field_name("name")
            if not name_node:
                continue

            parent = None
            if (node.parent and node.parent.type == "block"
                    and node.parent.parent
                    and node.parent.parent.type == "class_definition"):
                class_name = node.parent.parent.child_by_field_name("name")
                if class_name:
                    parent = self.node_text(class_name, source_bytes)

            defs.append(Definition(
                name=self.node_text(name_node, source_bytes),
                kind="method" if parent else "function",
                signature=self._func_sig(node, source_bytes),
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                parent=parent,
            ))

        for node in self.walk_nodes(root, ["class_definition"]):
            name_node = node.child_by_field_name("name")
            if name_node:
                defs.append(Definition(
                    name=self.node_text(name_node, source_bytes),
                    kind="class",
                    signature=self.node_text(name_node, source_bytes),
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                ))

        return defs

    def extract_calls(self, root: Node, source_bytes: bytes) -> list[Call]:
        calls: list[Call] = []

        for node in self.walk_nodes(root, ["call"]):
            fn = node.child_by_field_name("function")
            if fn is None:
                continue

            parent_def = self.find_enclosing_function(node, source_bytes)

            if fn.type == "identifier":
                calls.append(Call(callee=self.node_text(fn, source_bytes),
                                  line=node.start_point[0] + 1, parent_def=parent_def))
            elif fn.type == "attribute":
                obj = fn.child_by_field_name("object")
                attr = fn.child_by_field_name("attribute")
                if obj and attr:
                    calls.append(Call(
                        callee=f"{self.node_text(obj, source_bytes)}.{self.node_text(attr, source_bytes)}",
                        line=node.start_point[0] + 1, parent_def=parent_def,
                    ))

        return calls

    def _func_sig(self, node: Node, source_bytes: bytes) -> str:
        name = node.child_by_field_name("name")
        params = node.child_by_field_name("parameters")
        ret = node.child_by_field_name("return_type")
        sig = self.node_text(name, source_bytes) if name else ""
        if params:
            sig += self.node_text(params, source_bytes)
        if ret:
            sig += " -> " + self.node_text(ret, source_bytes)
        return sig
