"""Ruby extractor — handles .rb files."""
from __future__ import annotations

from tree_sitter import Node

from .base import BaseExtractor, Call, Definition, Export, Import


class RubyExtractor(BaseExtractor):
    language = "ruby"

    def extract_imports(self, root: Node, source_bytes: bytes) -> list[Import]:
        imports: list[Import] = []

        REQUIRE_METHODS = {"require", "require_relative", "load", "autoload"}
        MIXIN_METHODS = {"include", "extend", "prepend"}

        for node in self.walk_nodes(root, ["call"]):
            method_node = node.child_by_field_name("method")
            if method_node is None:
                continue
            method_str = self.node_text(method_node, source_bytes)

            if method_str in REQUIRE_METHODS:
                args = node.child_by_field_name("arguments")
                if args:
                    for s in self.children_of_type(args, "string"):
                        content = self.find_child(s, "string_content")
                        path = self.node_text(content, source_bytes) if content else self.node_text(s, source_bytes).strip("'\"")
                        imports.append(Import(source=path, line=node.start_point[0] + 1))

            elif method_str in MIXIN_METHODS:
                args = node.child_by_field_name("arguments")
                if args:
                    for const_node in self.children_of_type(args, "constant"):
                        name = self.node_text(const_node, source_bytes)
                        imports.append(Import(
                            source=name, symbols=[name],
                            line=node.start_point[0] + 1,
                        ))

        return imports

    def extract_exports(self, root: Node, source_bytes: bytes) -> list[Export]:
        exports: list[Export] = []

        for node in self.walk_nodes(root, ["method", "singleton_method"]):
            name_node = node.child_by_field_name("name")
            if name_node:
                exports.append(Export(
                    name=self.node_text(name_node, source_bytes),
                    kind="function",
                    signature=self._method_sig(node, source_bytes),
                    line=node.start_point[0] + 1,
                ))

        for node in self.walk_nodes(root, ["module", "class"]):
            name_node = node.child_by_field_name("name")
            if name_node:
                exports.append(Export(
                    name=self.node_text(name_node, source_bytes),
                    kind="class",
                    signature=self.node_text(name_node, source_bytes),
                    line=node.start_point[0] + 1,
                ))

        return exports

    def extract_definitions(self, root: Node, source_bytes: bytes) -> list[Definition]:
        defs: list[Definition] = []

        for node in self.walk_nodes(root, ["method", "singleton_method"]):
            name_node = node.child_by_field_name("name")
            if not name_node:
                continue
            parent = self.find_enclosing_class(node, source_bytes)
            defs.append(Definition(
                name=self.node_text(name_node, source_bytes),
                kind="method" if parent else "function",
                signature=self._method_sig(node, source_bytes),
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                parent=parent,
            ))

        for node in self.walk_nodes(root, ["class", "module"]):
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
            method_node = node.child_by_field_name("method")
            receiver_node = node.child_by_field_name("receiver")
            if method_node:
                callee = self.node_text(method_node, source_bytes)
                if receiver_node:
                    callee = f"{self.node_text(receiver_node, source_bytes)}.{callee}"
                calls.append(Call(
                    callee=callee,
                    line=node.start_point[0] + 1,
                    parent_def=self.find_enclosing_function(node, source_bytes),
                ))

        return calls

    def _method_sig(self, node: Node, source_bytes: bytes) -> str:
        name = node.child_by_field_name("name")
        params = node.child_by_field_name("parameters")
        sig = "def " + (self.node_text(name, source_bytes) if name else "")
        if params:
            sig += self.node_text(params, source_bytes)
        return sig
