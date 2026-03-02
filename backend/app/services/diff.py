import difflib

def generate_diff(original: str, modified: str) -> dict:
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    
    diff = list(difflib.unified_diff(original_lines, modified_lines, n=3))
    
    hunks = []
    current_hunk = None
    additions = 0
    deletions = 0
    changed_lines = []
    
    line_num = 0
    for line in diff:
        if line.startswith('@@'):
            # @@ -start,count +start,count @@
            parts = line.split(' ')
            orig_info = parts[1]
            mod_info = parts[2]
            
            try:
                mod_start = int(mod_info.split(',')[0].replace('+', ''))
            except Exception:
                mod_start = 1
                
            line_num = mod_start
            
            if current_hunk:
                hunks.append(current_hunk)
            current_hunk = {
                "start_line": mod_start,
                "end_line": mod_start,
                "type": "context",
                "content": []
            }
        elif current_hunk is not None:
            if line.startswith('+') and not line.startswith('+++'):
                current_hunk["content"].append(line)
                current_hunk["type"] = "add"
                additions += 1
                changed_lines.append(line_num)
                line_num += 1
                current_hunk["end_line"] = line_num
            elif line.startswith('-') and not line.startswith('---'):
                current_hunk["content"].append(line)
                current_hunk["type"] = "remove"
                deletions += 1
                changed_lines.append(line_num)
                current_hunk["end_line"] = max(current_hunk["end_line"], line_num)
            elif not line.startswith('\\'):
                current_hunk["content"].append(line)
                line_num += 1
                current_hunk["end_line"] = line_num
                
    if current_hunk:
         hunks.append(current_hunk)
         
    for h in hunks:
        h["content"] = "".join(h["content"])
        
    return {
        "hunks": hunks,
        "changed_lines": list(set(changed_lines)),
        "additions": additions,
        "deletions": deletions,
        "changed_symbols": [] # We could extract symbols if we cross-ref AST here, but omitting for basic diff
    }
