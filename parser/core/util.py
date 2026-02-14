import re

def normalize_call_name(raw: str) -> str:
    """
    Normalizes call expressions across languages.

    Examples:
    - helper()                  -> helper
    - obj.helper(1)             -> helper
    - this.helper()             -> helper
    - console.log(x)            -> log
    - fetch("/users")           -> fetch
    - fetch("/users").then(...) -> fetch
    """
    if not raw:
        return raw

    raw = raw.strip()

    # 🔥 collapse fetch / axios / promise chains
    if raw.startswith("fetch"):
        return "fetch"

    if raw.startswith("axios"):
        return "axios"

    # remove arguments
    name = raw.split("(")[0]

    # remove object / this / module prefix
    if "." in name:
        name = name.split(".")[-1]

    return name.strip()
