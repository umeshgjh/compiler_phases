import re

def infix_to_postfix(expr):
    try:
        # Remove all spaces and ensure proper spacing around operators
        expr = re.sub(r'\s+', '', expr)
        expr = re.sub(r'([+\-*/^()])', r' \1 ', expr)
        expr = expr.strip()
        
        precedence = {'+':1, '-':1, '*':2, '/':2, '^':3}
        stack = []
        output = []
        
        # Tokenize the expression
        tokens = expr.split()
        
        for token in tokens:
            if re.match(r'^[a-zA-Z0-9_]+$', token):  # Operand
                output.append(token)
            elif token == '(':
                stack.append(token)
            elif token == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                if not stack:  # No matching '(' found
                    raise ValueError("Mismatched parentheses")
                stack.pop()  # Remove '('
            elif token in precedence:  # Operator
                while (stack and stack[-1] != '(' and 
                       precedence.get(stack[-1], 0) >= precedence[token]):
                    output.append(stack.pop())
                stack.append(token)
            else:
                raise ValueError(f"Invalid token: {token}")
        
        # Pop remaining operators
        while stack:
            if stack[-1] == '(':
                raise ValueError("Mismatched parentheses")
            output.append(stack.pop())
        
        return ' '.join(output)
    except Exception as e:
        raise ValueError(f"Error in infix to postfix conversion: {str(e)}")

def postfix_to_infix(expr):
    try:
        # Split on spaces and filter out empty strings
        tokens = [t for t in expr.split() if t]
        
        if not tokens:
            raise ValueError("Empty expression")
            
        stack = []
        operators = {'+', '-', '*', '/', '^'}
        
        for token in tokens:
            if re.match(r'^[a-zA-Z0-9_]+$', token):  # Operand
                stack.append(token)
            elif token in operators:  # Operator
                if len(stack) < 2:
                    raise ValueError("Invalid postfix expression: insufficient operands")
                b = stack.pop()
                a = stack.pop()
                # Add parentheses only when necessary
                if token in {'+', '-'} and any(op in a for op in {'*', '/'}):
                    a = f"({a})"
                if token in {'+', '-'} and any(op in b for op in {'*', '/'}):
                    b = f"({b})"
                stack.append(f"{a} {token} {b}")
            else:
                raise ValueError(f"Invalid token: {token}")
        
        if len(stack) != 1:
            raise ValueError("Invalid postfix expression: too many operands")
            
        return stack[0]
    except Exception as e:
        raise ValueError(f"Error in postfix to infix conversion: {str(e)}") 