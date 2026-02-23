from pathlib import Path
from parser.analyzer import analyze_repository, AnalysisConfig
import json
config = AnalysisConfig(
    allowed_languages=["java"],
    max_files=10
)

result = analyze_repository(
    Path("mini_repo"),
    config
)

result = analyze_repository(Path("mini_repo"), config)

print(f"Parsed {result['summary']['files_parsed']} source files\n")

for i, file in enumerate(result["details"], start=1):
    print(f"File {i}:")
    print(f"  path: {file['path'].split('/')[-1]}")
    print(f"  language: {file['language']}")
    print(f"  line_count: {file['line_count']}")
    print(f"  parse_error: {file['parse_error']}")
    print()

