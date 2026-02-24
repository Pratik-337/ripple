from parser.core.diff_engine import find_changed_nodes
from pathlib import Path
import requests
import uuid
import json

from parser.core.ast_loader import parse_code
from parser.core.symbol_table import SymbolTable
from parser.core.impact import propagate_impact

from parser.language_registry import EXTENSION_MAP, TREE_SITTER_LANG, PARSER_MAP
from parser.analyzer import analyze_repository, AnalysisConfig

from parser.languages.java_parser import parse_java
from parser.languages.python_parser import parse_python
from parser.languages.javascript_parser import parse_javascript
from parser.languages.typescript_parser import parse_typescript
from parser.languages.c_parser import parse_c
from parser.languages.cpp_parser import parse_cpp
from parser.languages.go_parser import parse_go
from parser.languages.rust_parser import parse_rust
from parser.languages.php_parser import parse_php
from parser.languages.kotlin_parser import parse_kotlin

from parser.core.graph_builder import GraphBuilder
from parser.core.equivalence import build_cross_language_equivalence
from parser.core.api_linker import link_api_calls

PARSER_MAP.update({
    'JAVA': parse_java, 'PYTHON': parse_python, 'JAVASCRIPT': parse_javascript, 'TYPESCRIPT': parse_typescript,
    'C': parse_c, 'CPP': parse_cpp, 'GO': parse_go, 'RUST': parse_rust, 'PHP': parse_php, 'KOTLIN': parse_kotlin,
})

def analyze_changes(project_root: Path, change_id: str, changed_nodes: dict, changed_snippets: dict | None = None, changed_line_ranges: dict | None = None):
    """
    Analyzes multiple changed nodes and merges their impacts.
    changed_nodes: dict of {node_id: change_type}
    """
    builder = GraphBuilder()
    symbol_table = SymbolTable()
    config = AnalysisConfig(allowed_languages=list(PARSER_MAP.keys()), max_files=5000)
    analysis = analyze_repository(project_root, config)

    # Build (language, stem) -> relative path map for original_code extraction
    file_index = {}
    for d in analysis['details']:
        try:
            p = Path(d['path'])
            rel = p.relative_to(project_root)
        except Exception:
            rel = Path(d['path'])
        file_index[(d['language'], p.stem)] = str(rel)

    # --- PASS 1: DISCOVERY ---
    parsed_units = []
    for unit in analysis['details']:
        if unit['parse_error']: continue
        path = Path(unit['path'])
        language = EXTENSION_MAP.get(path.suffix.lower())
        if language in PARSER_MAP:
            code = path.read_text(encoding='utf8', errors='ignore')
            tree = parse_code(code, TREE_SITTER_LANG[language])
            PARSER_MAP[language](tree, code, path.stem, symbol_table)
            parsed_units.append({'tree': tree, 'code': code, 'stem': path.stem, 'lang': language, 'file': path.name})

    # --- PASS 2: LINKING ---
    for unit in parsed_units:
        nodes, relations = PARSER_MAP[unit['lang']](unit['tree'], unit['code'], unit['stem'], symbol_table)
        for n in nodes: builder.add_node(n)
        for r in relations: builder.add_relation(r)

    graph = builder.build()
    for r in build_cross_language_equivalence(list(graph.nodes.values())): graph.add_relation(r)
    graph = link_api_calls(graph)

    # Export basic graph
    with open('output.json', 'w') as f: json.dump(graph.export(), f, indent=2)

    # Aggregated Impacts
    all_impacts = {}
    node_lookup = {nid: (ntype, nlang) for (nid, ntype, nlang) in graph.nodes.keys()}
    
    # Noise Filtering: If a child and parent both changed, prioritize child
    filtered_changes = {}
    sorted_changes = sorted(changed_nodes.keys(), key=len, reverse=True) # Check longest FQNs first (specific)
    handled_parents = set()
    
    for nid in sorted_changes:
        if nid in handled_parents: continue
        filtered_changes[nid] = changed_nodes[nid]
        # Mark parent as handled if this is a method within a class
        if '::' in nid:
            parent = nid.rsplit('::', 1)[0]
            handled_parents.add(parent)

    for start_node, change_type in filtered_changes.items():
        # Resolve best match for the start node
        resolved_start = start_node
        best_match = None
        for (nid, ntype, nlang) in graph.nodes.keys():
            if nid == start_node or nid.split('(')[0] == start_node:
                best_match = nid
                break
        
        if best_match:
            node_impacts = propagate_impact(graph, best_match)
            for target_id, info in node_impacts.items():
                if target_id not in all_impacts or all_impacts[target_id]['depth'] > info['depth']:
                    all_impacts[target_id] = {
                        'depth': info['depth'],
                        'via': info['via'],
                        'root_change': start_node,
                        'change_type': change_type
                    }

    affected_components = []
    actual_nodes = {nid: node for (nid, ntype, nlang), node in graph.nodes.items()}

    for node_id, info in all_impacts.items():
        node = actual_nodes.get(node_id)
        if not node: continue
        
        is_root = (node_id == info['root_change'] or node_id.split('(')[0] == info['root_change'])
        ctype = info['change_type'] if is_root else f"impacted_by_{info['change_type'].lower()}"

        # Resolve file path for original_code extraction
        rel_path = file_index.get((node.language, getattr(node, 'file', '')))
        file_label = rel_path if rel_path else getattr(node, 'file', 'unknown')

        original_code = None
        if changed_snippets and node_id in changed_snippets:
            original_code = changed_snippets[node_id]
        if rel_path:
            try:
                src_path = project_root / rel_path
                lines = src_path.read_text(encoding='utf8', errors='ignore').splitlines()
                start = max(getattr(node, 'start_line', 1), 1)
                end = max(getattr(node, 'end_line', start), start)
                if original_code is None:
                    original_code = "\n".join(lines[start-1:end])
            except Exception:
                if original_code is None:
                    original_code = None

        # If we have precise changed line range, use it
        line_start = getattr(node, 'start_line', 1)
        line_end = getattr(node, 'end_line', 1)
        if changed_line_ranges and node_id in changed_line_ranges:
            line_start, line_end = changed_line_ranges[node_id]

        affected_components.append({
            'component_id': str(uuid.uuid5(uuid.NAMESPACE_DNS, node_id)),
            'change_type': ctype,
            'component_name': node_id.split('::')[-1].split('(')[0] if '(' in node_id else node_id.split('::')[-1],
            'contributor': {'id': 'unknown', 'name': 'Emma Carstairs', 'avatar_url': 'https://avatars.githubusercontent.com/u/1'},
            'confidence': 'high',
            'detection_method': 'parser',
            'affected_files': [{
                'filename': file_label,
                'affected_lines': [{
                    'start_line': line_start,
                    'end_line': line_end,
                    'original_code': original_code,
                    'reason': f"Impacted via {info['via']} from {info['root_change']} at depth {info['depth']}",
                    'annotation': f"{info['via']} impact from {info['root_change']}",
                    'suggested_fix': None,
                    'confidence': 1.0
                }]
            }]
        })

    affected_components.sort(key=lambda x: (x["component_name"], x["affected_files"][0]["filename"]))

    return {
        'schema_version': '1.0',
        'event': 'impact:parser_complete',
        'change_request_id': change_id,
        'data': {
            'status': 'parser_complete',
            'affected_components': affected_components,
            'unaffected_components': [],
            'summary': {
                'total_affected': len(affected_components), 
                'total_files_flagged': len(set(c['affected_files'][0]['filename'] for c in affected_components)),
                'detection_method': 'parser', 
                'llm_analysis_pending': True
            }
        }
    }

def run_pipeline(project_root: Path, impact_start_node="getUsers", send_to_backend=False):
    # Backward compatibility for old calls
    result = analyze_changes(project_root, 'compat-id', {impact_start_node: 'LOGIC_CHANGE'})
    return result, result['data']['affected_components']
