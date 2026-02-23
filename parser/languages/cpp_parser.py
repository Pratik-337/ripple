from ..core.node import Node
from ..core.relation import Relation
from ..core.traversal import traverse
from ..core.util import normalize_call_name

def parse_cpp_cpp(tree, source_code, filename, symbol_table, lang):
    root = tree.root_node
    nodes, relations, src = [], [], source_code.encode('utf8')
    def text(n): return src[n.start_byte:n.end_byte].decode('utf8', errors='ignore')

    scope_stack = []
    for node in traverse(root):
        while scope_stack and node.start_byte > scope_stack[-1]['end']: scope_stack.pop()
        curr_owner = scope_stack[-1]['id'] if scope_stack else None

        if node.type == 'preproc_include':
            p = node.child_by_field_name('path')
            if p: nodes.append(Node(text(p).strip('"<>'), 'IMPORT', lang, filename, node.start_point[0]+1, node.end_point[0]+1))

        elif node.type in {'class_specifier', 'struct_specifier'}:
            nm = node.child_by_field_name('name')
            if nm:
                fqn = f'{lang.lower()}::{filename}::{text(nm)}'
                nodes.append(Node(fqn, 'CLASS', lang, filename, node.start_point[0]+1, node.end_point[0]+1))
                symbol_table.add_definition(lang, fqn, 'CLASS', filename, None, node.start_point[0]+1, node.end_point[0]+1)
                
                # CPP Inheritance
                base = node.child_by_field_name('base_class')
                if base:
                    for b in traverse(base):
                        if b.type == 'type_identifier':
                            target = f'{lang.lower()}::{filename}::{text(b)}'
                            relations.append(Relation(fqn, target, 'IMPLEMENTS'))
                            symbol_table.hierarchy[lang][fqn].add(target)
                scope_stack.append({'id': fqn, 'end': node.end_byte})

        elif node.type == 'function_definition':
            decl = node.child_by_field_name('declarator')
            if decl:
                actual = decl
                while actual.child_by_field_name('declarator'): actual = actual.child_by_field_name('declarator')
                nm = actual.child_by_field_name('declarator') or actual
                r_nm = text(nm)
                fn_id = f'{curr_owner}.{r_nm}' if curr_owner else f'{lang.lower()}::{filename}::{r_nm}'
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

def parse_cpp(tree, source_code, filename, symbol_table):
    return parse_cpp_cpp(tree, source_code, filename, symbol_table, 'CPP')
