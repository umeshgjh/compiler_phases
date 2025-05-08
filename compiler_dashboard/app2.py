from flask import Flask, render_template, request, jsonify
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

class CodeForm(FlaskForm):
    code = TextAreaField('Enter your code:', validators=[DataRequired()])
    submit = SubmitField('Generate 3-Address Code')

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
            # Reset all counters and lists
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

            # Generate all representations
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
            if '=' in line:
                left, right = line.split('=', 1)
                left = left.strip()
                right = right.strip()

                if any(op in right for op in ['+', '-', '*', '/']):
                    # Handle arithmetic operations
                    op = next(op for op in ['+', '-', '*', '/'] if op in right)
                    op1, op2 = right.split(op)
                    temp = self.get_temp()
                    self.quadruples.append({
                        'location': i,
                        'op': op,
                        'arg1': op1.strip(),
                        'arg2': op2.strip(),
                        'result': temp
                    })
                    # Add assignment to target
                    self.quadruples.append({
                        'location': i + 1,
                        'op': '=',
                        'arg1': temp,
                        'arg2': '',
                        'result': left
                    })
                else:
                    # Handle simple assignment
                    self.quadruples.append({
                        'location': i,
                        'op': '=',
                        'arg1': right,
                        'arg2': '',
                        'result': left
                    })
            elif 'ifFalse' in line:
                # Handle ifFalse statements
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
            elif 'goto' in line:
                # Handle goto statements
                target = line.split('goto')[1].strip()
                self.quadruples.append({
                    'location': i,
                    'op': 'goto',
                    'arg1': '',
                    'arg2': '',
                    'result': target
                })
            elif ':' in line:
                # Handle labels
                label = line.replace(':', '').strip()
                self.quadruples.append({
                    'location': i,
                    'op': 'label',
                    'arg1': label,
                    'arg2': '',
                    'result': ''
                })
            elif any(op in line for op in ['<', '>', '<=', '>=', '==', '!=']):
                # Handle comparison operations
                for op in ['<=', '>=', '==', '!=', '<', '>']:
                    if op in line:
                        left, right = line.split(op)
                        temp = self.get_temp()
                        self.quadruples.append({
                            'location': i,
                            'op': op,
                            'arg1': left.strip(),
                            'arg2': right.strip(),
                            'result': temp
                        })
                        break

    def _generate_triples(self):
        for i, quad in enumerate(self.quadruples):
            if quad['op'] == '=':
                # For simple assignments
                self.triples.append({
                    'location': i,
                    'op': '=',
                    'arg1': quad['arg1'].replace('t', '') if quad['arg1'].startswith('t') else quad['arg1'],
                    'arg2': ''
                })
            elif quad['op'] in ['+', '-', '*', '/']:
                # For arithmetic operations
                self.triples.append({
                    'location': i,
                    'op': quad['op'],
                    'arg1': quad['arg1'].replace('t', '') if quad['arg1'].startswith('t') else quad['arg1'],
                    'arg2': quad['arg2'].replace('t', '') if quad['arg2'].startswith('t') else quad['arg2']
                })
            elif quad['op'] == 'ifFalse':
                # For conditional jumps
                self.triples.append({
                    'location': i,
                    'op': 'ifFalse',
                    'arg1': quad['arg1'].replace('t', '') if quad['arg1'].startswith('t') else quad['arg1'],
                    'arg2': quad['result']
                })
            elif quad['op'] == 'goto':
                # For unconditional jumps
                self.triples.append({
                    'location': i,
                    'op': 'goto',
                    'arg1': quad['result'],
                    'arg2': ''
                })
            elif quad['op'] == 'label':
                # For labels
                self.triples.append({
                    'location': i,
                    'op': 'label',
                    'arg1': quad['arg1'],
                    'arg2': ''
                })
            elif quad['op'] in ['<', '>', '<=', '>=', '==', '!=']:
                # For comparison operations
                self.triples.append({
                    'location': i,
                    'op': quad['op'],
                    'arg1': quad['arg1'].replace('t', '') if quad['arg1'].startswith('t') else quad['arg1'],
                    'arg2': quad['arg2'].replace('t', '') if quad['arg2'].startswith('t') else quad['arg2']
                })

    def _generate_indirect_triples(self):
        # Simple list of pointers starting from 1000
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

        # Add goto to skip else block
        self.code.append(f"goto {if_end}")
        self.code.append(f"{else_label}:")

        # Check for else
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

        # Add end label
        self.code.append(f"{if_end}:")
        return idx - 1

    def _handle_for_loop(self, lines, start_idx):
        for_line = lines[start_idx].strip()
        match = re.match(r'for\s*\((.*?);(.*?);(.*?)\)', for_line)
        if not match:
            raise ValueError("Invalid for loop syntax")

        init, condition, increment = match.groups()
        
        # Generate initialization
        if '=' in init:
            self._handle_assignment(init.strip())

        loop_start = self.get_label()
        loop_end = self.get_label()
        
        # Generate loop structure
        self.code.append(f"{loop_start}:")
        
        # Generate condition
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
        
        # Process loop body
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

        # Handle increment
        increment = increment.strip()
        if '++' in increment:
            var = increment.replace('++', '').strip()
            self.code.append(f"{var} = {var} + 1")
        elif '--' in increment:
            var = increment.replace('--', '').strip()
            self.code.append(f"{var} = {var} - 1")
        elif '+=' in increment:
            var, val = increment.split('+=')
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

        # Generate loop structure
        self.code.append(f"{loop_start}:")
        
        # Handle condition
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
        
        # Process loop body
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

        # Add goto to loop start and end label
        self.code.append(f"goto {loop_start}")
        self.code.append(f"{loop_end}:")
        
        return idx - 1

    def _handle_array_operation(self, line):
        left, right = line.split('=', 1)
        left = left.strip()
        right = right.strip()

        # Handle array access on left side
        array_name = left[:left.index('[')]
        index_expr = left[left.index('[') + 1:left.index(']')]
        
        # Handle the right side expression
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
        # Convert infix to postfix using BODMAS rules
        tokens = re.findall(r'(\w+|\+|\-|\*|\/|\(|\)|\d+)', expression)
        output = []
        operators = {'+': 1, '-': 1, '*': 2, '/': 2}
        op_stack = []

        for token in tokens:
            if token == '(':
                op_stack.append(token)
            elif token == ')':
                while op_stack and op_stack[-1] != '(':
                    output.append(op_stack.pop())
                if op_stack and op_stack[-1] == '(':
                    op_stack.pop()
            elif token in operators:
                while (op_stack and op_stack[-1] != '(' and 
                       operators.get(op_stack[-1], 0) >= operators[token]):
                    output.append(op_stack.pop())
                op_stack.append(token)
            else:
                output.append(token)

        while op_stack:
            output.append(op_stack.pop())

        # Evaluate postfix expression
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

@app.route('/', methods=['GET', 'POST'])
def index():
    form = CodeForm()
    result = None
    if form.validate_on_submit():
        generator = ThreeAddressCodeGenerator()
        result = generator.generate(form.code.data)
    return render_template('/media/umeshgjh/New Volume/COMPILER/inte/compiler_dashboard/templates/index for 3 address code.html', form=form, result=result)

@app.route('/get_representation', methods=['POST'])
def get_representation():
    code = request.json.get('code')
    representation_type = request.json.get('type')
    
    generator = ThreeAddressCodeGenerator()
    result = generator.generate(code)
    
    if 'error' in result:
        return jsonify({'error': result['error']})
    
    return jsonify({
        'representation': result[representation_type]
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000) 