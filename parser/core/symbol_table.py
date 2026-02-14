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
        if current_class and current_class in self.methods:
            if call_name in self.methods[current_class]:
                return f"{current_class}.{call_name}"

        if current_file in self.functions:
            if call_name in self.functions[current_file]:
                return f"{current_file}.{call_name}"

        return call_name
