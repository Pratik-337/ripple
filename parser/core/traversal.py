def traverse(node):
    cursor = node.walk()
    visited_children = False

    while True:
        if not visited_children:
            yield cursor.node
            if cursor.goto_first_child():
                visited_children = False
                continue
            visited_children = True

        if cursor.goto_next_sibling():
            visited_children = False
            continue

        if not cursor.goto_parent():
            break
