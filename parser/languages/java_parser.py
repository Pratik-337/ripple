from ..core.node import Node
from ..core.relation import Relation
from ..core.traversal import traverse
from ..core.util import normalize_call_name

def parse_java(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes, relations, src = [], [], source_code.encode('utf8')
    def text(n): return src[n.start_byte:n.end_byte].decode('utf8', errors='ignore')
    
    pkg = 'default'
    for c in root.children:
        if c.type == 'package_declaration':
            n = c.child_by_field_name('name')
            if n: pkg = text(n).replace(';', '').strip()

    for c in root.children:
        if c.type in {'class_declaration', 'interface_declaration'}:
            nm = c.child_by_field_name('name')
            if not nm: continue
            r_nm = text(nm)
            kind = 'INTERFACE' if c.type == 'interface_declaration' else 'CLASS'
            cls_id = f'java::{pkg}::{r_nm}'
            nodes.append(Node(cls_id, kind, 'JAVA', filename, c.start_point[0]+1, c.end_point[0]+1))
            symbol_table.add_definition('JAVA', cls_id, kind, filename, None, c.start_point[0]+1, c.end_point[0]+1, body_text=text(c))

            # Inheritance
            for gc in c.children:
                if gc.type in {'extends_interfaces', 'interfaces', 'superclass'}:
                    for spec in traverse(gc):
                        if spec.type == 'type_identifier':
                            target = f'java::{pkg}::{text(spec)}'
                            relations.append(Relation(cls_id, target, 'IMPLEMENTS'))
                            symbol_table.hierarchy['JAVA'][cls_id].add(target)

            body = c.child_by_field_name('body')
            if not body: continue
            
            # --- PASS 1: Fields ---
            for child in body.children:
                if child.type == 'field_declaration':
                    t = child.child_by_field_name('type')
                    decl = child.child_by_field_name('declarator')
                    if t and decl:
                        f_name = text(decl.child_by_field_name('name'))
                        f_type = text(t)
                        symbol_table.add_field_to_class('JAVA', cls_id, f_name, f_type)

            # --- PASS 2: Methods ---
            for m in body.children:
                if m.type == 'method_declaration':
                    mnm = m.child_by_field_name('name')
                    if not mnm: continue
                    
                    params = m.child_by_field_name('parameters')
                    sig = '()'
                    if params:
                        types = []
                        for p in params.children:
                            if p.type == 'formal_parameter':
                                t = p.child_by_field_name('type')
                                if t: types.append(text(t))
                        sig = '(' + ','.join(types) + ')'
                    
                    m_id = f'{cls_id}::{text(mnm)}{sig}'
                    nodes.append(Node(m_id, 'METHOD', 'JAVA', filename, m.start_point[0]+1, m.end_point[0]+1))
                    relations.append(Relation(cls_id, m_id, 'CONTAINS'))
                    symbol_table.add_definition('JAVA', m_id, 'METHOD', filename, cls_id, m.start_point[0]+1, m.end_point[0]+1, body_text=text(m))
                    
                    # Local Variable tracking (very basic)
                    local_scope = {}
                    for n in traverse(m):
                        if n.type == 'variable_declarator':
                            p = n.parent
                            while p and p.type != 'variable_declaration' and p.type != 'local_variable_declaration':
                                p = p.parent
                            if p:
                                t = p.child_by_field_name('type')
                                if t: local_scope[text(n.child_by_field_name('name'))] = text(t)

                        if n.type == 'method_invocation':
                            obj, nm = n.child_by_field_name('object'), n.child_by_field_name('name')
                            if nm:
                                raw = f'{text(obj)}::{text(nm)}' if obj else text(nm)
                                res, mode = symbol_table.resolve('JAVA', filename, cls_id, raw, local_scope)
                                relations.append(Relation(m_id, res, mode))
    return nodes, relations
