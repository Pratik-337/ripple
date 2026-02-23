from ..core.node import Node
from ..core.relation import Relation
from ..core.traversal import traverse
from ..core.util import normalize_call_name

def parse_python(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes, relations, src = [], [], source_code.encode('utf8')
    def text(n): return src[n.start_byte:n.end_byte].decode('utf8')

    for c in root.children:
        if c.type == 'class_definition':
            nm = text(c.child_by_field_name('name'))
            cls_id = f'python::{filename}::{nm}'
            nodes.append(Node(cls_id, 'CLASS', 'PYTHON', filename, c.start_point[0]+1, c.end_point[0]+1))
            symbol_table.add_definition('PYTHON', cls_id, 'CLASS', filename, None, c.start_point[0]+1, c.end_point[0]+1)
            
            args = c.child_by_field_name('arguments')
            if args:
                for arg in args.children:
                    if arg.type == 'identifier':
                        base = f'python::{filename}::{text(arg)}'
                        relations.append(Relation(cls_id, base, 'IMPLEMENTS'))
                        symbol_table.hierarchy['PYTHON'][cls_id].add(base)

            body = c.child_by_field_name('body')
            for m in body.children if body else []:
                if m.type == 'function_definition':
                    mnm = text(m.child_by_field_name('name'))
                    m_id = f'{cls_id}::{mnm}()'
                    nodes.append(Node(m_id, 'METHOD', 'PYTHON', filename, m.start_point[0]+1, m.end_point[0]+1))
                    relations.append(Relation(cls_id, m_id, 'CONTAINS'))
                    symbol_table.add_definition('PYTHON', m_id, 'METHOD', filename, cls_id, m.start_point[0]+1, m.end_point[0]+1)
                    
                    for n in traverse(m):
                        if n.type == 'call':
                            fn = n.child_by_field_name('function')
                            if fn:
                                res, mode = symbol_table.resolve('PYTHON', filename, cls_id, normalize_call_name(text(fn)))
                                relations.append(Relation(m_id, res, mode))

        elif c.type == 'function_definition':
            fnm = text(c.child_by_field_name('name'))
            f_id = f'python::{filename}::{fnm}'
            nodes.append(Node(f_id, 'FUNCTION', 'PYTHON', filename, c.start_point[0]+1, c.end_point[0]+1))
            symbol_table.add_definition('PYTHON', f_id, 'FUNCTION', filename, None, c.start_point[0]+1, c.end_point[0]+1)
            for n in traverse(c):
                if n.type == 'call':
                    fn = n.child_by_field_name('function')
                    if fn:
                        res, mode = symbol_table.resolve('PYTHON', filename, None, normalize_call_name(text(fn)))
                        relations.append(Relation(f_id, res, mode))
    return nodes, relations
