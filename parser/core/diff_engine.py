import hashlib

def categorize_change(old_node, new_node):
    """
    Compares two versions of a node (from SymbolTable) and returns the change type.
    """
    if not old_node and not new_node:
        return 'NO_CHANGE'
    if not old_node:
        return 'NEW_DEFINITION'
    if not new_node:
        return 'DELETED_DEFINITION'
    
    # Compare IDs (includes signatures now!)
    old_id = old_node.get('id')
    new_id = new_node.get('id')

    if old_id != new_id:
        return 'SIGNATURE_CHANGE'
    
    # Compare body hashes for logic changes
    old_hash = old_node.get('body_hash')
    new_hash = new_node.get('body_hash')
    
    if old_hash != new_hash:
        return 'LOGIC_CHANGE'
    
    # If lines changed but hash didn't, it might be whitespace/metadata
    if old_node.get('start') != new_node.get('start') or old_node.get('end') != new_node.get('end'):
        return 'METADATA_CHANGE'

    return 'NO_CHANGE'

def find_changed_nodes(old_symbol_table, new_symbol_table):
    """
    Returns a map of node_id -> change_type
    """
    changes = {}
    all_keys = set(old_symbol_table.definitions.keys()) | set(new_symbol_table.definitions.keys())
    
    for key in all_keys:
        old = old_symbol_table.definitions.get(key)
        new = new_symbol_table.definitions.get(key)
        
        ctype = categorize_change(old, new)
        if ctype != 'NO_CHANGE':
            # Use the FQN from the key (lang, fqn)
            changes[key[1]] = ctype
            
    return changes
