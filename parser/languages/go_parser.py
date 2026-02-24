from parser.core.node import Node
from parser.core.relation import Relation
from parser.core.traversal import traverse
from parser.core.util import normalize_call_name

def parse_go(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes, relations, src = [], [], source_code.encode('utf8')
    def text(n): return src[n.start_byte:n.end_byte].decode('utf8', errors='ignore')

    pkg = 'main'
    for c in root.children:
        if c.type == 'package_clause':
            nm = c.child_by_field_name('name')
            if nm: pkg = text(nm)

    for child in root.children:
        if child.type == 'function_declaration':
            nm = child.child_by_field_name('name')
            if not nm: continue
            f_nm = text(nm)
            rec_name = None
            rec_node = child.child_by_field_name('receiver')
            if rec_node:
                for r in traverse(rec_node): 
                    if r.type == 'type_identifier': rec_name = text(r); break

            owner = f'go::{pkg}::{rec_name}' if rec_name else None
            sig = '()' # Go signatures could be parsed from parameters
            fn_id = f'{owner}::{f_nm}{sig}' if owner else f'go::{pkg}::{f_nm}{sig}'
            kind = 'METHOD' if rec_name else 'FUNCTION'

            nodes.append(Node(fn_id, kind, 'GO', filename, child.start_point[0]+1, child.end_point[0]+1))
            symbol_table.add_definition('GO', fn_id, kind, filename, owner, child.start_point[0]+1, child.end_point[0]+1, body_text=text(child))
            if owner: relations.append(Relation(owner, fn_id, 'CONTAINS'))

            body = child.child_by_field_name('body')
            if body:
                for n in traverse(body):
                    if n.type == 'call_expression':
                        fn_p = n.child_by_field_name('function')
                        if fn_p:
                            res, mode = symbol_table.resolve('GO', filename, owner, normalize_call_name(text(fn_p)))
                            relations.append(Relation(fn_id, res, mode))
    return nodes, relations
