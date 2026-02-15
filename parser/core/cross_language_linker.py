import re

HTTP_CALL_PATTERNS = [
    "fetch",
    "axios.get",
    "axios.post",
    "axios.put",
    "axios.delete"
]

SPRING_MAPPING_ANNOTATIONS = [
    "GetMapping",
    "PostMapping",
    "PutMapping",
    "DeleteMapping",
    "RequestMapping"
]


def link(graph):
    """
    Links frontend JS/TS HTTP calls to backend Java Spring APIs
    """
    api_endpoints = []
    frontend_calls = []

    # ===============================
    # 1. Collect backend API endpoints
    # ===============================
    for (src, tgt, typ) in graph.relations:
        if typ == "ANNOTATED_WITH":
            for ann in SPRING_MAPPING_ANNOTATIONS:
                if ann in src:
                    path = extract_path(src)
                    if path:
                        api_endpoints.append({
                            "path": path,
                            "target": tgt
                        })

    # ===============================
    # 2. Collect frontend HTTP calls
    # ===============================
    for (src, tgt, typ) in graph.relations:
        if typ == "CALLS":
            if any(p in tgt for p in HTTP_CALL_PATTERNS):
                path = extract_url(tgt)
                if path:
                    frontend_calls.append({
                        "caller": src,
                        "path": path
                    })

    # ===============================
    # 3. Link frontend → backend
    # ===============================
    added = 0
    for call in frontend_calls:
        for api in api_endpoints:
            if normalize(call["path"]) == normalize(api["path"]):
                graph.relations.add(
                    (
                        call["caller"],
                        api["target"],
                        "CALLS_API"
                    )
                )
                added += 1

    print(f"API edges added: {added}")
    return graph


# ===============================
# Helpers
# ===============================

def extract_path(annotation_text):
    """
    @GetMapping("/users") -> /users
    """
    match = re.search(r'"(.*?)"', annotation_text)
    return match.group(1) if match else None


def extract_url(call_text):
    """
    fetch("/users") -> /users
    axios.get("/users") -> /users
    """
    match = re.search(r'"(.*?)"', call_text)
    return match.group(1) if match else None


def normalize(path):
    return path.rstrip("/")
