"""
Base data classes and abstract extractor that all language extractors inherit.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tree_sitter import Node


# ── Data classes (the unified symbol format) ───────────────────────────────────

@dataclass
class Import:
    source: str
    symbols: list[str] = field(default_factory=list)
    is_default: bool = False
    is_wildcard: bool = False
    line: int = 0


@dataclass
class Export:
    name: str
    kind: str  # "function" | "class" | "type" | "variable" | "default"
    signature: str = ""
    line: int = 0


@dataclass
class Definition:
    name: str
    kind: str  # "function" | "class" | "method" | "interface" | "type" | "variable"
    signature: str = ""
    start_line: int = 0
    end_line: int = 0
    parent: str | None = None


@dataclass
class Call:
    callee: str
    line: int = 0
    parent_def: str | None = None


@dataclass
class ParsedFile:
    path: str
    language: str
    imports: list[Import] = field(default_factory=list)
    exports: list[Export] = field(default_factory=list)
    definitions: list[Definition] = field(default_factory=list)
    calls: list[Call] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Converts to JSON-serializable dict for JSONB storage in project_files."""
        return {
            "path": self.path,
            "language": self.language,
            "imports": [
                {"source": i.source, "symbols": i.symbols,
                 "is_default": i.is_default, "is_wildcard": i.is_wildcard, "line": i.line}
                for i in self.imports
            ],
            "exports": [
                {"name": e.name, "kind": e.kind, "signature": e.signature, "line": e.line}
                for e in self.exports
            ],
            "definitions": [
                {"name": d.name, "kind": d.kind, "signature": d.signature,
                 "start_line": d.start_line, "end_line": d.end_line, "parent": d.parent}
                for d in self.definitions
            ],
            "calls": [
                {"callee": c.callee, "line": c.line, "parent_def": c.parent_def}
                for c in self.calls
            ],
        }


# ── Base extractor ─────────────────────────────────────────────────────────────

class BaseExtractor(ABC):
    language: str = ""

    def extract(self, root: Node, source_bytes: bytes, file_path: str) -> ParsedFile:
        result = ParsedFile(path=file_path, language=self.language)
        try:
            result.imports = self.extract_imports(root, source_bytes)
        except Exception:
            pass
        try:
            result.exports = self.extract_exports(root, source_bytes)
        except Exception:
            pass
        try:
            result.definitions = self.extract_definitions(root, source_bytes)
        except Exception:
            pass
        try:
            result.calls = self.extract_calls(root, source_bytes)
        except Exception:
            pass
        return result

    # ── Shared utilities ───────────────────────────────────────────────────────

    def node_text(self, node: Node, source_bytes: bytes) -> str:
        return source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

    def walk_nodes(self, root: Node, target_types: set[str] | list[str]):
        """Iterative DFS yielding all nodes whose type is in target_types."""
        target_types = set(target_types)
        stack = [root]
        while stack:
            node = stack.pop()
            if node.type in target_types:
                yield node
            # reversed so left-to-right order is preserved
            for child in reversed(node.children):
                stack.append(child)

    def children_of_type(self, node: Node, *types: str) -> list[Node]:
        """Returns direct children matching any of the given type names."""
        return [c for c in node.children if c.type in types]

    def find_child(self, node: Node, *types: str) -> Node | None:
        """Returns first direct child matching any of the given type names."""
        for c in node.children:
            if c.type in types:
                return c
        return None

    def find_enclosing_function(self, node: Node, source_bytes: bytes) -> str | None:
        """Walk up the tree to find the name of the nearest enclosing function."""
        FUNCTION_TYPES = {
            "function_declaration", "method_definition", "arrow_function",
            "function_expression", "function_definition", "method_declaration",
            "function_item",  # Rust
        }
        current = node.parent
        while current is not None:
            if current.type in FUNCTION_TYPES:
                name_node = current.child_by_field_name("name")
                if name_node:
                    return self.node_text(name_node, source_bytes)
            current = current.parent
        return None

    def find_enclosing_class(self, node: Node, source_bytes: bytes) -> str | None:
        """Walk up the tree to find the name of the nearest enclosing class."""
        CLASS_TYPES = {
            "class_declaration", "class_definition", "class_body",
            "struct_item", "impl_item",
        }
        current = node.parent
        while current is not None:
            if current.type in CLASS_TYPES:
                name_node = current.child_by_field_name("name")
                if name_node:
                    return self.node_text(name_node, source_bytes)
                # class_body → parent is the actual class decl
                if current.type == "class_body" and current.parent:
                    parent_name = current.parent.child_by_field_name("name")
                    if parent_name:
                        return self.node_text(parent_name, source_bytes)
            current = current.parent
        return None

    # ── Abstract interface ─────────────────────────────────────────────────────

    @abstractmethod
    def extract_imports(self, root: Node, source_bytes: bytes) -> list[Import]: ...

    @abstractmethod
    def extract_exports(self, root: Node, source_bytes: bytes) -> list[Export]: ...

    @abstractmethod
    def extract_definitions(self, root: Node, source_bytes: bytes) -> list[Definition]: ...

    @abstractmethod
    def extract_calls(self, root: Node, source_bytes: bytes) -> list[Call]: ...
