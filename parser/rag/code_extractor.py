from pathlib import Path

def extract_code(project_root: Path, node):
    # Try the original filename first (it might already have an extension)
    file_path = project_root / node.file
    
    # If it doesn't exist, map node.language to standard extensions
    if not file_path.exists():
        ext_map = {
            "PYTHON": ".py", "JAVA": ".java", "JAVASCRIPT": ".js", 
            "TYPESCRIPT": ".ts", "C": ".c", "CPP": ".cpp", 
            "GO": ".go", "RUST": ".rs", "PHP": ".php", "KOTLIN": ".kt"
        }
        ext = ext_map.get(node.language, "")
        file_path = project_root / (str(node.file) + ext)

    # Fallback to a glob search for ANY extension if mapping fails
    if not file_path.exists():
        try:
            # Limit to first match to avoid confusion
            potential = list(project_root.glob(f"{node.file}.*"))
            if potential:
                file_path = potential[0]
            else:
                return None
        except:
            return None

    try:
        # Securely read text
        if not file_path.is_file():
            return None
            
        lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        
        # Bounds checking to avoid index errors
        start = max(0, node.start_line - 1)
        end = min(len(lines), node.end_line)
        
        if start >= len(lines):
            return None
            
        return "\n".join(lines[start:end])
    except Exception as e:
        # LOG for debugging
        print(f"Extraction failed for {node.file} ({node.language}): {str(e)}")
        return None
