import re

class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

def parse_expression(expr):
    def precedence(op):
        if op in ('+', '-'): return 1
        if op in ('*', '/'): return 2
        return 0
    output = []
    ops = []
    tokens = re.findall(r'\d+|[a-zA-Z_]\w*|[()+\-*/]', expr)
    for token in tokens:
        if re.match(r'\d+|[a-zA-Z_]\w*', token):
            output.append(token)
        elif token == '(': ops.append(token)
        elif token == ')':
            while ops and ops[-1] != '(': output.append(ops.pop())
            ops.pop()
        else:
            while ops and ops[-1] != '(' and precedence(ops[-1]) >= precedence(token):
                output.append(ops.pop())
            ops.append(token)
    while ops: output.append(ops.pop())
    return build_tree_from_postfix(output)

def build_tree_from_postfix(postfix):
    stack = []
    for token in postfix:
        if token in '+-*/':
            right = stack.pop()
            left = stack.pop()
            stack.append(Node(token, left, right))
        else:
            stack.append(Node(token))
    return stack[0] if stack else None

def tree_to_dict(node):
    if not node:
        return None
    return {
        'value': node.value,
        'left': tree_to_dict(node.left),
        'right': tree_to_dict(node.right)
    }

def tree_to_visjs(node):
    nodes = []
    edges = []
    def traverse(n, idx=1):
        if not n:
            return None, idx
        my_id = idx
        nodes.append({'id': my_id, 'label': str(n.value)})
        if n.left:
            left_id, idx = traverse(n.left, idx+1)
            edges.append({'from': my_id, 'to': left_id})
        if n.right:
            right_id, idx = traverse(n.right, idx+1)
            edges.append({'from': my_id, 'to': right_id})
        return my_id, idx
    traverse(node)
    return {'nodes': nodes, 'edges': edges} 