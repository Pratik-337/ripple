from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any
import os

from parser.language_registry import EXTENSION_MAP


# =========================
# Exceptions
# =========================

class SecurityError(Exception):
    pass


class AnalysisError(Exception):
    pass


# =========================
# Configuration
# =========================

@dataclass(frozen=True)
class AnalysisConfig:
    allowed_languages: List[str]
    max_files: int = 5000
    max_file_size_kb: int = 512
    max_depth: int = 200


# =========================
# Public Entry Point
# =========================

def analyze_repository(repo_path: Path, config: AnalysisConfig):
    """
    SECURE ENTRY POINT
    ------------------
    File discovery + metadata ONLY.
    """

    if not repo_path.exists():
        raise AnalysisError("Repository path does not exist")

    if not repo_path.is_dir():
        raise AnalysisError("Repository path is not a directory")

    repo_path = repo_path.resolve()

    if repo_path.is_symlink():
        raise SecurityError("Symlinked repository roots are not allowed")

    all_files = _safe_walk(repo_path, config)
    details = []

    allowed_languages = {lang.upper() for lang in config.allowed_languages}

    for file_path in all_files:
        ext = file_path.suffix.lower()
        language = EXTENSION_MAP.get(ext)

        if not language:
            continue

        if language not in allowed_languages:
            continue

        try:
            code = file_path.read_text(encoding="utf8", errors="ignore")
            line_count = code.count("\n")
            parse_error = None
        except Exception as e:
            line_count = 0
            parse_error = str(e)

        details.append({
            "path": str(file_path.resolve()),
            "language": language,
            "line_count": line_count,
            "parse_error": parse_error
        })

    return {
        "schema_version": "1.0",
        "language": "mixed",
        "summary": {
            "files_discovered": len(details),
            "files_parsed": len([d for d in details if d["parse_error"] is None]),
            "files_failed": len([d for d in details if d["parse_error"] is not None]),
            "total_nodes": 0,
            "total_relations": 0
        },
        "files": [
            {
                "path": d["path"],
                "status": "parsed" if d["parse_error"] is None else "failed"
            }
            for d in details
        ],
        "details": details,
        "errors": []
    }


# =========================
# Internal Helpers
# =========================

def _safe_walk(repo_path: Path, config: AnalysisConfig):
    collected_files = []

    for root, _, files in os.walk(repo_path, followlinks=False):
        root_path = Path(root)

        try:
            root_path.relative_to(repo_path)
        except ValueError:
            raise SecurityError("Directory traversal detected")

        depth = len(root_path.relative_to(repo_path).parts)
        if depth > config.max_depth:
            raise SecurityError("Maximum directory depth exceeded")

        for name in files:
            file_path = root_path / name

            if file_path.is_symlink():
                continue

            if len(collected_files) >= config.max_files:
                raise AnalysisError("Maximum file limit exceeded")

            try:
                size_kb = file_path.stat().st_size / 1024
            except OSError:
                continue

            if size_kb > config.max_file_size_kb:
                continue

            collected_files.append(file_path)

    return collected_files
