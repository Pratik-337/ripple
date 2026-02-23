from ..core.node import Node
from ..core.relation import Relation
from ..core.traversal import traverse
from ..core.util import normalize_call_name

def parse_java(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes, relations, src = [], [], source_code.encode('utf8')
    def text(n): return src[n.start_byte:n.end_byte].decode('utf8')
    
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
            symbol_table.add_definition('JAVA', cls_id, kind, filename, None, c.start_point[0]+1, c.end_point[0]+1)

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
            for m in body.children:
                if m.type == 'method_declaration':
                    mnm = m.child_by_field_name('name')
                    if not mnm: continue
                    m_id = f'{cls_id}.{text(mnm)}'
                    nodes.append(Node(m_id, 'METHOD', 'JAVA', filename, m.start_point[0]+1, m.end_point[0]+1))
                    relations.append(Relation(cls_id, m_id, 'CONTAINS'))
                    symbol_table.add_definition('JAVA', m_id, 'METHOD', filename, cls_id, m.start_point[0]+1, m.end_point[0]+1)
                    
                    for n in traverse(m):
                        if n.type == 'method_invocation':
                            obj, nm = n.child_by_field_name('object'), n.child_by_field_name('name')
                            if nm:
                                raw = f'{text(obj)}.{text(nm)}' if obj else text(nm)
                                res, mode = symbol_table.resolve('JAVA', filename, cls_id, raw)
                                relations.append(Relation(m_id, res, mode))
    return nodes, relations
