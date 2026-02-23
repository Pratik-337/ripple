from parser.core.relation import Relation


# Languages where name-based equivalence is VALID
EQUIVALENCE_SAFE_LANGS = {
    "JAVASCRIPT",
    "TYPESCRIPT",
}

# Languages that must NEVER auto-link by name
EQUIVALENCE_BLOCKED_LANGS = {
    "RUST",
    "C",
    "CPP",
    "GO",
    "JAVA",
    "PYTHON",
}


def build_cross_language_equivalence(nodes):
    """
    Build CROSS_LANG_EQUIVALENT edges ONLY where it is semantically safe.

    Rule:
    - JS <-> TS : allowed
    - Everything else: forbidden unless explicitly configured later
    """

    relations = []

    # Index nodes by simple name
    by_name = {}
    for node in nodes:
        simple_name = node.id.split(".")[-1]
        by_name.setdefault(simple_name, []).append(node)

    for name, group in by_name.items():
        if len(group) < 2:
            continue

        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a = group[i]
                b = group[j]

                # Same language → ignore
                if a.language == b.language:
                    continue

                # Block if either side is unsafe
                if (
                    a.language in EQUIVALENCE_BLOCKED_LANGS
                    or b.language in EQUIVALENCE_BLOCKED_LANGS
                ):
                    continue

                # Allow ONLY JS <-> TS
                if (
                    a.language in EQUIVALENCE_SAFE_LANGS
                    and b.language in EQUIVALENCE_SAFE_LANGS
                ):
                    relations.append(
                        Relation(
                            source=a.id,
                            target=b.id,
                            type="CROSS_LANG_EQUIVALENT"
                        )
                    )

                    relations.append(
                        Relation(
                            source=b.id,
                            target=a.id,
                            type="CROSS_LANG_EQUIVALENT"
                        )
                    )

    return relations