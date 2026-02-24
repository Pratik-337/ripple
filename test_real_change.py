import sys
from pathlib import Path
import json
import hashlib
from parser.pipeline import analyze_change
from parser.core.ast_loader import parse_code
from parser.core.symbol_table import SymbolTable
from parser.language_registry import TREE_SITTER_LANG
from parser.languages.java_parser import parse_java
from parser.core.diff_engine import find_changed_nodes

def get_snapshot(path):
    st = SymbolTable()
    # Simplified parser call for demo
    for f in Path(path).glob('**/*.java'):
        code = f.read_text()
        tree = parse_code(code, 'java')
        parse_java(tree, code, f.stem, st)
    return st

print('--- STEP 1: Taking snapshot of current code ---')
old_st = get_snapshot('samples')

print('\n--- STEP 2: SIMULATING A CODE CHANGE ---')
print('Modifying samples/UserService.java body...')
original_file = Path('samples/UserService.java')
original_content = original_file.read_text()
# Add a dummy comment to change the hash but keep signature same
new_content = original_content.replace('int a=10;', 'int a=10; // Change made!')
original_file.write_text(new_content)

print('\n--- STEP 3: Taking new snapshot ---')
new_st = get_snapshot('samples')

print('\n--- STEP 4: DETECTING CHANGES AUTOMATICALLY ---')
changes = find_changed_nodes(old_st, new_st)
for node_id, change_type in changes.items():
    if change_type != 'NO_CHANGE':
        print(f'DETECTED: {node_id} has a {change_type}')
        
        print(f'\n--- STEP 5: CALCULATING RIPPLE EFFECT FOR {node_id} ---')
        # Now we run the actual pipeline using the DETECTED node as the start point
        result = analyze_change(Path('samples'), 'trial-1', node_id)
        
        print('\nFINAL IMPACT REPORT:')
        for comp in result['data']['affected_components']:
            print(f"  -> {comp['component_name']} ({comp['change_type']}) in {comp['affected_files'][0]['filename']}")

# Restore the file so we don't leave a mess
original_file.write_text(original_content)
