import tree_sitter
import tree_sitter_java
import tree_sitter_typescript as ts_ts
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import os
from app.core.neo4j_db import neo4j_db

from app.models.component import ProjectFile, ComponentDependency, Component
import uuid


@dataclass
class ImportInfo:
    source: str
    symbols: List[str]


@dataclass
class ExportInfo:
    name: str


@dataclass
class ParsedFile:
    imports: List[ImportInfo] = field(default_factory=list)
    exports: List[ExportInfo] = field(default_factory=list)
    definitions: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)


class TypeScriptExtractor:
    def __init__(self, content: bytes, tree: tree_sitter.Tree):
        self.content = content
        self.tree = tree
        self.root = tree.root_node

    def _get_text(self, node: tree_sitter.Node) -> str:
        return self.content[node.start_byte:node.end_byte].decode("utf8")

    def extract_imports(self) -> List[ImportInfo]:
        imports = []

        def traverse_imports(node: tree_sitter.Node):
            if node.type == 'import_statement':
                source = ""
                symbols = []
                for child in node.children:
                    if child.type == 'string':
                        source = self._get_text(child).strip("'\"")
                    elif child.type == 'import_clause':
                        for gchild in child.children:
                            if gchild.type == 'named_imports':
                                for spec in gchild.children:
                                    if spec.type == 'import_specifier':
                                        for s_child in spec.children:
                                            if s_child.type == 'identifier':
                                                symbols.append(self._get_text(s_child))
                            elif gchild.type == 'identifier':
                                symbols.append(self._get_text(gchild))
                if source:
                    imports.append(ImportInfo(source=source, symbols=symbols))
            else:
                for child in node.children:
                    traverse_imports(child)

        traverse_imports(self.root)
        return imports

    def extract_exports(self) -> List[ExportInfo]:
        exports = []

        def traverse_exports(node: tree_sitter.Node):
            if node.type == 'export_statement':
                for child in node.children:
                    if child.type in ('lexical_declaration', 'variable_declaration'):
                        for var_decl in child.children:
                            if var_decl.type == 'variable_declarator':
                                for v_child in var_decl.children:
                                    if v_child.type == 'identifier':
                                        exports.append(ExportInfo(name=self._get_text(v_child)))
                    elif child.type in ('function_declaration', 'class_declaration'):
                        for fn_child in child.children:
                            if fn_child.type in ('identifier', 'type_identifier'):
                                exports.append(ExportInfo(name=self._get_text(fn_child)))
                    elif child.type == 'export_clause':
                        for spec in child.children:
                            if spec.type == 'export_specifier':
                                for s_child in spec.children:
                                    if s_child.type == 'identifier':
                                        exports.append(ExportInfo(name=self._get_text(s_child)))
                                        break
            else:
                for child in node.children:
                    traverse_exports(child)

        traverse_exports(self.root)
        return exports

    def extract_definitions(self) -> List[str]:
        return []

    def extract_calls(self) -> List[str]:
        return []


# ─── BRAND NEW JAVA EXTRACTOR ────────────────────────────────────────────────
class JavaExtractor:
    def __init__(self, content: bytes, tree: tree_sitter.Tree):
        self.content = content
        self.tree = tree
        self.root = tree.root_node

    def _get_text(self, node: tree_sitter.Node) -> str:
        return self.content[node.start_byte:node.end_byte].decode("utf8")

    def extract_imports(self) -> List[ImportInfo]:
        imports = []

        def traverse_imports(node: tree_sitter.Node):
            if node.type == 'import_declaration':
                # Grab the actual import path (e.g., java.util.List)
                text = self._get_text(node).replace('import ', '').replace(';', '').strip()
                # Use the last part of the path as the symbol
                symbol = text.split('.')[-1]
                imports.append(ImportInfo(source=text, symbols=[symbol]))
            else:
                for child in node.children:
                    traverse_imports(child)

        traverse_imports(self.root)
        return imports

    def extract_exports(self) -> List[ExportInfo]:
        exports = []

        def traverse_exports(node: tree_sitter.Node):
            # In Java, classes and interfaces act as exported modules
            if node.type in ['class_declaration', 'interface_declaration', 'enum_declaration']:
                for child in node.children:
                    if child.type == 'identifier':
                        exports.append(ExportInfo(name=self._get_text(child)))
                        break

            for child in node.children:
                traverse_exports(child)

        traverse_exports(self.root)
        return exports

    def extract_definitions(self) -> List[str]:
        return []

    def extract_calls(self) -> List[str]:
        return []


# ─────────────────────────────────────────────────────────────────────────────


def parse_file(file_path: str, content: str) -> ParsedFile:
    is_java = file_path.endswith('.java')

    # Dynamically select language grammar
    if is_java:
        lang = tree_sitter.Language(tree_sitter_java.language())
    else:
        lang = tree_sitter.Language(ts_ts.language_typescript())

    parser = tree_sitter.Parser()
    try:
        parser.set_language(lang)
    except Exception:
        parser.language = lang

    content_bytes = content.encode("utf8")
    tree = parser.parse(content_bytes)

    # Route to the correct Extractor
    if is_java:
        extractor = JavaExtractor(content_bytes, tree)
    else:
        extractor = TypeScriptExtractor(content_bytes, tree)

    return ParsedFile(
        imports=extractor.extract_imports(),
        exports=extractor.extract_exports(),
        definitions=extractor.extract_definitions(),
        calls=extractor.extract_calls()
    )


async def build_dependency_graph(project_id: str, db: AsyncSession):
    res = await db.execute(
        select(ProjectFile)
        .where(ProjectFile.project_id == project_id)
        .where(ProjectFile.parsed_symbols != None)
    )
    files = res.scalars().all()

    export_index = {}
    path_to_file = {}

    for f in files:
        norm_path = os.path.normpath(f.path)
        path_to_file[norm_path] = f

        symbols = f.parsed_symbols or {}
        exports = symbols.get("exports", [])
        for ex in exports:
            ex_name = ex.get("name") if isinstance(ex, dict) else ex
            export_index[ex_name] = f

    deps_to_create = []
    seen_deps = set()

    for src_file in files:
        if not src_file.component_id:
            continue

        imports = (src_file.parsed_symbols or {}).get("imports", [])

        for imp in imports:
            source_req = imp.get("source")
            if not source_req:
                continue

            target_f = None

            # 1. Try resolving relative paths (TypeScript style)
            if source_req.startswith("."):
                base_dir = os.path.dirname(src_file.path)
                resolved_base = os.path.normpath(os.path.join(base_dir, source_req))
                for ext in [".ts", ".tsx", ".js", ".jsx"]:
                    cand = f"{resolved_base}{ext}"
                    if cand in path_to_file:
                        target_f = path_to_file[cand]
                        break

            # 2. Try resolving by symbol mapping (Java style)
            if not target_f:
                symbols_req = imp.get("symbols", [])
                for s in symbols_req:
                    if s in export_index:
                        target_f = export_index[s]
                        break

            if target_f and target_f.component_id and target_f.component_id != src_file.component_id:
                dep_key = (src_file.component_id, target_f.component_id)
                if dep_key not in seen_deps:
                    seen_deps.add(dep_key)
                    deps_to_create.append(
                        ComponentDependency(
                            project_id=project_id,
                            source_component_id=src_file.component_id,
                            target_component_id=target_f.component_id,
                            dependency_type="import",
                            confidence=1.0,
                            symbols=imp.get("symbols", []),
                            detection_method="parser"
                        )
                    )

    for d in deps_to_create:
        db.add(d)

    await db.commit()

    # ─── DYNAMIC NEO4J INGESTION ─────────────────────────────────────────────
    nodes = []
    relations = []

    for f in files:
        file_id = f.path

        # Make sure the UI knows if it's Java or TS
        lang_str = "java" if file_id.endswith(".java") else "typescript"
        nodes.append({"id": file_id, "type": "FILE", "language": lang_str})

        symbols = f.parsed_symbols or {}

        for ex in symbols.get("exports", []):
            ex_name = ex.get("name") if isinstance(ex, dict) else ex
            node_id = f"{file_id}::{ex_name}"
            nodes.append({"id": node_id, "type": "EXPORT", "language": lang_str})
            relations.append({"from": file_id, "to": node_id, "type": "CONTAINS"})

        for imp in symbols.get("imports", []):
            target_module = imp.get("source")
            if target_module:
                nodes.append({"id": target_module, "type": "MODULE", "language": "unknown"})
                relations.append({"from": file_id, "to": target_module, "type": "IMPORTS"})

    unique_nodes = list({n["id"]: n for n in nodes}.values())

    try:
        with neo4j_db.get_session() as session:
            session.run("""
                UNWIND $nodes AS n
                MERGE (e:CodeNode {id: n.id, project_id: $project_id})
                SET e.type = n.type, e.language = n.language
            """, nodes=unique_nodes, project_id=project_id)

            session.run("""
                UNWIND $rels AS r
                MATCH (source:CodeNode {id: r.from, project_id: $project_id})
                MATCH (target:CodeNode {id: r.to})
                MERGE (source)-[rel:DEPENDS_ON]->(target)
                SET rel.type = r.type
            """, rels=relations, project_id=project_id)
        print(f"Graph Built! Saved {len(unique_nodes)} nodes and {len(relations)} relations to Neo4j.")
    except Exception as e:
        print(f"Neo4j ingestion error: {e}")