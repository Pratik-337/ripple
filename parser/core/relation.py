class Relation:
    def __init__(self, source, target, type):
        self.source = source
        self.target = target
        self.type = type

    def to_dict(self):
        return {
            "from": self.source,
            "to": self.target,
            "type": self.type
        }
