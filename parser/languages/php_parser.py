from ..core.node import Node
from ..core.relation import Relation
from ..core.traversal import traverse
from ..core.util import normalize_call_name

def parse_php(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes, relations, src = [], [], source_code.encode('utf8')
    def text(n): return src[n.start_byte:n.end_byte].decode('utf8')

    scope_stack = []
    for node in traverse(root):
        while scope_stack and node.start_byte > scope_stack[-1]['end']: scope_stack.pop()
        curr_owner = scope_stack[-1]['id'] if scope_stack else None

        if node.type == 'class_declaration':
            nm = node.child_by_field_name('name')
            if nm:
                fqn = f'php::{filename}::{text(nm)}'
                nodes.append(Node(fqn, 'CLASS', 'PHP', filename, node.start_point[0]+1, node.end_point[0]+1))
                symbol_table.add_definition('PHP', fqn, 'CLASS', filename, None, node.start_point[0]+1, node.end_point[0]+1)
                scope_stack.append({'id': fqn, 'end': node.end_byte})

        elif node.type in {'function_definition', 'method_declaration'}:
            nm = node.child_by_field_name('name')
            if nm:
                r_nm = text(nm)
                fn_id = f'{curr_owner}.{r_nm}' if curr_owner else f'php::{filename}::{r_nm}'
                nodes.append(Node(fn_id, 'METHOD' if curr_owner else 'FUNCTION', 'PHP', filename, node.start_point[0]+1, node.end_point[0]+1))
                symbol_table.add_definition('PHP', fn_id, 'METHOD' if curr_owner else 'FUNCTION', filename, curr_owner, node.start_point[0]+1, node.end_point[0]+1)
                if curr_owner: relations.append(Relation(curr_owner, fn_id, 'CONTAINS'))

                body = node.child_by_field_name('body')
                if body:
                    for sub in traverse(body):
                        if sub.type in {'function_call_expression', 'member_call_expression'}:
                            fn_p = sub.child_by_field_name('function') or sub.child_by_field_name('name')
                            if fn_p:
                                res, mode = symbol_table.resolve('PHP', filename, curr_owner, normalize_call_name(text(fn_p)))
                                relations.append(Relation(fn_id, res, mode))
    return nodes, relations
