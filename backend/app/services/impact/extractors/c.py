"""C / C++ extractor — handles .c .h .cpp .cc .hpp files."""
from __future__ import annotations

from tree_sitter import Node

from .base import BaseExtractor, Call, Definition, Export, Import


class CExtractor(BaseExtractor):
    language = "c"  # overridden at runtime for C++

    def extract_imports(self, root: Node, source_bytes: bytes) -> list[Import]:
        imports: list[Import] = []

        for node in self.walk_nodes(root, ["preproc_include"]):
            path_node = node.child_by_field_name("path")
            if path_node is None:
                continue
            raw = self.node_text(path_node, source_bytes)
            path = raw.strip('"<>')
            imports.append(Import(
                source=path,
                symbols=[],      # C includes bring everything in
                is_wildcard=True,
                line=node.start_point[0] + 1,
            ))

        return imports

    def extract_exports(self, root: Node, source_bytes: bytes) -> list[Export]:
        # Anything at file scope not marked 'static'
        exports: list[Export] = []

        for node in self.walk_nodes(root, ["function_definition", "declaration"]):
            # Top-level only
            if node.parent and node.parent.type not in ("translation_unit",):
                continue

            # Skip 'static' (file-private)
            for child in node.children:
                if child.type == "storage_class_specifier":
                    if "static" in self.node_text(child, source_bytes):
                        break
            else:
                declarator = self._find_function_declarator(node)
                if declarator:
                    name_node = self.find_child(declarator, "identifier")
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

        for node in self.walk_nodes(root, ["function_definition"]):
            declarator = self._find_function_declarator(node)
            if not declarator:
                continue
            name_node = self.find_child(declarator, "identifier")
            if not name_node:
                continue

            defs.append(Definition(
                name=self.node_text(name_node, source_bytes),
                kind="function",
                signature=self._func_sig(node, source_bytes),
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
            ))

        # C++ class definitions
        for node in self.walk_nodes(root, ["class_specifier", "struct_specifier"]):
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
            calls.append(Call(
                callee=self.node_text(fn, source_bytes),
                line=node.start_point[0] + 1,
                parent_def=parent_def,
            ))

        return calls

    def _find_function_declarator(self, node: Node) -> Node | None:
        for child in node.children:
            if child.type == "function_declarator":
                return child
            if child.type == "pointer_declarator":
                result = self._find_function_declarator(child)
                if result:
                    return result
        return None

    def _func_sig(self, node: Node, source_bytes: bytes) -> str:
        decl = self._find_function_declarator(node)
        if decl:
            return self.node_text(decl, source_bytes)
        return ""


class CppExtractor(CExtractor):
    language = "cpp"
