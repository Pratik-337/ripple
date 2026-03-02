"""Go extractor — handles .go files. Exports by capitalisation convention."""
from __future__ import annotations

from tree_sitter import Node

from .base import BaseExtractor, Call, Definition, Export, Import


class GoExtractor(BaseExtractor):
    language = "go"

    def extract_imports(self, root: Node, source_bytes: bytes) -> list[Import]:
        imports: list[Import] = []

        for node in self.walk_nodes(root, ["import_spec"]):
            path_node = node.child_by_field_name("path")
            if path_node is None:
                continue
            path = self.node_text(path_node, source_bytes).strip('"')
            alias_node = node.child_by_field_name("name")
            alias = (self.node_text(alias_node, source_bytes)
                     if alias_node else path.split("/")[-1])
            imports.append(Import(
                source=path, symbols=[alias],
                line=node.start_point[0] + 1,
            ))

        return imports

    def extract_exports(self, root: Node, source_bytes: bytes) -> list[Export]:
        exports: list[Export] = []

        for node in self.walk_nodes(root, ["function_declaration", "method_declaration"]):
            name_node = node.child_by_field_name("name")
            if name_node is None:
                continue
            name = self.node_text(name_node, source_bytes)
            if name and name[0].isupper():
                exports.append(Export(
                    name=name, kind="function",
                    signature=self._func_sig(node, source_bytes),
                    line=node.start_point[0] + 1,
                ))

        for node in self.walk_nodes(root, ["type_declaration"]):
            for spec in self.children_of_type(node, "type_spec"):
                name_node = spec.child_by_field_name("name")
                if name_node:
                    name = self.node_text(name_node, source_bytes)
                    if name and name[0].isupper():
                        exports.append(Export(
                            name=name, kind="type",
                            signature=name, line=spec.start_point[0] + 1,
                        ))

        return exports

    def extract_definitions(self, root: Node, source_bytes: bytes) -> list[Definition]:
        defs: list[Definition] = []

        for node in self.walk_nodes(root, ["function_declaration"]):
            name_node = node.child_by_field_name("name")
            if name_node:
                defs.append(Definition(
                    name=self.node_text(name_node, source_bytes),
                    kind="function",
                    signature=self._func_sig(node, source_bytes),
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                ))

        for node in self.walk_nodes(root, ["method_declaration"]):
            name_node = node.child_by_field_name("name")
            receiver = node.child_by_field_name("receiver")
            parent = self._receiver_type(receiver, source_bytes) if receiver else None
            if name_node:
                defs.append(Definition(
                    name=self.node_text(name_node, source_bytes),
                    kind="method",
                    signature=self._func_sig(node, source_bytes),
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    parent=parent,
                ))

        return defs

    def extract_calls(self, root: Node, source_bytes: bytes) -> list[Call]:
        calls: list[Call] = []

        for node in self.walk_nodes(root, ["call_expression"]):
            fn = node.child_by_field_name("function")
            if fn is None:
                continue
            parent_def = self.find_enclosing_function(node, source_bytes)
            if fn.type == "identifier":
                calls.append(Call(callee=self.node_text(fn, source_bytes),
                                  line=node.start_point[0] + 1, parent_def=parent_def))
            elif fn.type == "selector_expression":
                obj = fn.child_by_field_name("operand")
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
        result = node.child_by_field_name("result")
        sig = self.node_text(name, source_bytes) if name else ""
        if params:
            sig += self.node_text(params, source_bytes)
        if result:
            sig += " " + self.node_text(result, source_bytes)
        return sig

    def _receiver_type(self, receiver_node: Node, source_bytes: bytes) -> str | None:
        for child in receiver_node.children:
            if child.type == "parameter_declaration":
                type_node = child.child_by_field_name("type")
                if type_node:
                    return self.node_text(type_node, source_bytes).lstrip("*")
        return None
