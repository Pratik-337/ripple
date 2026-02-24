from parser.core.node import Node
from parser.core.relation import Relation
from parser.core.traversal import traverse
from parser.core.util import normalize_call_name

def parse_typescript(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes, relations, src = [], [], source_code.encode('utf8')
    def text(n): return src[n.start_byte:n.end_byte].decode('utf8', errors='ignore')
    
    scope_stack = []

    for node in traverse(root):
        while scope_stack and node.start_byte >= scope_stack[-1]['end']: scope_stack.pop()
        curr_owner = scope_stack[-1]['id'] if scope_stack else None

        if node.type == 'class_declaration':
            nm = node.child_by_field_name('name')
            if nm:
                cls_id = f'typescript::{filename}::{text(nm)}'
                nodes.append(Node(cls_id, 'CLASS', 'TYPESCRIPT', filename, node.start_point[0]+1, node.end_point[0]+1))
                symbol_table.add_definition('TYPESCRIPT', cls_id, 'CLASS', filename, curr_owner, node.start_point[0]+1, node.end_point[0]+1, body_text=text(node))
                scope_stack.append({'id': cls_id, 'end': node.end_byte})

        elif node.type in {'function_declaration', 'method_definition'}:
            nm = node.child_by_field_name('name')
            if nm:
                f_nm = text(nm)
                fn_id = f'{curr_owner}::{f_nm}()' if curr_owner else f'typescript::{filename}::{f_nm}()'
                nodes.append(Node(fn_id, 'METHOD' if curr_owner else 'FUNCTION', 'TYPESCRIPT', filename, node.start_point[0]+1, node.end_point[0]+1))
                symbol_table.add_definition('TYPESCRIPT', fn_id, 'METHOD' if curr_owner else 'FUNCTION', filename, curr_owner, node.start_point[0]+1, node.end_point[0]+1, body_text=text(node))
                if curr_owner: relations.append(Relation(curr_owner, fn_id, 'CONTAINS'))

                body = node.child_by_field_name('body')
                if body:
                    for sub in traverse(body):
                        if sub.type == 'call_expression':
                            f_call = sub.child_by_field_name('function')
                            if f_call:
                                res, mode = symbol_table.resolve('TYPESCRIPT', filename, curr_owner, normalize_call_name(text(f_call)))
                                relations.append(Relation(fn_id, res, mode))
    return nodes, relations
