from parser.core.node import Node
from parser.core.relation import Relation
from parser.core.traversal import traverse
from parser.core.util import normalize_call_name

def parse_cpp(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes, relations, src = [], [], source_code.encode('utf8')
    def text(n): return src[n.start_byte:n.end_byte].decode('utf8', errors='ignore')
    
    scope_stack = []

    for node in traverse(root):
        while scope_stack and node.start_byte >= scope_stack[-1]['end']: scope_stack.pop()
        curr_owner = scope_stack[-1]['id'] if scope_stack else None

        if node.type in {'class_specifier', 'struct_specifier'}:
            nm = node.child_by_field_name('name')
            if nm:
                cls_nm = text(nm)
                cls_id = f'cpp::{filename}::{cls_nm}'
                nodes.append(Node(cls_id, 'CLASS', 'CPP', filename, node.start_point[0]+1, node.end_point[0]+1))
                symbol_table.add_definition('CPP', cls_id, 'CLASS', filename, curr_owner, node.start_point[0]+1, node.end_point[0]+1, body_text=text(node))
                scope_stack.append({'id': cls_id, 'end': node.end_byte})

        elif node.type == 'function_definition':
            decl = node.child_by_field_name('declarator')
            if decl:
                name_node = None
                for n in traverse(decl):
                    if n.type == 'field_identifier' or n.type == 'identifier':
                        name_node = n
                        break
                
                if name_node:
                    f_nm = text(name_node)
                    fn_id = f'{curr_owner}::{f_nm}()' if curr_owner else f'cpp::{filename}::{f_nm}()'
                    nodes.append(Node(fn_id, 'METHOD' if curr_owner else 'FUNCTION', 'CPP', filename, node.start_point[0]+1, node.end_point[0]+1))
                    symbol_table.add_definition('CPP', fn_id, 'METHOD' if curr_owner else 'FUNCTION', filename, curr_owner, node.start_point[0]+1, node.end_point[0]+1, body_text=text(node))
                    if curr_owner: relations.append(Relation(curr_owner, fn_id, 'CONTAINS'))

                    body = node.child_by_field_name('body')
                    if body:
                        for sub in traverse(body):
                            if sub.type == 'call_expression':
                                f_call = sub.child_by_field_name('function')
                                if f_call:
                                    res, mode = symbol_table.resolve('CPP', filename, curr_owner, normalize_call_name(text(f_call)))
                                    relations.append(Relation(fn_id, res, mode))
        
        elif node.type == 'preproc_include':
            path = node.child_by_field_name('path')
            if path:
                inc_id = text(path).strip('"<>')
                nodes.append(Node(inc_id, 'IMPORT', 'CPP', filename, node.start_point[0]+1, node.end_point[0]+1))
                symbol_table.add_import(filename, inc_id, inc_id)

    return nodes, relations
