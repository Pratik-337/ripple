from ..core.node import Node
from ..core.relation import Relation
from ..core.traversal import traverse
from ..core.util import normalize_call_name

def parse_python(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes, relations, src = [], [], source_code.encode('utf8')
    def text(n): return src[n.start_byte:n.end_byte].decode('utf8', errors='ignore')
    
    scope_stack = []
    
    for node in traverse(root):
        while scope_stack and node.start_byte >= scope_stack[-1]['end_byte']:
            scope_stack.pop()

        curr_owner = scope_stack[-1]['id'] if scope_stack else None

        if node.type == 'class_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                cls_name = text(name_node)
                cls_id = f'python::{filename}::{cls_name}'
                nodes.append(Node(cls_id, 'CLASS', 'PYTHON', filename, node.start_point[0]+1, node.end_point[0]+1))
                symbol_table.add_definition('PYTHON', cls_id, 'CLASS', filename, curr_owner, node.start_point[0]+1, node.end_point[0]+1, body_text=text(node))
                scope_stack.append({'id': cls_id, 'type': 'CLASS', 'end_byte': node.end_byte})
        
        elif node.type == 'function_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                func_name = text(name_node)
                sig = '()' # Python signatures are tricky with default params, using () as standard
                func_id_suffix = f'{func_name}{sig}'

                if curr_owner and scope_stack[-1]['type'] == 'CLASS':
                    func_id = f'{curr_owner}::{func_id_suffix}'
                    nodes.append(Node(func_id, 'METHOD', 'PYTHON', filename, node.start_point[0]+1, node.end_point[0]+1))
                    relations.append(Relation(curr_owner, func_id, 'CONTAINS'))
                    symbol_table.add_definition('PYTHON', func_id, 'METHOD', filename, curr_owner, node.start_point[0]+1, node.end_point[0]+1, body_text=text(node))
                else:
                    func_id = f'python::{filename}::{func_id_suffix}'
                    nodes.append(Node(func_id, 'FUNCTION', 'PYTHON', filename, node.start_point[0]+1, node.end_point[0]+1))
                    symbol_table.add_definition('PYTHON', func_id, 'FUNCTION', filename, None, node.start_point[0]+1, node.end_point[0]+1, body_text=text(node))
                
                scope_stack.append({'id': func_id, 'type': 'FUNCTION', 'end_byte': node.end_byte})

                body = node.child_by_field_name('body')
                if body:
                    local_scope = {}
                    for sub_node in traverse(body):
                        if sub_node.type == 'call':
                            func_call_node = sub_node.child_by_field_name('function')
                            if func_call_node:
                                call_name = normalize_call_name(text(func_call_node))
                                res, mode = symbol_table.resolve('PYTHON', filename, func_id, call_name, local_scope)
                                if res:
                                    relations.append(Relation(func_id, res, mode))
                        elif sub_node.type == 'assignment':
                            left = sub_node.child_by_field_name('left')
                            right = sub_node.child_by_field_name('right')
                            if left and right and left.type == 'identifier':
                                if (right.type == 'call' and right.child_by_field_name('function') and 
                                    (text(right.child_by_field_name('function')), 'CLASS') in [(d['id'], d['type']) for d in symbol_table.definitions.values()]):
                                    local_scope[text(left)] = text(right.child_by_field_name('function'))

    return nodes, relations
