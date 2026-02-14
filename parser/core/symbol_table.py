class SymbolTable:
    def __init__(self):
        self.functions = {}
        self.classes = {}
        self.methods = {}
        self.imports = {}

    def add_function(self, file, name):
        self.functions.setdefault(file, set()).add(name)

    def add_class(self, file, class_name):
        self.classes.setdefault(file, set()).add(class_name)

    def add_method(self, class_name, method_name):
        self.methods.setdefault(class_name, set()).add(method_name)

    def add_import(self, file, import_name):
        self.imports.setdefault(file, set()).add(import_name)

    def resolve(self, current_class, current_file, call_name):
        # 1️⃣ same class
        if current_class and current_class in self.methods:
            if call_name in self.methods[current_class]:
                return f"{current_class}.{call_name}"

        # 2️⃣ same file
        if current_file in self.functions:
            if call_name in self.functions[current_file]:
                return f"{current_file}.{call_name}"

        # 3️⃣ imported files (NEW)
        cross = self.resolve_cross_file(current_file, call_name)
        if cross:
            return cross

        # 4️⃣ unresolved
        return call_name

    def resolve_cross_file(self, current_file, call_name):
        """
        Try to resolve call_name in imported files
        """
        for imported in self.imports.get(current_file, []):
            if imported in self.functions:
                if call_name in self.functions[imported]:
                    return f"{imported}.{call_name}"
        return None
