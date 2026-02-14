from tree_sitter import Parser, Language
import tree_sitter_java
from tree_sitter_languages import get_parser

def parse_code(code, language):
    if language == "java":
        parser = get_parser("java")

    elif language == "python":
        parser = get_parser("python")

    elif language in ("javascript", "js"):
        parser = get_parser("javascript")

    elif language == "typescript":
        parser = get_parser("typescript")

    elif language == "go":
        parser = get_parser("go")

    elif language == "c":
        parser = get_parser("c")

    elif language in ("cpp", "c++"):
        parser = get_parser("cpp")  

    elif language == "rust":
        parser = get_parser("rust")

    elif language == "kotlin":
        parser = get_parser("kotlin")

    elif language == "php":
        parser = get_parser("php")
    
    else:
        raise ValueError(f"Unsupported language: {language}")

    return parser.parse(code.encode("utf8"))
