class Node:
    def __init__(self, id, type, language):
        self.id = id
        self.type = type
        self.language = language

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "language": self.language
        }
