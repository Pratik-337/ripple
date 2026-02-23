from collections import defaultdict

class SymbolTable:
    def __init__(self):
        self.definitions = {}
        self.imports = {}
        self.index = defaultdict(lambda: defaultdict(set))
        self.hierarchy = defaultdict(lambda: defaultdict(set))
        self.methods = defaultdict(lambda: defaultdict(set))

    def add_definition(self, lang, fqn, type, file, parent=None, start=1, end=1):
        self.definitions[(lang, fqn)] = {
            'type': type, 'file': file, 'parent': parent, 'start': start, 'end': end, 'fields': {}
        }
        self.index[lang][type].add(fqn)
        if parent: 
            self.hierarchy[lang][fqn].add(parent)
            meth_name = fqn.split('.')[-1] if '.' in fqn else fqn.split('::')[-1]
            self.methods[lang][parent].add(meth_name)

    def add_field_to_class(self, lang, class_fqn, field_name, field_type):
        if (lang, class_fqn) in self.definitions:
            self.definitions[(lang, class_fqn)]['fields'][field_name] = field_type

    def add_import(self, file, alias, target): self.imports.setdefault(file, {})[alias] = target

    def resolve(self, lang, current_file, current_owner, call_name, local_scope=None):
        # 1. Prepare parts
        obj, meth = None, call_name
        if '.' in call_name:
            obj, meth = call_name.split('.', 1)

        # 2. Local variable / Field resolution
        obj_type = None
        if local_scope and obj in local_scope: obj_type = local_scope[obj]
        elif current_owner and (lang, current_owner) in self.definitions:
            obj_type = self.definitions[(lang, current_owner)]['fields'].get(obj)
        
        if obj_type:
            # Resolve type via imports (e.g. UserService -> com.demo.UserService)
            full_type = self.imports.get(current_file, {}).get(obj_type, obj_type)
            return self._build_fqn(lang, full_type, meth), 'CALLS_DYNAMIC'

        # 3. Direct sibling / Inheritance resolution
        if current_owner:
            if meth in self.methods[lang][current_owner]:
                return f'{current_owner}.{meth}', 'CALLS'
            for parent in self.hierarchy[lang].get(current_owner, []):
                if meth in self.methods[lang][parent]:
                    return f'{parent}.{meth}', 'CALLS_DYNAMIC'

        # 4. OMNISCIENT GLOBAL SEARCH (The Fix)
        # If we have a method name (with or without a receiver), search the whole project
        for type_key in ['METHOD', 'FUNCTION']:
            for fqn in self.index[lang].get(type_key, []):
                # Match if FQN ends with .meth or ::meth
                if fqn.endswith(f'.{meth}') or fqn.endswith(f'::{meth}') or fqn == meth:
                    return fqn, 'CALLS_DYNAMIC' if type_key == 'METHOD' else 'CALLS'

        return call_name, 'CALLS'

    def _build_fqn(self, lang, owner_type, meth_name):
        prefix = 'java::default' if lang == 'JAVA' else lang.lower()
        if '::' in owner_type: return f'{owner_type}.{meth_name}'
        return f'{prefix}::{owner_type}.{meth_name}'
