# language_registry.py

# -------------------------------
# Extension → Canonical Language
# -------------------------------
EXTENSION_MAP = {
    ".java": "JAVA",
    ".py": "PYTHON",
    ".js": "JAVASCRIPT",
    ".ts": "TYPESCRIPT",
    ".c": "C",
    ".cpp": "CPP",
    ".go": "GO",
    ".rs": "RUST",
    ".php": "PHP",
    ".kt": "KOTLIN",
}

# -------------------------------
# Canonical Language → Tree-sitter
# -------------------------------
TREE_SITTER_LANG = {
    "JAVA": "java",
    "PYTHON": "python",
    "JAVASCRIPT": "javascript",
    "TYPESCRIPT": "typescript",
    "C": "c",
    "CPP": "cpp",
    "GO": "go",
    "RUST": "rust",
    "PHP": "php",
    "KOTLIN": "kotlin",
}

# -------------------------------
# Canonical Language → Parser
# (filled in main.py to avoid circular imports)
# -------------------------------
PARSER_MAP = {}
