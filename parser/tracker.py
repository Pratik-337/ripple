import sys
import os
import pickle
import json
from pathlib import Path
from parser.pipeline import analyze_changes
from parser.core.ast_loader import parse_code
from parser.core.symbol_table import SymbolTable
from parser.core.diff_engine import find_changed_nodes
import difflib
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

def _extract_changed_lines(old_text, new_text):
    """
    Return only changed lines (new-side) for a function body.
    For deletions, include the removed lines prefixed with '- '.
    """
    if old_text is None and new_text is None:
        return None
    if old_text is None:
        return new_text.strip()
    if new_text is None:
        return "\n".join(f"- {l}" for l in old_text.splitlines() if l.strip())

    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    out = []
    sm = difflib.SequenceMatcher(a=old_lines, b=new_lines)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "insert"):
            out.extend(new_lines[j1:j2])
        elif tag == "delete":
            out.extend(f"- {l}" for l in old_lines[i1:i2] if l.strip())
    result = "\n".join(out).strip()
    return result if result else None


def _extract_changed_line_range(old_text, new_text, base_start_line):
    """
    Returns a (start_line, end_line) tuple for changed lines.
    Prefers new-text line numbers when available.
    """
    if old_text is None and new_text is None:
        return None

    if new_text is None:
        # Only deletions; use old text line numbers
        lines = old_text.splitlines() if old_text else []
        if not lines:
            return None
        return base_start_line, base_start_line + len(lines) - 1

    old_lines = old_text.splitlines() if old_text else []
    new_lines = new_text.splitlines()

    changed_indices = []
    sm = difflib.SequenceMatcher(a=old_lines, b=new_lines)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "insert"):
            changed_indices.extend(range(j1, j2))
        elif tag == "delete" and not changed_indices:
            # deletions only; mark at deletion point
            changed_indices.append(max(j1 - 1, 0))

    if not changed_indices:
        return None

    start_idx = min(changed_indices)
    end_idx = max(changed_indices)
    return base_start_line + start_idx, base_start_line + end_idx


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

            # Build changed snippets from old/new symbol tables
            changed_snippets = {}
            changed_line_ranges = {}
            for (lang, fqn), old_def in old_st.definitions.items():
                if fqn not in real_changes:
                    continue
                new_def = new_st.definitions.get((lang, fqn))
                snippet = _extract_changed_lines(
                    old_def.get("body_text") if old_def else None,
                    new_def.get("body_text") if new_def else None
                )
                if snippet:
                    changed_snippets[fqn] = snippet

                base_start = (new_def or old_def).get("start", 1)
                line_range = _extract_changed_line_range(
                    old_def.get("body_text") if old_def else None,
                    new_def.get("body_text") if new_def else None,
                    base_start
                )
                if line_range:
                    changed_line_ranges[fqn] = line_range

            result = analyze_changes(
                Path("samples"),
                "manual-check",
                real_changes,
                changed_snippets=changed_snippets,
                changed_line_ranges=changed_line_ranges
            )
            
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
