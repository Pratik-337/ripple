import os

EXT_MAP = {
    ".ts": "typescript", ".tsx": "typescript",
    ".js": "javascript", ".jsx": "javascript",
    ".py": "python", ".go": "go", ".rs": "rust",
    ".java": "java", ".cs": "c_sharp", ".rb": "ruby",
    ".php": "php", ".cpp": "cpp", ".c": "c",
    ".html": "html", ".css": "css", ".json": "json",
    ".md": "markdown", ".yaml": "yaml", ".yml": "yaml",
}

def detect_language(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    return EXT_MAP.get(ext.lower(), "plaintext")
