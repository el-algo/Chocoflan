"""
This is a sample programming language translator and
virtual machine for Chocoflan.
"""

class Token:
    def __init__(self, typ, val, pos) -> None:
        self.type = typ
        self.val = val
        self.pos = pos

    def __repr__(self) -> str:
        return f"[{self.type}, {self.val}]"

class Lexer:
    KEYWORDS = {
        "main": "MAIN",
        "end": "END",
        "def": "DEF"
    }

    def __init__(self, src) -> None:
        self.src = src
        self.i = 0
        self.n = len(src)

    def peek(self):
        return self.src[self.i] if self.i < self.n else '\0'

    def match(self, expected) -> bool:
        if self.peek() == expected:
            self.i += 1
            return True
        return False

    def advance(self):
        ch = self.peek()
        self.i += 1
        return ch

    def consume_ws(self):
        while self.peek().isspace():
            self.advance()

    def next_token(self):
        self.consume_ws()
        ch = self.peek()
        pos = self.i

        if ch == '\0':
            return Token("EOF", None, pos)

        # Identifiers / keywords
        if ch.isalpha() or ch == '_':
            start = self.i
            while self.peek().isalnum() or self.peek() == '_':
                self.advance()
            text = self.src[start:self.i]
            kw = self.KEYWORDS.get(text.lower())
            if kw:
                return Token(kw, text, pos)
            return Token("IDENT", text, pos)

        # Integer numbers
        if ch.isdigit():
            start = self.i
            while self.peek().isdigit():
                self.advance()
            num = int(self.src[start:self.i])
            return Token("NUMBER", num, pos)

        # Operators
        c = self.advance()
        if c == '+': return Token("ADD", "+", pos)
        if c == '-': return Token("SUB", "-", pos)
        if c == '*': return Token("MUL", "*", pos)
        if c == '/': return Token("DIV", "/", pos)

        return Token("ERROR", c, pos)


class Parser:
    def __init__(self, lexer) -> None:
        self.lexer = lexer
        self.cur = self.lexer.next_token()
        self.code = []

    def error(self, msg):
        raise SyntaxError(f"{msg} at pos {self.cur.pos}, got {self.cur}")

    def match(self, typ):
        if self.cur.type == typ:
            self.cur = self.lexer.next_token()
            return True
        return False

    def expect(self, typ):
        if not self.match(typ):
            self.error(f"Expected {typ}")

    def emit(self, op, arg=None):
        self.code.append((op, arg))

    # program := (MAIN code END) | code ;  (EOF required)
    def program(self):
        if self.cur.type == "MAIN":
            self.match("MAIN")
            self.code_block()
            self.expect("END")
        else:
            self.code_block()
        self.expect("EOF")
        self.emit("HALT")
        return self.code

    # code := { expression } ;   (stop at END or EOF)
    def code_block(self):
        while self.cur.type not in ("END", "EOF"):
            self.expression()

    # expression :=
    #     NUMBER            -> PUSH n
    #   | IDENT             -> LOAD name
    #   | DEF IDENT         -> STORE name   (pops value)
    #   | ADD|SUB|MUL|DIV   -> corresponding ALU op
    def expression(self):
        t = self.cur.type

        if t == "NUMBER":
            val = self.cur.val
            self.match("NUMBER")
            self.emit("PUSH", val)
            return

        if t == "IDENT":
            name = self.cur.val
            self.match("IDENT")
            self.emit("LOAD", name)
            return

        if t == "DEF":
            self.match("DEF")
            if self.cur.type != "IDENT":
                self.error("Identifier after 'def'")
            name = self.cur.val
            self.match("IDENT")
            self.emit("STORE", name)
            return

        if t in ("ADD", "SUB", "MUL", "DIV"):
            self.match(t)
            self.emit(t)
            return

        self.error("Unexpected token in expression")


# Stack VM
class VM:
    def __init__(self, code):
        self.code = code
        self.pc = 0
        self.stack = []
        self.env = {}

    def pop1(self):
        if not self.stack:
            raise RuntimeError("Stack underflow: need one operand")
        return self.stack.pop()

    def pop2(self):
        if len(self.stack) < 2:
            raise RuntimeError("Stack underflow: need two operands")
        b = self.stack.pop()
        a = self.stack.pop()
        return a, b

    def run(self):
        while self.pc < len(self.code):
            op, arg = self.code[self.pc]
            self.pc += 1

            if op == "HALT":
                return

            elif op == "PUSH":
                self.stack.append(arg)

            elif op == "LOAD":
                if arg not in self.env:
                    raise NameError(f"Undefined identifier '{arg}'")
                self.stack.append(self.env[arg])

            elif op == "STORE":
                val = self.pop1()
                self.env[arg] = val

            elif op == "ADD":
                a, b = self.pop2()
                self.stack.append(a + b)

            elif op == "SUB":
                a, b = self.pop2()
                self.stack.append(a - b)

            elif op == "MUL":
                a, b = self.pop2()
                self.stack.append(a * b)

            elif op == "DIV":
                a, b = self.pop2()
                if b == 0:
                    raise ZeroDivisionError("Division by zero")
                self.stack.append(a // b)

            else:
                raise RuntimeError(f"Unknown opcode {op}")

    def list_bytecode(self):
        print("Bytecode:")
        for i in self.code:
            print(i)


def compile_and_run(src):
    l = Lexer(src)
    p = Parser(l)
    bytecode = p.program()
    vm = VM(bytecode)
    vm.run()

    vm.list_bytecode()
    print("Env:", vm.env)
    print("Stack:", vm.stack)
    if vm.stack:
        print("Result:", vm.stack[-1])


if __name__ == "__main__":
    # Examples
    # compile_and_run("2 2 + 5 *")
    # compile_and_run("main 10 3 - 2 * end")
    # compile_and_run("10 def x   x 2 *")

    # REPL
    while True:
        try:
            print("$ ", end="")
            line = input()
            if not line:
                continue
            compile_and_run(line)
        except (EOFError, KeyboardInterrupt):
            break
