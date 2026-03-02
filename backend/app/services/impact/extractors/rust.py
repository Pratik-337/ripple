"""Rust extractor — handles .rs files."""
from __future__ import annotations

from tree_sitter import Node

from .base import BaseExtractor, Call, Definition, Export, Import


class RustExtractor(BaseExtractor):
    language = "rust"

    def extract_imports(self, root: Node, source_bytes: bytes) -> list[Import]:
        imports: list[Import] = []

        for node in self.walk_nodes(root, ["use_declaration"]):
            path_text = self.node_text(node, source_bytes)
            path_text = path_text.replace("use ", "").rstrip(";").strip()
            symbols = self._extract_use_tree_symbols(node, source_bytes)
            imports.append(Import(
                source=path_text, symbols=symbols,
                line=node.start_point[0] + 1,
            ))

        return imports

    def _extract_use_tree_symbols(self, node: Node, source_bytes: bytes) -> list[str]:
        symbols: list[str] = []
        for child in self.walk_nodes(node, ["identifier"]):
            text = self.node_text(child, source_bytes)
            if text not in ("use", "pub", "crate", "super", "self"):
                symbols.append(text)
        return symbols

    def extract_exports(self, root: Node, source_bytes: bytes) -> list[Export]:
        exports: list[Export] = []

        PUB_NODE_TYPES = [
            "function_item", "struct_item", "enum_item",
            "trait_item", "type_item",
        ]

        for node in self.walk_nodes(root, PUB_NODE_TYPES):
            vis = node.child_by_field_name("visibility")
            if vis is None:
                continue
            if "pub" not in self.node_text(vis, source_bytes):
                continue
            name_node = node.child_by_field_name("name")
            if not name_node:
                continue

            kind_map = {
                "function_item": "function",
                "struct_item": "class",
                "enum_item": "type",
                "trait_item": "type",
                "type_item": "type",
            }

            exports.append(Export(
                name=self.node_text(name_node, source_bytes),
                kind=kind_map.get(node.type, "variable"),
                signature=self.node_text(name_node, source_bytes),
                line=node.start_point[0] + 1,
            ))

        return exports

    def extract_definitions(self, root: Node, source_bytes: bytes) -> list[Definition]:
        defs: list[Definition] = []

        for node in self.walk_nodes(root, ["function_item"]):
            name_node = node.child_by_field_name("name")
            if not name_node:
                continue
            parent = self._find_impl_type(node, source_bytes)
            defs.append(Definition(
                name=self.node_text(name_node, source_bytes),
                kind="method" if parent else "function",
                signature=self._func_sig(node, source_bytes),
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                parent=parent,
            ))

        for node in self.walk_nodes(root, ["struct_item", "enum_item"]):
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

        for node in self.walk_nodes(root, ["call_expression"]):
            fn = node.child_by_field_name("function")
            if fn is None:
                continue
            parent_def = self.find_enclosing_function(node, source_bytes)
            if fn.type in ("identifier", "scoped_identifier"):
                calls.append(Call(callee=self.node_text(fn, source_bytes),
                                  line=node.start_point[0] + 1, parent_def=parent_def))
            elif fn.type == "field_expression":
                obj = fn.child_by_field_name("value")
                field_ = fn.child_by_field_name("field")
                if obj and field_:
                    calls.append(Call(
                        callee=f"{self.node_text(obj, source_bytes)}.{self.node_text(field_, source_bytes)}",
                        line=node.start_point[0] + 1, parent_def=parent_def,
                    ))

        return calls

    def _func_sig(self, node: Node, source_bytes: bytes) -> str:
        name = node.child_by_field_name("name")
        params = node.child_by_field_name("parameters")
        ret = node.child_by_field_name("return_type")
        sig = "fn " + (self.node_text(name, source_bytes) if name else "")
        if params:
            sig += self.node_text(params, source_bytes)
        if ret:
            sig += " -> " + self.node_text(ret, source_bytes)
        return sig

    def _find_impl_type(self, node: Node, source_bytes: bytes) -> str | None:
        current = node.parent
        while current:
            if current.type == "impl_item":
                type_node = current.child_by_field_name("type")
                if type_node:
                    return self.node_text(type_node, source_bytes)
            current = current.parent
        return None
