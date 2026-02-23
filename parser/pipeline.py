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

def analyze_change(project_root: Path, change_id: str, impact_start_node: str):
    builder = GraphBuilder()
    symbol_table = SymbolTable()
    config = AnalysisConfig(allowed_languages=list(PARSER_MAP.keys()), max_files=5000)
    analysis = analyze_repository(project_root, config)

    # --- PASS 1: DISCOVERY (All Definitions) ---
    parsed_units = []
    for unit in analysis['details']:
        if unit['parse_error']: continue
        path = Path(unit['path'])
        language = EXTENSION_MAP.get(path.suffix.lower())
        if language in PARSER_MAP:
            code = path.read_text(encoding='utf8', errors='ignore')
            tree = parse_code(code, TREE_SITTER_LANG[language])
            # Dry run to fill symbol table
            PARSER_MAP[language](tree, code, path.stem, symbol_table)
            parsed_units.append({'tree': tree, 'code': code, 'stem': path.stem, 'lang': language, 'file': path.name})

    # --- PASS 2: LINKING (All Relations) ---
    for unit in parsed_units:
        nodes, relations = PARSER_MAP[unit['lang']](unit['tree'], unit['code'], unit['stem'], symbol_table)
        for n in nodes: builder.add_node(n)
        for r in relations: builder.add_relation(r)

    graph = builder.build()
    for r in build_cross_language_equivalence(list(graph.nodes.values())): graph.add_relation(r)
    graph = link_api_calls(graph)

    full_graph = graph.export()
    with open('output.json', 'w') as f: json.dump(full_graph, f, indent=2)

    resolved_start = impact_start_node
    for (nid, ntype, nlang) in graph.nodes.keys():
        if nid.endswith(impact_start_node): resolved_start = nid; break

    impacts = propagate_impact(graph, resolved_start)
    
    affected_components = []
    node_lookup = {nid: node for (nid, ntype, nlang), node in graph.nodes.items()}

    for node_id, info in impacts.items():
        node = node_lookup.get(node_id)
        if not node: continue

        affected_components.append({
            'component_id': str(uuid.uuid4()),
            'component_name': node_id.split('::')[1] if '::' in node_id else 'Core',
            'contributor': {'id': 'unknown', 'name': 'Emma Carstairs', 'avatar_url': 'https://avatars.githubusercontent.com/u/1'},
            'confidence': 'high' if info['depth'] <= 1 else 'medium',
            'detection_method': 'parser',
            'affected_files': [{
                'filename': getattr(node, 'file', 'unknown'),
                'affected_lines': [{
                    'start_line': getattr(node, 'start_line', 1),
                    'end_line': getattr(node, 'end_line', 1),
                    'reason': f'Impacted at depth {info["depth"]}',
                    'confidence': 1.0
                }]
            }]
        })

    return {
        'event': 'impact:parser_complete',
        'change_request_id': change_id,
        'data': {
            'status': 'parser_complete',
            'affected_components': affected_components,
            'summary': {
                'total_affected': len(affected_components), 
                'total_files_flagged': len(set(c['affected_files'][0]['filename'] for c in affected_components)),
                'detection_method': 'parser', 
                'llm_analysis_pending': True
            }
        }
    }

def run_pipeline(project_root: Path, send_to_backend=False):
    result = analyze_change(project_root, 'compat-id', 'UserController.getUsers')
    return result, result['data']['affected_components']
