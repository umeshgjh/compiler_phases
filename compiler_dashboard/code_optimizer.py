import re

def optimize_three_address_code(code):
    lines = [line.strip().rstrip(';') for line in code.strip().split('\n') if line.strip()]
    assigns = []
    uses = set()
    expr_to_var = {}
    var_to_expr = {}
    optimized = []

    # First pass: parse assignments and collect variable usage
    for line in lines:
        m = re.match(r'(\w+)\s*=\s*(.+)', line)
        if m:
            var, expr = m.group(1), m.group(2)
            assigns.append((var, expr))
            var_to_expr[var] = expr
            tokens = re.findall(r'[a-zA-Z_]\w*', expr)
            for t in tokens:
                if t != var:
                    uses.add(t)
        else:
            assigns.append((None, line))

    # Second pass: constant folding and algebraic simplification
    folded = []
    for var, expr in assigns:
        if var is None:
            folded.append((var, expr))
            continue
        # Constant folding
        const_match = re.match(r'(\d+)\s*([\+\-\*/])\s*(\d+)', expr)
        if const_match:
            a, op, b = const_match.groups()
            a, b = int(a), int(b)
            if op == '+': val = a + b
            elif op == '-': val = a - b
            elif op == '*': val = a * b
            elif op == '/': val = a // b if b != 0 else 0
            expr = str(val)
        # Algebraic simplification
        if re.match(r'(\w+)\s*\*\s*1$', expr): expr = re.sub(r'\s*\*\s*1$', '', expr)
        elif re.match(r'1\s*\*\s*(\w+)$', expr): expr = re.sub(r'^1\s*\*\s*', '', expr)
        elif re.match(r'(\w+)\s*\+\s*0$', expr): expr = re.sub(r'\s*\+\s*0$', '', expr)
        elif re.match(r'0\s*\+\s*(\w+)$', expr): expr = re.sub(r'^0\s*\+\s*', '', expr)
        elif re.match(r'(\w+)\s*-\s*0$', expr): expr = re.sub(r'\s*-\s*0$', '', expr)
        elif re.match(r'(\w+)\s*\*\s*0$', expr) or re.match(r'0\s*\*\s*(\w+)$', expr): expr = '0'
        elif re.match(r'(\w+)\s*/\s*1$', expr): expr = re.sub(r'\s*/\s*1$', '', expr)
        folded.append((var, expr))

    # Third pass: advanced common subexpression elimination and copy propagation
    expr_seen = {}
    var_copies = {}
    cse = []
    for var, expr in folded:
        if var is None:
            cse.append((var, expr))
            continue
        if expr in expr_seen:
            # Only keep if this variable is used
            if var in uses:
                cse.append((var, expr_seen[expr]))
                var_copies[var] = expr_seen[expr]
            # If not used, skip
        else:
            expr_seen[expr] = var
            cse.append((var, expr))

    # Fourth pass: propagate copy chains
    final_assigns = []
    var_map = {}
    for var, expr in cse:
        if var is None:
            final_assigns.append((var, expr))
            continue
        # Propagate chains: a = b, b = c, ... => a = final value
        target = expr
        while target in var_copies:
            target = var_copies[target]
        var_map[var] = target
        final_assigns.append((var, target))

    # Fifth pass: remove assignments to unused variables and redundant chains
    used = set(uses)
    if final_assigns:
        last_var = None
        for v, _ in reversed(final_assigns):
            if v is not None:
                last_var = v
                break
        if last_var:
            used.add(last_var)
    kept = set()
    output = []
    for i, (var, expr) in enumerate(final_assigns):
        if var is None:
            output.append(expr)
            continue
        if var not in used or var in kept:
            continue
        if re.match(r'^[a-zA-Z_]\w*$', expr) and expr in used and var != expr:
            if var not in uses:
                continue
        output.append(f"{var} = {expr};")
        kept.add(var)
    return '\n'.join(output) 