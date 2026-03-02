"""
TypeScript / JavaScript extractor.
Handles: .ts  .tsx  .js  .jsx  .mjs
Uses tree-sitter-typescript grammar which is a strict superset of JS.
Node type names verified against tree-sitter-typescript grammar 0.23.x.
"""
from __future__ import annotations

from tree_sitter import Node

from .base import BaseExtractor, Call, Definition, Export, Import


class TypeScriptExtractor(BaseExtractor):
    language = "typescript"

    # ── Imports ───────────────────────────────────────────────────────────────

    def extract_imports(self, root: Node, source_bytes: bytes) -> list[Import]:
        imports: list[Import] = []

        # ES module imports: import { A, B } from './mod'
        for node in self.walk_nodes(root, ["import_statement"]):
            source_node = node.child_by_field_name("source")
            if source_node is None:
                continue
            source_path = self.node_text(source_node, source_bytes).strip("'\"")

            imp = Import(source=source_path, line=node.start_point[0] + 1)
            clause = self.find_child(node, "import_clause")

            if clause is None:
                # Side-effect import: import './styles.css'
                imports.append(imp)
                continue

            # Default import: import Foo from './foo'
            default_id = clause.child_by_field_name("name")
            if default_id:
                imp.is_default = True
                imp.symbols.append(self.node_text(default_id, source_bytes))

            # Namespace import: import * as Foo from './foo'
            ns = self.find_child(clause, "namespace_import")
            if ns:
                imp.is_wildcard = True
                alias = self.find_child(ns, "identifier")
                if alias:
                    imp.symbols.append(self.node_text(alias, source_bytes))

            # Named imports: import { A, B as C } from './foo'
            named = self.find_child(clause, "named_imports")
            if named:
                for spec in self.children_of_type(named, "import_specifier"):
                    name_node = spec.child_by_field_name("name")
                    if name_node:
                        imp.symbols.append(self.node_text(name_node, source_bytes))

            imports.append(imp)

        # CommonJS require(): const { A } = require('./mod')
        for node in self.walk_nodes(root, ["call_expression"]):
            fn = node.child_by_field_name("function")
            args = node.child_by_field_name("arguments")
            if fn is None or args is None:
                continue
            if self.node_text(fn, source_bytes) != "require":
                continue
            # First real argument (children[0]= '(', children[1]=arg, ...)
            str_nodes = self.children_of_type(args, "string", "template_string")
            for sn in str_nodes:
                path = self.node_text(sn, source_bytes).strip("'\"`")
                imports.append(Import(source=path, line=node.start_point[0] + 1))
                break

        return imports

    # ── Exports ───────────────────────────────────────────────────────────────

    def extract_exports(self, root: Node, source_bytes: bytes) -> list[Export]:
        exports: list[Export] = []

        for node in self.walk_nodes(root, ["export_statement"]):
            decl = node.child_by_field_name("declaration")

            if decl is None:
                # export { A, B as C }
                clause = self.find_child(node, "export_clause")
                if clause:
                    for spec in self.children_of_type(clause, "export_specifier"):
                        name_node = spec.child_by_field_name("name")
                        if name_node:
                            exports.append(Export(
                                name=self.node_text(name_node, source_bytes),
                                kind="variable",
                                signature=self.node_text(name_node, source_bytes),
                                line=spec.start_point[0] + 1,
                            ))
                # export default <expr>
                default_kw = self.find_child(node, "default")
                if default_kw:
                    # find the expression being exported
                    for c in node.children:
                        if c.type not in ("export", "default", "comment") and not c.is_named:
                            continue
                        if c.type in ("identifier", "function_declaration",
                                       "class_declaration", "arrow_function"):
                            name = "default"
                            if c.type in ("function_declaration", "class_declaration"):
                                n = c.child_by_field_name("name")
                                if n:
                                    name = self.node_text(n, source_bytes)
                            exports.append(Export(
                                name=name, kind="default",
                                signature=name, line=node.start_point[0] + 1,
                            ))
                            break
                continue

            t = decl.type
            if t == "function_declaration":
                name_node = decl.child_by_field_name("name")
                if name_node:
                    exports.append(Export(
                        name=self.node_text(name_node, source_bytes),
                        kind="function",
                        signature=self._function_signature(decl, source_bytes),
                        line=decl.start_point[0] + 1,
                    ))

            elif t == "class_declaration":
                name_node = decl.child_by_field_name("name")
                if name_node:
                    exports.append(Export(
                        name=self.node_text(name_node, source_bytes),
                        kind="class",
                        signature=self.node_text(name_node, source_bytes),
                        line=decl.start_point[0] + 1,
                    ))

            elif t in ("lexical_declaration", "variable_declaration"):
                for declarator in self.children_of_type(decl, "variable_declarator"):
                    name_node = declarator.child_by_field_name("name")
                    if name_node:
                        exports.append(Export(
                            name=self.node_text(name_node, source_bytes),
                            kind="variable",
                            signature=self.node_text(name_node, source_bytes),
                            line=declarator.start_point[0] + 1,
                        ))

            elif t in ("type_alias_declaration", "interface_declaration"):
                name_node = decl.child_by_field_name("name")
                if name_node:
                    exports.append(Export(
                        name=self.node_text(name_node, source_bytes),
                        kind="type",
                        signature=self.node_text(name_node, source_bytes),
                        line=decl.start_point[0] + 1,
                    ))

        return exports

    # ── Definitions ───────────────────────────────────────────────────────────

    def extract_definitions(self, root: Node, source_bytes: bytes) -> list[Definition]:
        defs: list[Definition] = []
        seen: set[tuple] = set()

        # Functions and methods
        for node in self.walk_nodes(root, [
            "function_declaration", "method_definition",
            "function_expression", "arrow_function",
        ]):
            name_node = node.child_by_field_name("name")
            if name_node is None:
                continue

            name = self.node_text(name_node, source_bytes)
            key = (name, node.start_point[0])
            if key in seen:
                continue
            seen.add(key)

            parent = None
            if node.type == "method_definition":
                parent = self._method_parent_class(node, source_bytes)

            defs.append(Definition(
                name=name,
                kind="method" if parent else "function",
                signature=self._function_signature(node, source_bytes),
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                parent=parent,
            ))

        # Classes
        for node in self.walk_nodes(root, ["class_declaration"]):
            name_node = node.child_by_field_name("name")
            if name_node is None:
                continue
            name = self.node_text(name_node, source_bytes)
            defs.append(Definition(
                name=name,
                kind="class",
                signature=name,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
            ))

        # Interfaces and type aliases
        for node in self.walk_nodes(root, ["interface_declaration", "type_alias_declaration"]):
            name_node = node.child_by_field_name("name")
            if name_node is None:
                continue
            defs.append(Definition(
                name=self.node_text(name_node, source_bytes),
                kind="interface" if node.type == "interface_declaration" else "type",
                signature=self.node_text(name_node, source_bytes),
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
            ))

        return defs

    # ── Calls ─────────────────────────────────────────────────────────────────

    def extract_calls(self, root: Node, source_bytes: bytes) -> list[Call]:
        calls: list[Call] = []

        for node in self.walk_nodes(root, ["call_expression"]):
            fn = node.child_by_field_name("function")
            if fn is None:
                continue

            parent_def = self.find_enclosing_function(node, source_bytes)

            if fn.type == "identifier":
                calls.append(Call(
                    callee=self.node_text(fn, source_bytes),
                    line=node.start_point[0] + 1,
                    parent_def=parent_def,
                ))
            elif fn.type == "member_expression":
                obj = fn.child_by_field_name("object")
                prop = fn.child_by_field_name("property")
                if obj and prop:
                    calls.append(Call(
                        callee=f"{self.node_text(obj, source_bytes)}.{self.node_text(prop, source_bytes)}",
                        line=node.start_point[0] + 1,
                        parent_def=parent_def,
                    ))

        return calls

    # ── Private helpers ───────────────────────────────────────────────────────

    def _function_signature(self, node: Node, source_bytes: bytes) -> str:
        name = node.child_by_field_name("name")
        params = node.child_by_field_name("parameters")
        return_type = node.child_by_field_name("return_type")

        sig = self.node_text(name, source_bytes) if name else ""
        if params:
            sig += self.node_text(params, source_bytes)
        if return_type:
            sig += ": " + self.node_text(return_type, source_bytes)
        return sig

    def _method_parent_class(self, method_node: Node, source_bytes: bytes) -> str | None:
        # method_definition → class_body → class_declaration
        body = method_node.parent
        if body is None or body.type != "class_body":
            return None
        cls = body.parent
        if cls is None:
            return None
        name_node = cls.child_by_field_name("name")
        return self.node_text(name_node, source_bytes) if name_node else None
