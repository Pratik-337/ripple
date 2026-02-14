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
    Adds cross-language REST API links:
    Frontend (JS/TS) -> Backend (Java Spring)
    """
    api_endpoints = []
    frontend_calls = []

    # ---------------------------------
    # 1. Collect backend API endpoints
    # ---------------------------------
    for node in graph.nodes.values():
        if node.language == "JAVA" and node.type == "METHOD":
            for (src, tgt, typ) in graph.relations:
                if tgt == node.id and typ == "ANNOTATED_WITH":
                    for ann in SPRING_MAPPING_ANNOTATIONS:
                        if ann in src:
                            path = extract_path(src)
                            if path:
                                api_endpoints.append({
                                    "path": path,
                                    "method": ann.upper(),
                                    "target": node.id
                                })

    # ---------------------------------
    # 2. Collect frontend HTTP calls
    # ---------------------------------
    for (src, tgt, typ) in graph.relations:
        if typ == "CALLS":
            for pattern in HTTP_CALL_PATTERNS:
                if pattern in tgt:
                    path = extract_url(tgt)
                    if path:
                        frontend_calls.append({
                            "caller": src,
                            "path": path
                        })

    # ---------------------------------
    # 3. Match frontend -> backend
    # ---------------------------------
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

    return graph


# ------------------ helpers ------------------

def extract_path(annotation_text):
    """
    Extracts path from @GetMapping("/api/x")
    """
    match = re.search(r'\"(.*?)\"', annotation_text)
    return match.group(1) if match else None


def extract_url(call_text):
    """
    Extracts URL from fetch("/api/x") or axios.get("/api/x")
    """
    match = re.search(r'\"(.*?)\"', call_text)
    return match.group(1) if match else None


def normalize(path):
    return path.rstrip("/")
