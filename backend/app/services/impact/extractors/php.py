"""PHP extractor — handles .php files."""
from __future__ import annotations

from tree_sitter import Node

from .base import BaseExtractor, Call, Definition, Export, Import


class PHPExtractor(BaseExtractor):
    language = "php"

    def extract_imports(self, root: Node, source_bytes: bytes) -> list[Import]:
        imports: list[Import] = []

        # require_once 'file.php' / include 'file.php'
        for node in self.walk_nodes(root, [
            "include_expression", "include_once_expression",
            "require_expression", "require_once_expression",
        ]):
            # Last named child is the path
            for child in reversed(node.children):
                if child.type in ("string", "encapsed_string"):
                    content = self.find_child(child, "string_value", "string_content")
                    path = self.node_text(content, source_bytes) if content else self.node_text(child, source_bytes).strip("'\"")
                    imports.append(Import(source=path, line=node.start_point[0] + 1))
                    break

        # use Namespace\ClassName;
        # use Namespace\ClassName as Alias;
        for node in self.walk_nodes(root, ["use_declaration"]):
            for clause in self.children_of_type(node, "use_clause"):
                name_node = self.find_child(clause, "qualified_name", "name")
                alias_node = clause.child_by_field_name("alias")
                if name_node:
                    name_text = self.node_text(name_node, source_bytes)
                    symbol = (self.node_text(alias_node, source_bytes)
                              if alias_node else name_text.split("\\")[-1])
                    imports.append(Import(
                        source=name_text,
                        symbols=[symbol],
                        line=clause.start_point[0] + 1,
                    ))

        return imports

    def extract_exports(self, root: Node, source_bytes: bytes) -> list[Export]:
        exports: list[Export] = []

        # Top-level functions and classes are publicly accessible
        for node in self.walk_nodes(root, ["function_definition"]):
            name_node = node.child_by_field_name("name")
            if name_node:
                exports.append(Export(
                    name=self.node_text(name_node, source_bytes),
                    kind="function",
                    signature=self._func_sig(node, source_bytes),
                    line=node.start_point[0] + 1,
                ))

        for node in self.walk_nodes(root, ["class_declaration", "interface_declaration"]):
            name_node = node.child_by_field_name("name")
            if name_node:
                exports.append(Export(
                    name=self.node_text(name_node, source_bytes),
                    kind="class" if node.type == "class_declaration" else "type",
                    signature=self.node_text(name_node, source_bytes),
                    line=node.start_point[0] + 1,
                ))

        # Public methods
        for node in self.walk_nodes(root, ["method_declaration"]):
            mods = self.find_child(node, "modifier")
            if mods and "public" in self.node_text(mods, source_bytes):
                name_node = node.child_by_field_name("name")
                if name_node:
                    exports.append(Export(
                        name=self.node_text(name_node, source_bytes),
                        kind="function",
                        signature=self._func_sig(node, source_bytes),
                        line=node.start_point[0] + 1,
                    ))

        return exports

    def extract_definitions(self, root: Node, source_bytes: bytes) -> list[Definition]:
        defs: list[Definition] = []

        for node in self.walk_nodes(root, ["function_definition", "method_declaration"]):
            name_node = node.child_by_field_name("name")
            if not name_node:
                continue
            parent = self.find_enclosing_class(node, source_bytes)
            defs.append(Definition(
                name=self.node_text(name_node, source_bytes),
                kind="method" if parent else "function",
                signature=self._func_sig(node, source_bytes),
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

        for node in self.walk_nodes(root, ["function_call_expression"]):
            fn = node.child_by_field_name("function")
            if fn:
                calls.append(Call(
                    callee=self.node_text(fn, source_bytes),
                    line=node.start_point[0] + 1,
                    parent_def=self.find_enclosing_function(node, source_bytes),
                ))

        for node in self.walk_nodes(root, ["member_call_expression"]):
            obj = node.child_by_field_name("object")
            name = node.child_by_field_name("name")
            if obj and name:
                calls.append(Call(
                    callee=f"{self.node_text(obj, source_bytes)}.{self.node_text(name, source_bytes)}",
                    line=node.start_point[0] + 1,
                    parent_def=self.find_enclosing_function(node, source_bytes),
                ))

        return calls

    def _func_sig(self, node: Node, source_bytes: bytes) -> str:
        name = node.child_by_field_name("name")
        params = node.child_by_field_name("parameters")
        sig = self.node_text(name, source_bytes) if name else ""
        if params:
            sig += self.node_text(params, source_bytes)
        return sig
