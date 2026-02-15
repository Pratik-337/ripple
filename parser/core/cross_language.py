# core/cross_language.py

from core.relation import Relation
from core.util import normalize_call_name


def normalize_node_id(node_id: str) -> str:
    """
    Normalize node id to a base name for cross-language matching.

    Examples:
      test.helper           -> helper
      utils.helper          -> helper
      Calculator.add        -> add
      fs::read_to_string    -> read_to_string
      Println               -> println
    """
    # split on common separators
    for sep in ["::", ".", "/"]:
        if sep in node_id:
            node_id = node_id.split(sep)[-1]

    return normalize_call_name(node_id)


def build_cross_language_links(nodes):
    """
    Build CROSS_LANG_EQUIVALENT relations between nodes
    that represent the same logical entity across languages.
    """

    groups = {}
    relations = []

    # 1️⃣ group nodes by (normalized_name, type)
    for node in nodes:
        base = normalize_node_id(node.id)
        key = (base, node.type)

        groups.setdefault(key, []).append(node)

    # 2️⃣ link nodes across different languages
    for (_, _), group in groups.items():
        if len(group) < 2:
            continue

        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a = group[i]
                b = group[j]

                if a.language == b.language:
                    continue

                relations.append(
                    Relation(a.id, b.id, "CROSS_LANG_EQUIVALENT")
                )
                relations.append(
                    Relation(b.id, a.id, "CROSS_LANG_EQUIVALENT")
                )

    return relations
