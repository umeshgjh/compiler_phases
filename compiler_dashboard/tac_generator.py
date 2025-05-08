import re

class ThreeAddressCodeGenerator:
    def __init__(self):
        self.temp_counter = 0
        self.label_counter = 0
        self.code = []
        self.symbol_table = {}
        self.quadruples = []
        self.triples = []
        self.indirect_triples = []

    def get_temp(self):
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def get_label(self):
        self.label_counter += 1
        return f"L{self.label_counter}"

    def generate(self, input_code):
        try:
            self.temp_counter = 0
            self.label_counter = 0
            self.code = []
            self.quadruples = []
            self.triples = []
            self.indirect_triples = []

            lines = input_code.strip().split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if not line or line.startswith('//'):
                    i += 1
                    continue

                if line.startswith('for'):
                    i = self._handle_for_loop(lines, i)
                elif line.startswith('if'):
                    i = self._handle_if_statement(lines, i)
                elif line.startswith('while'):
                    i = self._handle_while_loop(lines, i)
                elif '[' in line and '=' in line:
                    self._handle_array_operation(line)
                elif '=' in line:
                    self._handle_assignment(line)
                i += 1

            self._generate_quadruples()
            self._generate_triples()
            self._generate_indirect_triples()

            return {
                'three_address': self.code,
                'quadruple': self.quadruples,
                'triple': self.triples,
                'indirect_triple': self.indirect_triples
            }
        except Exception as e:
            return {'error': str(e)}

    def _generate_quadruples(self):
        for i, line in enumerate(self.code):
            # Only process valid assignment or operation lines
            if '=' in line and not line.strip().startswith('if'):
                left, right = line.split('=', 1)
                left = left.strip()
                right = right.strip()
                # Only one quadruple per operation/assignment
                if any(op in right for op in ['+', '-', '*', '/']):
                    op = next(op for op in ['+', '-', '*', '/'] if op in right)
                    op1, op2 = right.split(op)
                    self.quadruples.append({
                        'location': i,
                        'op': op,
                        'arg1': op1.strip(),
                        'arg2': op2.strip(),
                        'result': left
                    })
                else:
                    self.quadruples.append({
                        'location': i,
                        'op': '=',
                        'arg1': right,
                        'arg2': '',
                        'result': left
                    })
            elif 'ifFalse' in line:
                parts = line.split()
                condition = parts[1]
                target = parts[3]
                self.quadruples.append({
                    'location': i,
                    'op': 'ifFalse',
                    'arg1': condition,
                    'arg2': '',
                    'result': target
                })
            # Do not generate quadruples for label, goto, or malformed lines

    def _generate_triples(self):
        temp_to_location = {}
        # Map every result that is a temp variable to its location
        for i, quad in enumerate(self.quadruples):
            if isinstance(quad.get('result', None), str) and quad['result'].startswith('t'):
                temp_to_location[quad['result']] = i

        def arg_loc(arg):
            if isinstance(arg, str) and arg.startswith('t') and arg in temp_to_location:
                return temp_to_location[arg]
            return arg

        for i, quad in enumerate(self.quadruples):
            if quad['op'] == '=' or quad['op'] in ['+', '-', '*', '/']:
                self.triples.append({
                    'location': i,
                    'op': quad['op'],
                    'arg1': arg_loc(quad['arg1']),
                    'arg2': arg_loc(quad['arg2']) if quad['arg2'] else ''
                })
            elif quad['op'] == 'ifFalse':
                self.triples.append({
                    'location': i,
                    'op': 'ifFalse',
                    'arg1': arg_loc(quad['arg1']),
                    'arg2': quad['result']
                })
        # Do not generate triples for label, goto, or malformed lines

    def _generate_indirect_triples(self):
        self.indirect_triples = [{'pointer': 1000 + i, 'location': i} for i in range(len(self.triples))]

    def _handle_if_statement(self, lines, start_idx):
        if_line = lines[start_idx].strip()
        match = re.match(r'if\s*\((.*?)\)', if_line)
        if not match:
            raise ValueError("Invalid if statement syntax")

        condition = match.group(1).strip()
        if_end = self.get_label()
        else_label = self.get_label()

        # Handle condition
        if '==' in condition:
            left, right = condition.split('==')
            temp = self.get_temp()
            self.code.append(f"{temp} = {left.strip()} == {right.strip()}")
            self.code.append(f"ifFalse {temp} goto {else_label}")
        elif '!=' in condition:
            left, right = condition.split('!=')
            temp = self.get_temp()
            self.code.append(f"{temp} = {left.strip()} != {right.strip()}")
            self.code.append(f"ifFalse {temp} goto {else_label}")
        elif '<=' in condition:
            left, right = condition.split('<=')
            temp = self.get_temp()
            self.code.append(f"{temp} = {left.strip()} <= {right.strip()}")
            self.code.append(f"ifFalse {temp} goto {else_label}")
        elif '>=' in condition:
            left, right = condition.split('>=')
            temp = self.get_temp()
            self.code.append(f"{temp} = {left.strip()} >= {right.strip()}")
            self.code.append(f"ifFalse {temp} goto {else_label}")
        elif '<' in condition:
            left, right = condition.split('<')
            temp = self.get_temp()
            self.code.append(f"{temp} = {left.strip()} < {right.strip()}")
            self.code.append(f"ifFalse {temp} goto {else_label}")
        elif '>' in condition:
            left, right = condition.split('>')
            temp = self.get_temp()
            self.code.append(f"{temp} = {left.strip()} > {right.strip()}")
            self.code.append(f"ifFalse {temp} goto {else_label}")

        # Process if body
        idx = start_idx + 1
        brace_count = 1
        if_body = []
        while idx < len(lines) and brace_count > 0:
            line = lines[idx].strip()
            if '{' in line:
                brace_count += 1
            if '}' in line:
                brace_count -= 1
            if line and not line.startswith('}') and not line.startswith('{'):
                if '[' in line and '=' in line:
                    self._handle_array_operation(line)
                elif '=' in line:
                    self._handle_assignment(line)
            idx += 1
        self.code.append(f"goto {if_end}")
        self.code.append(f"{else_label}:")
        if idx < len(lines) and lines[idx].strip().startswith('else'):
            idx += 1
            brace_count = 1
            while idx < len(lines) and brace_count > 0:
                line = lines[idx].strip()
                if '{' in line:
                    brace_count += 1
                if '}' in line:
                    brace_count -= 1
                if line and not line.startswith('}') and not line.startswith('{'):
                    if '[' in line and '=' in line:
                        self._handle_array_operation(line)
                    elif '=' in line:
                        self._handle_assignment(line)
                idx += 1
        self.code.append(f"{if_end}:")
        return idx - 1

    def _handle_for_loop(self, lines, start_idx):
        for_line = lines[start_idx].strip()
        match = re.match(r'for\s*\((.*?);(.*?);(.*?)\)', for_line)
        if not match:
            raise ValueError("Invalid for loop syntax")
        init, condition, increment = match.groups()
        if '=' in init:
            self._handle_assignment(init.strip())
        loop_start = self.get_label()
        loop_end = self.get_label()
        self.code.append(f"{loop_start}:")
        condition = condition.strip()
        if '<=' in condition:
            var, limit = condition.split('<=')
            temp = self.get_temp()
            self.code.append(f"{temp} = {var.strip()} <= {limit.strip()}")
            self.code.append(f"if {temp} == 0 goto {loop_end}")
        elif '>=' in condition:
            var, limit = condition.split('>=')
            temp = self.get_temp()
            self.code.append(f"{temp} = {var.strip()} >= {limit.strip()}")
            self.code.append(f"if {temp} == 0 goto {loop_end}")
        elif '<' in condition:
            var, limit = condition.split('<')
            temp = self.get_temp()
            self.code.append(f"{temp} = {var.strip()} < {limit.strip()}")
            self.code.append(f"if {temp} == 0 goto {loop_end}")
        elif '>' in condition:
            var, limit = condition.split('>')
            temp = self.get_temp()
            self.code.append(f"{temp} = {var.strip()} > {limit.strip()}")
            self.code.append(f"if {temp} == 0 goto {loop_end}")
        idx = start_idx + 1
        brace_count = 1
        while idx < len(lines) and brace_count > 0:
            line = lines[idx].strip()
            if '{' in line:
                brace_count += 1
            if '}' in line:
                brace_count -= 1
            if line and not line.startswith('}') and not line.startswith('{'):
                if '[' in line and '=' in line:
                    self._handle_array_operation(line)
                elif '=' in line:
                    self._handle_assignment(line)
            idx += 1
        increment = increment.strip()
        if '++' in increment:
            var = increment.replace('++', '').strip()
            self.code.append(f"{var} = {var} + 1")
        elif '--' in increment:
            var = increment.replace('--', '').strip()
            self.code.append(f"{var} = {var} - 1")
        elif '+=' in increment:
            var, val = increment.split('+=' )
            self.code.append(f"{var.strip()} = {var.strip()} + {val.strip()}")
        elif '-=' in increment:
            var, val = increment.split('-=')
            self.code.append(f"{var.strip()} = {var.strip()} - {val.strip()}")
        self.code.append(f"goto {loop_start}")
        self.code.append(f"{loop_end}:")
        return idx - 1

    def _handle_while_loop(self, lines, start_idx):
        while_line = lines[start_idx].strip()
        match = re.match(r'while\s*\((.*?)\)', while_line)
        if not match:
            raise ValueError("Invalid while loop syntax")
        condition = match.group(1).strip()
        loop_start = self.get_label()
        loop_end = self.get_label()
        self.code.append(f"{loop_start}:")
        if '==' in condition:
            left, right = condition.split('==')
            temp = self.get_temp()
            self.code.append(f"{temp} = {left.strip()} == {right.strip()}")
            self.code.append(f"ifFalse {temp} goto {loop_end}")
        elif '!=' in condition:
            left, right = condition.split('!=')
            temp = self.get_temp()
            self.code.append(f"{temp} = {left.strip()} != {right.strip()}")
            self.code.append(f"ifFalse {temp} goto {loop_end}")
        elif '<=' in condition:
            left, right = condition.split('<=')
            temp = self.get_temp()
            self.code.append(f"{temp} = {left.strip()} <= {right.strip()}")
            self.code.append(f"ifFalse {temp} goto {loop_end}")
        elif '>=' in condition:
            left, right = condition.split('>=')
            temp = self.get_temp()
            self.code.append(f"{temp} = {left.strip()} >= {right.strip()}")
            self.code.append(f"ifFalse {temp} goto {loop_end}")
        elif '<' in condition:
            left, right = condition.split('<')
            temp = self.get_temp()
            self.code.append(f"{temp} = {left.strip()} < {right.strip()}")
            self.code.append(f"ifFalse {temp} goto {loop_end}")
        elif '>' in condition:
            left, right = condition.split('>')
            temp = self.get_temp()
            self.code.append(f"{temp} = {left.strip()} > {right.strip()}")
            self.code.append(f"ifFalse {temp} goto {loop_end}")
        idx = start_idx + 1
        brace_count = 1
        while idx < len(lines) and brace_count > 0:
            line = lines[idx].strip()
            if '{' in line:
                brace_count += 1
            if '}' in line:
                brace_count -= 1
            if line and not line.startswith('}') and not line.startswith('{'):
                if '[' in line and '=' in line:
                    self._handle_array_operation(line)
                elif '=' in line:
                    self._handle_assignment(line)
            idx += 1
        self.code.append(f"goto {loop_start}")
        self.code.append(f"{loop_end}:")
        return idx - 1

    def _handle_array_operation(self, line):
        left, right = line.split('=', 1)
        left = left.strip()
        right = right.strip()
        array_name = left[:left.index('[')]
        index_expr = left[left.index('[') + 1:left.index(']')]
        if any(op in right for op in ['+', '-', '*', '/']):
            temp = self.get_temp()
            self._handle_arithmetic(temp, right)
            self.code.append(f"{array_name}[{index_expr}] = {temp}")
        else:
            self.code.append(f"{array_name}[{index_expr}] = {right}")

    def _handle_assignment(self, line):
        left, right = line.split('=', 1)
        left = left.strip()
        right = right.strip()
        if any(op in right for op in ['+', '-', '*', '/']):
            self._handle_arithmetic(left, right)
        else:
            self.code.append(f"{left} = {right}")

    def _handle_arithmetic(self, target, expression):
        tokens = re.findall(r'(\w+|\+|\-|\*|\/|\(|\)|\d+)', expression)
        output = []
        operators = {'+': 1, '-': 1, '*': 2, '/': 2}
        op_stack = []
        for token in tokens:
            if token == '(': op_stack.append(token)
            elif token == ')':
                while op_stack and op_stack[-1] != '(': output.append(op_stack.pop())
                if op_stack and op_stack[-1] == '(': op_stack.pop()
            elif token in operators:
                while (op_stack and op_stack[-1] != '(' and operators.get(op_stack[-1], 0) >= operators[token]):
                    output.append(op_stack.pop())
                op_stack.append(token)
            else:
                output.append(token)
        while op_stack: output.append(op_stack.pop())
        stack = []
        for token in output:
            if token in operators:
                op2 = stack.pop()
                op1 = stack.pop()
                temp = self.get_temp()
                self.code.append(f"{temp} = {op1} {token} {op2}")
                stack.append(temp)
            else:
                stack.append(token)
        if stack:
            self.code.append(f"{target} = {stack[0]}")

    # Please copy the rest of your class code here, including all helper methods. 