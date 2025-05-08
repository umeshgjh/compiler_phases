import re
from enum import Enum, auto
from functools import lru_cache

class TokenType(Enum):
    # Keywords
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    RETURN = auto()
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    BOOL = auto()
    VOID = auto()
    MAIN = auto()
    INCLUDE = auto()
    DEFINE = auto()
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    ASSIGN = auto()
    EQUALS = auto()
    NOT_EQUALS = auto()
    LESS_THAN = auto()
    GREATER_THAN = auto()
    LESS_EQUAL = auto()
    GREATER_EQUAL = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    MODULO = auto()
    INCREMENT = auto()
    DECREMENT = auto()
    
    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    SEMICOLON = auto()
    COMMA = auto()
    DOT = auto()
    COLON = auto()
    QUESTION = auto()
    HASH = auto()
    SINGLE_QUOTE = auto()
    DOUBLE_QUOTE = auto()
    BACKSLASH = auto()
    
    # Literals
    IDENTIFIER = auto()
    INTEGER_LITERAL = auto()
    FLOAT_LITERAL = auto()
    STRING_LITERAL = auto()
    CHAR_LITERAL = auto()
    BOOLEAN_LITERAL = auto()
    
    # Special
    EOF = auto()
    ERROR = auto()

class Token:
    def __init__(self, type, value, line, column):
        self.type = type
        self.value = value
        self.line = line
        self.column = column
    
    def __str__(self):
        return f"Token({self.type}, '{self.value}', line={self.line}, col={self.column})"

class Lexer:
    # Compile patterns once for better performance
    TOKEN_PATTERNS = [
        # Keywords
        (TokenType.IF, r'if\b'),
        (TokenType.ELSE, r'else\b'),
        (TokenType.WHILE, r'while\b'),
        (TokenType.FOR, r'for\b'),
        (TokenType.RETURN, r'return\b'),
        (TokenType.INT, r'int\b'),
        (TokenType.FLOAT, r'float\b'),
        (TokenType.STRING, r'string\b'),
        (TokenType.BOOL, r'bool\b'),
        (TokenType.VOID, r'void\b'),
        (TokenType.MAIN, r'main\b'),
        (TokenType.INCLUDE, r'include\b'),
        (TokenType.DEFINE, r'define\b'),
        
        # Operators
        (TokenType.PLUS, r'\+'),
        (TokenType.MINUS, r'-'),
        (TokenType.MULTIPLY, r'\*'),
        (TokenType.DIVIDE, r'/'),
        (TokenType.ASSIGN, r'='),
        (TokenType.EQUALS, r'=='),
        (TokenType.NOT_EQUALS, r'!='),
        (TokenType.LESS_THAN, r'<'),
        (TokenType.GREATER_THAN, r'>'),
        (TokenType.LESS_EQUAL, r'<='),
        (TokenType.GREATER_EQUAL, r'>='),
        (TokenType.AND, r'&&'),
        (TokenType.OR, r'\|\|'),
        (TokenType.NOT, r'!'),
        (TokenType.MODULO, r'%'),
        (TokenType.INCREMENT, r'\+\+'),
        (TokenType.DECREMENT, r'--'),
        
        # Delimiters
        (TokenType.LPAREN, r'\('),
        (TokenType.RPAREN, r'\)'),
        (TokenType.LBRACE, r'\{'),
        (TokenType.RBRACE, r'\}'),
        (TokenType.LBRACKET, r'\['),
        (TokenType.RBRACKET, r'\]'),
        (TokenType.SEMICOLON, r';'),
        (TokenType.COMMA, r','),
        (TokenType.DOT, r'\.'),
        (TokenType.COLON, r':'),
        (TokenType.QUESTION, r'\?'),
        (TokenType.HASH, r'#'),
        (TokenType.SINGLE_QUOTE, r'\''),
        (TokenType.DOUBLE_QUOTE, r'"'),
        (TokenType.BACKSLASH, r'\\'),
        
        # Literals
        (TokenType.IDENTIFIER, r'[a-zA-Z_][a-zA-Z0-9_]*'),
        (TokenType.INTEGER_LITERAL, r'\d+'),
        (TokenType.FLOAT_LITERAL, r'\d+\.\d+'),
        (TokenType.STRING_LITERAL, r'"[^"\\]*(\\.[^"\\]*)*"'),
        (TokenType.CHAR_LITERAL, r'\'[^\'\\]*(\\.[^\'\\]*)*\''),
        (TokenType.BOOLEAN_LITERAL, r'(true|false)\b'),
    ]
    
    # Compile all patterns at class level
    PATTERNS = [(token_type, re.compile(pattern)) for token_type, pattern in TOKEN_PATTERNS]
    
    def __init__(self, source_code):
        self.source_code = source_code
        self.position = 0
        self.line = 1
        self.column = 1
        self.current_char = self.source_code[0] if source_code else None
        self._tokens = []
        self._tokenize()

    @lru_cache(maxsize=128)
    def _get_token_at_position(self, position):
        """Cached method to get token at a specific position"""
        for token_type, pattern in self.PATTERNS:
            match = pattern.match(self.source_code, position)
            if match:
                return token_type, match.group(0), match.end()
        return None, None, None

    def advance(self):
        self.position += 1
        if self.position < len(self.source_code):
            self.current_char = self.source_code[self.position]
            self.column += 1
        else:
            self.current_char = None

    def skip_whitespace(self):
        while self.current_char and self.current_char.isspace():
            if self.current_char == '\n':
                self.line += 1
                self.column = 1
            self.advance()

    def skip_comment(self):
        if self.current_char == '/' and self.peek() == '/':
            while self.current_char and self.current_char != '\n':
                self.advance()
            self.advance()  # Skip the newline
        elif self.current_char == '/' and self.peek() == '*':
            self.advance()  # Skip /
            self.advance()  # Skip *
            while self.current_char and not (self.current_char == '*' and self.peek() == '/'):
                if self.current_char == '\n':
                    self.line += 1
                    self.column = 1
                self.advance()
            if self.current_char:
                self.advance()  # Skip *
                self.advance()  # Skip /
        elif self.current_char == '#':
            # Handle preprocessor directives
            while self.current_char and self.current_char != '\n':
                self.advance()
            self.advance()  # Skip the newline

    def peek(self):
        peek_pos = self.position + 1
        if peek_pos >= len(self.source_code):
            return None
        return self.source_code[peek_pos]

    def _tokenize(self):
        """Tokenize the entire source code at once"""
        while self.current_char:
            # Skip whitespace
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # Skip comments and preprocessor directives
            if (self.current_char == '/' and (self.peek() == '/' or self.peek() == '*')) or self.current_char == '#':
                self.skip_comment()
                continue

            # Try to match a token
            token_type, value, end_pos = self._get_token_at_position(self.position)
            
            if token_type:
                self._tokens.append(Token(token_type, value, self.line, self.column))
                self.position = end_pos
                self.column += len(value)
                self.current_char = self.source_code[self.position] if self.position < len(self.source_code) else None
            else:
                # Handle unknown characters more gracefully
                if self.current_char in '(){}[];,.:?!+-*/=<>#\'"\\':
                    self._tokens.append(Token(TokenType.ERROR, f"Unexpected character: {self.current_char}", self.line, self.column))
                else:
                    self._tokens.append(Token(TokenType.ERROR, f"Invalid character: {self.current_char}", self.line, self.column))
                self.advance()

        self._tokens.append(Token(TokenType.EOF, '', self.line, self.column))

    def get_next_token(self):
        """Get the next token from the pre-tokenized list"""
        if not self._tokens:
            return Token(TokenType.EOF, '', self.line, self.column)
        return self._tokens.pop(0)

    def tokenize(self):
        """Return all tokens"""
        return self._tokens.copy() 