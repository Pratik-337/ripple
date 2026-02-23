from ..core.node import Node
from ..core.relation import Relation
from ..core.traversal import traverse
from ..core.util import normalize_call_name

def parse_js_ts(tree, source_code, filename, symbol_table, lang):
    root = tree.root_node
    nodes, relations, src = [], [], source_code.encode('utf8')
    def text(n): return src[n.start_byte:n.end_byte].decode('utf8')

    scope_stack = []
    for node in traverse(root):
        while scope_stack and node.start_byte > scope_stack[-1]['end']: scope_stack.pop()
        curr_owner = scope_stack[-1]['id'] if scope_stack else None

        if node.type in {'class_declaration', 'interface_declaration', 'class'}:
            nm = node.child_by_field_name('name')
            if not nm: continue
            r_nm = text(nm)
            kind = 'INTERFACE' if 'interface' in node.type else 'CLASS'
            fqn = f'javascript::{r_nm}' if curr_owner else f'javascript::{filename}::{r_nm}'
            nodes.append(Node(fqn, kind, lang, filename, node.start_point[0]+1, node.end_point[0]+1))
            symbol_table.add_definition(lang, fqn, kind, filename, None, node.start_point[0]+1, node.end_point[0]+1)
            scope_stack.append({'id': fqn, 'end': node.end_byte})

        elif node.type in {'method_definition', 'function_declaration'}:
            nm = node.child_by_field_name('name')
            if not nm: continue
            r_nm = text(nm)
            fn_id = f'{curr_owner}::{r_nm}()' if curr_owner else f'javascript::{filename}::{r_nm}()'
            nodes.append(Node(fn_id, 'METHOD' if curr_owner else 'FUNCTION', lang, filename, node.start_point[0]+1, node.end_point[0]+1))
            symbol_table.add_definition(lang, fn_id, 'METHOD' if curr_owner else 'FUNCTION', filename, curr_owner, node.start_point[0]+1, node.end_point[0]+1)
            if curr_owner: relations.append(Relation(curr_owner, fn_id, 'CONTAINS'))

            body = node.child_by_field_name('body')
            if body:
                for sub in traverse(body):
                    if sub.type == 'call_expression':
                        fexpr = sub.child_by_field_name('function')
                        if fexpr:
                            res, mode = symbol_table.resolve(lang, filename, curr_owner, normalize_call_name(text(fexpr)))
                            relations.append(Relation(fn_id, res, mode))
    return nodes, relations

def parse_javascript(tree, source_code, filename, symbol_table):
    return parse_js_ts(tree, source_code, filename, symbol_table, 'JAVASCRIPT')
