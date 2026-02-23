class Node:
    def __init__(self, id, type, language, file='unknown', start_line=1, end_line=1):
        self.id = id
        self.type = type
        self.language = language
        self.file = file
        self.start_line = start_line
        self.end_line = end_line

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'language': self.language,
            'file': self.file,
            'start_line': self.start_line,
            'end_line': self.end_line
        }
