class MachineCodeGenerator:
    def __init__(self):
        self.registers = [f'R{i}' for i in range(8)]  # R0-R7
        self.register_map = {}  # Maps variables to registers
        self.next_register = 0
        self.machine_code = []
        self.variables = set()
        self.used_variables = set()  # Track variables that need to be loaded

    def get_register(self, var):
        try:
            if var not in self.register_map:
                if self.next_register >= len(self.registers):
                    raise ValueError("Not enough registers available")
                # Use sequential registers starting from R0
                self.register_map[var] = self.registers[self.next_register]
                self.next_register += 1
                # Only add non-temporary variables to used_variables
                if not var.startswith('t') and var != 'result':
                    self.used_variables.add(var)
            return self.register_map[var]
        except Exception as e:
            raise ValueError(f"Error allocating register for {var}: {str(e)}")

    def get_temp_register(self):
        try:
            if self.temp_register >= len(self.registers):
                raise ValueError("Not enough registers available for temporaries")
            reg = self.registers[self.temp_register]
            self.temp_register += 1
            return reg
        except Exception as e:
            raise ValueError(f"Error allocating temporary register: {str(e)}")

    def generate(self, tac_code):
        try:
            # Reset state
            self.register_map = {}
            self.next_register = 0
            self.machine_code = []
            self.variables = set()
            self.used_variables = set()

            # First pass: collect all variables and allocate registers
            lines = [line.strip() for line in tac_code.split('\n') if line.strip()]
            for line in lines:
                if '=' not in line:
                    raise ValueError(f"Invalid three address code line: {line}")
                
                left, right = line.split('=', 1)
                left = left.strip()
                right = right.strip()
                
                # Get registers for all variables
                self.get_register(left)  # Result variable
                if not any(op in right for op in ['+', '-', '*', '/']):
                    if not right.isdigit():
                        self.get_register(right)
                else:
                    for op in ['+', '-', '*', '/']:
                        if op in right:
                            op1, op2 = right.split(op)
                            self.get_register(op1.strip())
                            self.get_register(op2.strip())
                            break

            # Generate initial MOV instructions for variables
            for var in sorted(self.used_variables):
                self.machine_code.append(f"MOV {var}, {self.register_map[var]}")

            # Second pass: generate operation instructions
            for line in lines:
                left, right = line.split('=', 1)
                left = left.strip()
                right = right.strip()
                
                if not any(op in right for op in ['+', '-', '*', '/']):
                    if right.isdigit():
                        self.machine_code.append(f"MOV #{right}, {self.register_map[left]}")
                    else:
                        self.machine_code.append(f"MOV {self.register_map[right]}, {self.register_map[left]}")
                else:
                    for op in ['+', '-', '*', '/']:
                        if op in right:
                            op1, op2 = right.split(op)
                            op1 = op1.strip()
                            op2 = op2.strip()
                            
                            if op == '+':
                                self.machine_code.append(f"ADD {self.register_map[op1]}, {self.register_map[op2]}, {self.register_map[left]}")
                            elif op == '-':
                                self.machine_code.append(f"SUB {self.register_map[op1]}, {self.register_map[op2]}, {self.register_map[left]}")
                            elif op == '*':
                                self.machine_code.append(f"MUL {self.register_map[op1]}, {self.register_map[op2]}, {self.register_map[left]}")
                            elif op == '/':
                                self.machine_code.append(f"DIV {self.register_map[op1]}, {self.register_map[op2]}, {self.register_map[left]}")
                            break

            return '\n'.join(self.machine_code)
        except Exception as e:
            raise ValueError(f"Error generating machine code: {str(e)}") 