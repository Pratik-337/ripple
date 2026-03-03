from collections import defaultdict
import hashlib

def _dict_set_factory():
    return defaultdict(set)

class SymbolTable:
    def __init__(self):
        self.definitions = {}
        self.imports = {}
        self.index = defaultdict(_dict_set_factory)
        self.hierarchy = defaultdict(_dict_set_factory)
        self.methods = defaultdict(_dict_set_factory)

    def add_definition(self, lang, fqn, type, file, parent=None, start=1, end=1, body_text=None):
        body_hash = None
        if body_text:
            body_hash = hashlib.md5(body_text.strip().encode('utf8')).hexdigest()

        self.definitions[(lang, fqn)] = {
            'id': fqn,
            'type': type, 
            'file': file, 
            'parent': parent, 
            'start': start, 
            'end': end, 
            'fields': {}, 
            'body_hash': body_hash,
            'body_text': body_text
        }
        self.index[lang][type].add(fqn)
        if parent: 
            self.hierarchy[lang][fqn].add(parent)
            meth_name = fqn.split('::')[-1]
            self.methods[lang][parent].add(meth_name)

    def add_field_to_class(self, lang, class_fqn, field_name, field_type):
        if (lang, class_fqn) in self.definitions:
            self.definitions[(lang, class_fqn)]['fields'][field_name] = field_type

    def add_import(self, file, alias, target): self.imports.setdefault(file, {})[alias] = target

    def resolve(self, lang, current_file, current_owner, call_name, local_scope=None):
        # print(f"   [Resolver] Attempting: {call_name} in {current_owner}")
        obj, meth = None, call_name
        if '::' in call_name:
            parts = call_name.rsplit('::', 1)
            obj, meth = parts[0], parts[1]
        elif '.' in call_name:
            parts = call_name.split('.', 1)
            obj, meth = parts[0], parts[1]

        obj_type = None
        if local_scope and obj in local_scope: obj_type = local_scope[obj]
        elif current_owner and (lang, current_owner) in self.definitions:
            obj_type = self.definitions[(lang, current_owner)]['fields'].get(obj)
        
        if obj_type:
            full_type = self.imports.get(current_file, {}).get(obj_type, obj_type)
            target = self._build_fqn(lang, full_type, meth)
            if (lang == 'JAVA' or lang == 'KOTLIN') and not target.endswith('()'):
                target += '()'
            return target, 'CALLS_DYNAMIC'

        if current_owner:
            if meth in self.methods[lang][current_owner]:
                res = f'{current_owner}::{meth}'
                if (lang == 'JAVA' or lang == 'KOTLIN') and not res.endswith('()'): res += '()'
                return res, 'CALLS'
            for parent in self.hierarchy[lang].get(current_owner, []):
                if meth in self.methods[lang][parent]:
                    res = f'{parent}::{meth}'
                    if (lang == 'JAVA' or lang == 'KOTLIN') and not res.endswith('()'): res += '()'
                    return res, 'CALLS_DYNAMIC'

        # FALLBACK: If type resolution fails, search for any node ending with ::method() or method()
        search_meth = meth.split('(')[0] if '(' in meth else meth
        potential_matches = []
        
        for type_key in ['METHOD', 'FUNCTION']:
            for fqn in self.index[lang].get(type_key, []):
                clean_fqn = fqn.split('(')[0]
                if clean_fqn.endswith(f'::{search_meth}') or clean_fqn == search_meth:
                    potential_matches.append(fqn)
        
        # If we find exactly one match, we are confident. 
        # If multiple, we return the first but mark it as dynamic.
        if potential_matches:
            return potential_matches[0], 'CALLS_DYNAMIC'

                # FALLBACK: Global search
        search_meth = meth.split('(')[0] if '(' in meth else meth
        for type_key in ['METHOD', 'FUNCTION']:
            for fqn in self.index[lang].get(type_key, []):
                clean_fqn = fqn.split('(')[0]
                if clean_fqn.endswith(f'::{search_meth}') or clean_fqn == search_meth:
                    return fqn, 'CALLS_DYNAMIC'
        return call_name, 'CALLS'

    def _build_fqn(self, lang, owner_type, meth_name):
        prefix = 'java::default' if lang == 'JAVA' else lang.lower()
        if '::' in owner_type: return f'{owner_type}::{meth_name}'
        return f'{prefix}::{owner_type}::{meth_name}'
