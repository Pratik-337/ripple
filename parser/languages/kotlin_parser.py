from parser.core.node import Node
from parser.core.relation import Relation
from parser.core.traversal import traverse
from parser.core.util import normalize_call_name

def parse_kotlin(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes, relations, src = [], [], source_code.encode('utf8')
    def text(n): return src[n.start_byte:n.end_byte].decode('utf8', errors='ignore')
    
    pkg = 'main'
    for c in root.children:
        if c.type == 'package_header':
            n = c.child_by_field_name('name')
            if n: pkg = text(n).strip()

    scope_stack = []
    for node in traverse(root):
        while scope_stack and node.start_byte > scope_stack[-1]['end']: scope_stack.pop()
        curr_owner = scope_stack[-1]['id'] if scope_stack else None

        if node.type in {'class_declaration', 'object_declaration', 'interface_declaration', 'companion_object'}:
            nm = node.child_by_field_name('name')
            r_nm = text(nm).strip() if nm else ('Companion' if node.type == 'companion_object' else None)
            if not r_nm: continue
            kind = 'INTERFACE' if node.type == 'interface_declaration' or 'interface' in text(node).split('{')[0] else 'CLASS'
            fqn = f'{curr_owner}::{r_nm}' if curr_owner else f'kotlin::{pkg}::{r_nm}'
            nodes.append(Node(fqn, kind, 'KOTLIN', filename, node.start_point[0]+1, node.end_point[0]+1))
            symbol_table.add_definition('KOTLIN', fqn, kind, filename, None, node.start_point[0]+1, node.end_point[0]+1)
            
            for c in node.children:
                if c.type in {'delegation_specifier', 'delegation_specifiers'}:
                    for spec in traverse(c):
                        if spec.type in {'user_type', 'type_identifier'}:
                            target = f'kotlin::{pkg}::{text(spec).split("<")[0].split("(")[0].strip()}'
                            relations.append(Relation(fqn, target, 'IMPLEMENTS'))
                            symbol_table.hierarchy['KOTLIN'][fqn].add(target)
            scope_stack.append({'id': fqn, 'end': node.end_byte})

        elif node.type == 'function_declaration':
            nm = node.child_by_field_name('name')
            if not nm: continue
            r_nm = text(nm).strip()
            
            # Simple parameter extraction for Kotlin
            params = node.child_by_field_name('parameters')
            sig = '()'
            if params:
                types = []
                for p in params.children:
                    if p.type == 'parameter':
                        t = p.child_by_field_name('type')
                        if t: types.append(text(t))
                sig = '(' + ','.join(types) + ')'

            fn_id = f'{curr_owner}::{r_nm}{sig}' if curr_owner else f'kotlin::{pkg}::_::{r_nm}{sig}'
            nodes.append(Node(fn_id, 'METHOD' if curr_owner else 'FUNCTION', 'KOTLIN', filename, node.start_point[0]+1, node.end_point[0]+1))
            symbol_table.add_definition('KOTLIN', fn_id, 'METHOD' if curr_owner else 'FUNCTION', filename, curr_owner, node.start_point[0]+1, node.end_point[0]+1)
            if curr_owner: relations.append(Relation(curr_owner, fn_id, 'CONTAINS'))
            
            body = node.child_by_field_name('body')
            if body:
                for sub in traverse(body):
                    if sub.type == 'call_expression':
                        fexpr = sub.child_by_field_name('function')
                        if fexpr:
                            res, mode = symbol_table.resolve('KOTLIN', filename, curr_owner, normalize_call_name(text(fexpr)))
                            if res: relations.append(Relation(fn_id, res, mode))
    return nodes, relations
