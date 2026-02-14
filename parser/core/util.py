import re

def normalize_call_name(raw: str) -> str:
    """
    Converts:
    - helper()
    - helper(1,2)
    - this.helper()
    - obj.helper(3)
    into:
    - helper
    """
    if not raw:
        return raw

    # remove arguments
    name = raw.split("(")[0]

    # remove object prefix
    if "." in name:
        name = name.split(".")[-1]

    return name.strip()
