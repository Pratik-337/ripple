"""C# extractor — handles .cs files."""
from __future__ import annotations

from tree_sitter import Node

from .base import BaseExtractor, Call, Definition, Export, Import


class CSharpExtractor(BaseExtractor):
    language = "c_sharp"

    def extract_imports(self, root: Node, source_bytes: bytes) -> list[Import]:
        imports: list[Import] = []

        # using System.Collections.Generic;
        # using Auth = Company.Auth.Service;
        for node in self.walk_nodes(root, ["using_directive"]):
            name_node = node.child_by_field_name("name")
            alias_node = node.child_by_field_name("alias")
            if name_node is None:
                continue

            path = self.node_text(name_node, source_bytes)
            parts = path.split(".")
            symbol = self.node_text(alias_node, source_bytes) if alias_node else parts[-1]
            package = ".".join(parts[:-1]) if not alias_node else path

            imports.append(Import(
                source=package,
                symbols=[symbol],
                line=node.start_point[0] + 1,
            ))

        return imports

    def extract_exports(self, root: Node, source_bytes: bytes) -> list[Export]:
        exports: list[Export] = []

        EXPORT_TYPES = [
            "method_declaration", "class_declaration",
            "interface_declaration", "property_declaration",
        ]

        kind_map = {
            "method_declaration": "function",
            "class_declaration": "class",
            "interface_declaration": "type",
            "property_declaration": "variable",
        }

        for node in self.walk_nodes(root, EXPORT_TYPES):
            # Check for public modifier
            has_public = False
            for child in node.children:
                if child.type == "modifier" and "public" in self.node_text(child, source_bytes):
                    has_public = True
                    break
            if not has_public:
                continue

            name_node = node.child_by_field_name("name")
            if name_node is None:
                continue

            exports.append(Export(
                name=self.node_text(name_node, source_bytes),
                kind=kind_map.get(node.type, "variable"),
                signature=self._member_sig(node, source_bytes),
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
                signature=self._member_sig(node, source_bytes),
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

        for node in self.walk_nodes(root, ["invocation_expression"]):
            fn = node.child_by_field_name("function")
            if fn is None:
                continue
            parent_def = self.find_enclosing_function(node, source_bytes)
            calls.append(Call(
                callee=self.node_text(fn, source_bytes),
                line=node.start_point[0] + 1,
                parent_def=parent_def,
            ))

        return calls

    def _member_sig(self, node: Node, source_bytes: bytes) -> str:
        ret = node.child_by_field_name("type")
        name = node.child_by_field_name("name")
        params = node.child_by_field_name("parameter_list")
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
            if current.type == "declaration_list":
                cls = current.parent
                if cls and cls.type in ("class_declaration", "interface_declaration"):
                    name = cls.child_by_field_name("name")
                    if name:
                        return self.node_text(name, source_bytes)
            current = current.parent
        return None
