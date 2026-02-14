from pathlib import Path
from core.call_resolver import resolve_calls
import json
import requests

# ---------------- CORE ----------------
from core.ast_loader import parse_code
from core.graph import Graph
from core.symbol_table import SymbolTable

# ---------------- REGISTRY ----------------
from language_registry import (
    EXTENSION_MAP,
    TREE_SITTER_LANG,
    PARSER_MAP
)

# ---------------- PARSERS ----------------
from languages.java_parser import parse_java
from languages.python_parser import parse_python
from languages.javascript_parser import parse_javascript
from languages.typescript_parser import parse_typescript
from languages.c_parser import parse_c
from languages.cpp_parser import parse_cpp
from languages.go_parser import parse_go
from languages.rust_parser import parse_rust
from languages.php_parser import parse_php
from languages.kotlin_parser import parse_kotlin

from core.cross_language_linker import link


# ---------------- REGISTER PARSERS ----------------
PARSER_MAP.update({
    "JAVA": parse_java,
    "PYTHON": parse_python,
    "JAVASCRIPT": parse_javascript,
    "TYPESCRIPT": parse_typescript,
    "C": parse_c,
    "CPP": parse_cpp,
    "GO": parse_go,
    "RUST": parse_rust,
    "PHP": parse_php,
    "KOTLIN": parse_kotlin,
})

# ---------------- PATHS ----------------
PROJECT_ROOT = Path("samples")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------- GRAPH + SYMBOLS ----------------
graph = Graph()
symbol_table = SymbolTable()

# ---------------- MAIN LOOP ----------------
for file in PROJECT_ROOT.rglob("*"):
    if not file.is_file():
        continue

    ext = file.suffix.lower()
    if ext not in EXTENSION_MAP:
        continue

    language = EXTENSION_MAP[ext]

    if language not in PARSER_MAP:
        continue  # parser not implemented yet

    try:
        with open(file, "r", encoding="utf8", errors="ignore") as f:
            code = f.read()

        tree = parse_code(code, TREE_SITTER_LANG[language])

        nodes, relations = PARSER_MAP[language](
            tree,
            code,
            file.stem,
            symbol_table
        )

        for node in nodes:
            graph.add_node(node)

        for relation in relations:
            graph.add_relation(relation)

    except Exception as e:
        raise e

# ---------------- OUTPUT ----------------
graph = link(graph)
graph = resolve_calls(graph, symbol_table)
output = graph.export()

with open(OUTPUT_DIR / "graph.json", "w", encoding="utf8") as f:
    json.dump(output, f, indent=2)

print(json.dumps(output, indent=2))

BACKEND_URL = "http://localhost:8080/api/ingest"

print(f"\n Sending {len(output['nodes'])} nodes and {len(output['relations'])} relations to Backend...")

try:
    response = requests.post(BACKEND_URL, json=output)
    
    if response.status_code == 200:
        print("SUCCESS: Data ingested by Backend")
    else:
        print(f"ERROR: Backend returned {response.status_code}")
        print(response.text)

except requests.exceptions.ConnectionError:
    print("CONNECTION FAILED: Is the Java Backend running on port 8080?")
except Exception as e:
    print(f"UNEXPECTED ERROR: {e}")