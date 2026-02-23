from parser.core.node import Node
from parser.core.relation import Relation
from parser.core.traversal import traverse
from parser.core.util import normalize_call_name

def parse_rust(tree, source_code, filename, symbol_table):
    root = tree.root_node
    nodes, relations, src = [], [], source_code.encode('utf8')
    def text(n): return src[n.start_byte:n.end_byte].decode('utf8', errors='ignore')
    
    crate, module = 'crate', 'main'
    impl_stack = []
    current_function = None

    for node in traverse(root):
        while impl_stack and node.start_byte > impl_stack[-1]['end']: impl_stack.pop()
        curr_struct = impl_stack[-1]['struct_id'] if impl_stack else None
        curr_trait = impl_stack[-1].get('trait_id') if impl_stack else None

        if node.type == 'struct_item':
            nm = node.child_by_field_name('name')
            if nm:
                s_id = f'rust::{crate}::{module}::{text(nm)}'
                nodes.append(Node(s_id, 'STRUCT', 'RUST', filename, node.start_point[0]+1, node.end_point[0]+1))
                symbol_table.add_definition('RUST', s_id, 'STRUCT', filename, None, node.start_point[0]+1, node.end_point[0]+1)

        elif node.type == 'trait_item':
            nm = node.child_by_field_name('name')
            if nm:
                t_id = f'rust::{crate}::{module}::{text(nm)}'
                nodes.append(Node(t_id, 'TRAIT', 'RUST', filename, node.start_point[0]+1, node.end_point[0]+1))
                symbol_table.add_definition('RUST', t_id, 'TRAIT', filename, None, node.start_point[0]+1, node.end_point[0]+1)

        elif node.type == 'impl_item':
            t_node = node.child_by_field_name('type')
            tr_node = node.child_by_field_name('trait')
            s_nm = text(t_node) if t_node else None
            s_id = f'rust::{crate}::{module}::{s_nm}' if s_nm else None
            entry = {'end': node.end_byte, 'struct_id': s_id}
            if tr_node:
                tr_id = f'rust::{crate}::{module}::{text(tr_node)}'
                entry['trait_id'] = tr_id
                if s_id: 
                    relations.append(Relation(s_id, tr_id, 'IMPLEMENTS'))
                    symbol_table.hierarchy['RUST'][s_id].add(tr_id)
            impl_stack.append(entry)

        elif node.type == 'function_item':
            nm = node.child_by_field_name('name')
            if nm:
                f_nm = text(nm)
                
                # Rust signatures are complex, using () as placeholder for now
                # In a full implementation, we would parse parameters and return types
                sig = '()'
                fn_id = f'{curr_struct}::{f_nm}{sig}' if curr_struct else f'rust::{crate}::{module}::_::{f_nm}{sig}'
                
                nodes.append(Node(fn_id, 'METHOD' if curr_struct else 'FUNCTION', 'RUST', filename, node.start_point[0]+1, node.end_point[0]+1))
                symbol_table.add_definition('RUST', fn_id, 'METHOD' if curr_struct else 'FUNCTION', filename, curr_struct, node.start_point[0]+1, node.end_point[0]+1)
                if curr_struct: relations.append(Relation(curr_struct, fn_id, 'CONTAINS'))
                current_function = fn_id

        elif node.type == 'call_expression':
            if not current_function: continue
            f_node = node.child_by_field_name('function')
            if f_node:
                res, mode = symbol_table.resolve('RUST', filename, curr_struct, normalize_call_name(text(f_node)))
                if res: relations.append(Relation(current_function, res, mode))
    return nodes, relations
