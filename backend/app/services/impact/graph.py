"""
Dependency graph builder and impact analysis engine.
Translates ParsedFile imports/exports into database ComponentDependency edges,
and queries those edges to find affected files and components.
"""
import os
from collections import defaultdict
from typing import Any

from app.models.component import ComponentDependency
from app.services.impact.extractors.base import ParsedFile


def build_dependency_graph(
    project_id: str,
    parsed_files: list[ParsedFile],
    file_to_component_id: dict[str, str]
) -> list[ComponentDependency]:
    """
    Analyzes a list of ParsedFiles and their component mappings,
    resolving imports to build a list of ComponentDependency edges.
    """
    # Index: export name -> list of ParsedFiles that export it
    export_index: dict[str, list[ParsedFile]] = defaultdict(list)
    for pf in parsed_files:
        for ex in pf.exports:
            export_index[ex.name].append(pf)

    # Index: absolute file path -> ParsedFile
    file_index: dict[str, ParsedFile] = {pf.path: pf for pf in parsed_files}

    edges_data: list[dict[str, Any]] = []

    for pf in parsed_files:
        source_component_id = file_to_component_id.get(pf.path)
        if not source_component_id:
            continue

        for imp in pf.imports:
            resolved_path = resolve_import_path(imp.source, pf.path, set(file_index.keys()))
            target_file = file_index.get(resolved_path) if resolved_path else None

            if not target_file:
                continue  # External library or unmapped file

            target_component_id = file_to_component_id.get(target_file.path)
            if not target_component_id:
                continue

            if source_component_id == target_component_id:
                continue  # Internal component dependency, ignore for component graph

            # Verify which symbols actually exist in the target
            confirmed_symbols = []
            if imp.symbols:
                target_export_names = {e.name for e in target_file.exports}
                confirmed_symbols = [s for s in imp.symbols if s in target_export_names]
                if not confirmed_symbols:
                    continue  # Imported symbols don't exist in target, skip edge
            
            # Note: if imp.symbols is empty (wildcard/side-effect), confirmed_symbols is empty

            edges_data.append({
                "project_id": project_id,
                "source_component_id": source_component_id,
                "target_component_id": target_component_id,
                "dependency_type": "import",
                "confidence": 1.0,
                "detection_method": "parser",
                "symbols": confirmed_symbols,
            })

    # Deduplicate edges between the same components, merging symbols
    merged_edges: dict[tuple[str, str], dict[str, Any]] = {}

    for edge in edges_data:
        key = (edge["source_component_id"], edge["target_component_id"])
        if key not in merged_edges:
            merged_edges[key] = edge.copy()
            merged_edges[key]["symbols"] = set(edge.get("symbols", []))
        else:
            merged_edges[key]["symbols"].update(edge.get("symbols", []))

    # Convert back to SQLAlchemy models
    models: list[ComponentDependency] = []
    for edge in merged_edges.values():
        models.append(ComponentDependency(
            project_id=edge["project_id"],
            source_component_id=edge["source_component_id"],
            target_component_id=edge["target_component_id"],
            dependency_type=edge["dependency_type"],
            confidence=edge["confidence"],
            detection_method=edge["detection_method"],
            symbols=list(edge["symbols"]),
        ))

    return models


def resolve_import_path(import_source: str, current_file_path: str, all_file_paths: set[str]) -> str | None:
    """
    Attempts to resolve a relative import path to an absolute path within the project.
    Returns None if it's an external library or cannot be resolved.
    """
    if not (import_source.startswith("./") or import_source.startswith("../")):
        # Absolute or package import (e.g. 'react', 'lodash')
        return None

    base_dir = os.path.dirname(current_file_path)
    # Normpath resolves "foo/../bar" into "bar"
    resolved_base = os.path.normpath(os.path.join(base_dir, import_source))
    
    # We must use forward slashes for internal consistency if the DB paths use them
    resolved_base = resolved_base.replace("\\", "/")

    # Try exact match first
    if resolved_base in all_file_paths:
        return resolved_base

    # Try common extensions
    extensions = [".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs", ".java", ".rb", ".cs", ".php"]
    for ext in extensions:
        candidate = f"{resolved_base}{ext}"
        if candidate in all_file_paths:
            return candidate

    # Try index files (Node.js resolution)
    for ext in extensions:
        candidate = f"{resolved_base}/index{ext}"
        if candidate in all_file_paths:
            return candidate

    return None


def find_affected_components(
    changed_component_id: str,
    changed_symbols: list[str],
    direct_dependencies: list[ComponentDependency],
    dependent_files_data: list[tuple[str, str, dict]] # (component_id, file_path, parsed_symbols_dict)
) -> list[dict[str, Any]]:
    """
    Finds exactly which files and components are affected by a change to specific symbols.
    
    Args:
        changed_component_id: ID of the component that was modified
        changed_symbols: List of export names that were modified
        direct_dependencies: SQLAlchemy objects where target_component_id == changed_component_id
        dependent_files_data: Raw data of files belonging to the source components in direct_dependencies
            Format: [(component_id, file_path, parsed_symbols_dict), ...]
            
    Returns:
        List of dicts containing the impacted component ID, file path, and which symbols matched.
    """
    # Map valid source components
    valid_source_component_ids = {dep.source_component_id for dep in direct_dependencies}
    
    affected = []

    for comp_id, file_path, symbols_dict in dependent_files_data:
        if comp_id not in valid_source_component_ids:
            continue

        # Convert raw dict from DB back to Import objects to reuse logic
        file_imports = [
            Import(**i) for i in symbols_dict.get("imports", [])
        ]

        # Check if this file imports any of the changed symbols
        matching = []
        for symbol in changed_symbols:
            for imp in file_imports:
                # Does this import resolve to our changed component? 
                # (In reality, we compare the symbol strings because we know the component edge exists)
                if imp.is_wildcard or not imp.symbols or symbol in imp.symbols:
                    matching.append(symbol)
                    break # found symbol in at least one import statement

        if matching:
            affected.append({
                "component_id": comp_id,
                "file_path": file_path,
                "matched_symbols": matching,
                "confidence": 1.0,
                "detection_method": "parser",
            })

    return affected
