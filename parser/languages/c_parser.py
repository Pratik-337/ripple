from parser.core.node import Node
from parser.core.relation import Relation
from parser.core.traversal import traverse
from parser.core.util import normalize_call_name

def parse_c(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes, relations, src = [], [], source_code.encode('utf8')
    def text(n): return src[n.start_byte:n.end_byte].decode('utf8', errors='ignore')
    
    current_function = None

    for node in traverse(root):
        if node.type == 'function_definition':
            decl = node.child_by_field_name('declarator')
            if decl:
                # Find the actual name within the declarator
                name_node = None
                for n in traverse(decl):
                    if n.type == 'identifier':
                        name_node = n
                        break
                
                if name_node:
                    f_nm = text(name_node)
                    fn_id = f'c::{filename}::{f_nm}()'
                    nodes.append(Node(fn_id, 'FUNCTION', 'C', filename, node.start_point[0]+1, node.end_point[0]+1))
                    symbol_table.add_definition('C', fn_id, 'FUNCTION', filename, None, node.start_point[0]+1, node.end_point[0]+1, body_text=text(node))
                    current_function = fn_id

                    body = node.child_by_field_name('body')
                    if body:
                        for sub in traverse(body):
                            if sub.type == 'call_expression':
                                f_call = sub.child_by_field_name('function')
                                if f_call:
                                    res, mode = symbol_table.resolve('C', filename, None, normalize_call_name(text(f_call)))
                                    relations.append(Relation(fn_id, res, mode))
        
        elif node.type == 'preproc_include':
            path = node.child_by_field_name('path')
            if path:
                inc_id = text(path).strip('"<>')
                nodes.append(Node(inc_id, 'IMPORT', 'C', filename, node.start_point[0]+1, node.end_point[0]+1))
                symbol_table.add_import(filename, inc_id, inc_id)

    return nodes, relations
