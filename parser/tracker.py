import sys
import os
import pickle
import json
from pathlib import Path
from parser.pipeline import analyze_changes
from parser.core.ast_loader import parse_code
from parser.core.symbol_table import SymbolTable
from parser.core.diff_engine import find_changed_nodes
from parser.language_registry import TREE_SITTER_LANG, PARSER_MAP
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

PARSER_MAP.update({
    'JAVA': parse_java, 'PYTHON': parse_python, 'JAVASCRIPT': parse_javascript, 'TYPESCRIPT': parse_typescript,
    'C': parse_c, 'CPP': parse_cpp, 'GO': parse_go, 'RUST': parse_rust, 'PHP': parse_php, 'KOTLIN': parse_kotlin,
})

BASELINE_FILE = ".ripple_baseline.pkl"

def get_current_st(path):
    st = SymbolTable()
    path_obj = Path(path)
    for ext, lang in [('.java', 'JAVA'), ('.py', 'PYTHON'), ('.js', 'JAVASCRIPT'), ('.ts', 'TYPESCRIPT'), ('.c', 'C'), ('.cpp', 'CPP'), ('.go', 'GO'), ('.rs', 'RUST'), ('.php', 'PHP'), ('.kt', 'KOTLIN')]:
        for f in path_obj.glob(f"**/*{ext}"):
            try:
                code = f.read_text(encoding="utf8", errors="ignore")
                tree = parse_code(code, TREE_SITTER_LANG[lang])
                PARSER_MAP[lang](tree, code, f.stem, st)
            except Exception as e:
                print(f"Error parsing {f}: {e}")
    return st

def main():
    sys.path.insert(0, str(Path(__file__).parent.parent))

    if len(sys.argv) < 2:
        print("Usage: python -m parser.tracker [snapshot|check]")
        return

    cmd = sys.argv[1]
    
    if cmd == "snapshot":
        print("Scanning project and saving baseline...")
        st = get_current_st("samples")
        with open(BASELINE_FILE, "wb") as f:
            pickle.dump(st, f)
        print("Baseline saved successfully! Now go edit your code.")

    elif cmd == "check":
        if not os.path.exists(BASELINE_FILE):
            print("Error: No baseline found. Run 'snapshot' first.")
            return
        
        with open(BASELINE_FILE, "rb") as f:
            old_st = pickle.load(f)
        
        print("Scanning for changes...")
        new_st = get_current_st("samples")
        
        changes = find_changed_nodes(old_st, new_st)
        
        real_changes = {nid: ctype for nid, ctype in changes.items() if ctype not in ["NO_CHANGE", "METADATA_CHANGE"]}
        
        if real_changes:
            print(f"Detected {len(real_changes)} changes. Calculating aggregated ripple effect...")
            for nid, ctype in real_changes.items():
                print(f"  >>> {nid} ({ctype})")
            
            result = analyze_changes(Path("samples"), "manual-check", real_changes)
            
            with open("impact.json", "w") as f:
                json.dump(result, f, indent=2)
            print(f"[SAVED] Aggregated impact report saved to impact.json")

            print("--- AGGREGATED IMPACT REPORT ---")
            for comp in result["data"]["affected_components"]:
                if any(comp["change_type"] == ctype for ctype in real_changes.values()):
                     print(f"  [ROOT] {comp['component_name']} ({comp['change_type']})")
                else:
                     print(f"  [AFFECTED] {comp['component_name']} ({comp['affected_files'][0]['affected_lines'][0]['reason']})")
        else:
            print("No significant changes detected compared to baseline.")

if __name__ == "__main__":
    main()
