from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from lexer import Lexer, TokenType
from tac_generator import ThreeAddressCodeGenerator
from syntax_tree_generator import parse_expression, tree_to_dict, tree_to_visjs
from infix_postfix_converter import infix_to_postfix, postfix_to_infix
from code_optimizer import optimize_three_address_code
from machine_code_generator import MachineCodeGenerator

app = Flask(__name__)
CORS(app)

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/lexical')
def lexical():
    return render_template('index for lex.html')

@app.route('/three-address')
def three_address():
    return render_template('index for 3 address code.html')

@app.route('/syntax-tree')
def syntax_tree():
    return render_template('syntax_tree.html')

@app.route('/infix-postfix')
def infix_postfix():
    return render_template('infix_postfix.html')

@app.route('/code-optimization')
def code_optimization():
    return render_template('code_optimization.html')

@app.route('/machine-code')
def machine_code():
    return render_template('machine_code.html')

@app.route('/optimize_code', methods=['POST'])
def optimize_code():
    code = request.json.get('code', '')
    try:
        optimized = optimize_three_address_code(code)
        return jsonify({'success': True, 'optimized': optimized})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        source_code = request.json.get('source_code', '')
        phase = request.json.get('phase', 'lexical')
        
        if phase == 'lexical':
            lexer = Lexer(source_code)
            tokens = lexer.tokenize()
            
            token_list = []
            for token in tokens:
                token_list.append({
                    'type': token.type.name,
                    'value': token.value,
                    'line': token.line,
                    'column': token.column
                })
            
            return jsonify({
                'success': True,
                'tokens': token_list
            })
        else:  # three-address code generation
            generator = ThreeAddressCodeGenerator()
            result = generator.generate(source_code)
            if 'error' in result:
                return jsonify({'success': False, 'error': result['error']})
            return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/get_representation', methods=['POST'])
def get_representation():
    try:
        code = request.json.get('code', '')
        rep_type = request.json.get('type', 'quadruple')
        generator = ThreeAddressCodeGenerator()
        result = generator.generate(code)
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']})
        return jsonify({'success': True, 'representation': result[rep_type]})
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Endpoint for syntax tree generation
@app.route('/generate_syntax_tree', methods=['POST'])
def generate_syntax_tree():
    code = request.json.get('code', '')
    try:
        tree = parse_expression(code)
        tree_data = tree_to_dict(tree)
        visjs_data = tree_to_visjs(tree)
        return jsonify({'success': True, 'tree': tree_data, 'visjs': visjs_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Endpoint for infix/postfix conversion
@app.route('/convert_infix_postfix', methods=['POST'])
def convert_infix_postfix():
    expr = request.json.get('expr', '')
    direction = request.json.get('direction', 'infix-to-postfix')
    try:
        if direction == 'infix-to-postfix':
            result = infix_to_postfix(expr)
        else:
            result = postfix_to_infix(expr)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generate_machine_code', methods=['POST'])
def generate_machine_code():
    tac = request.json.get('tac', '')
    try:
        generator = MachineCodeGenerator()
        result = generator.generate(tac)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True) 