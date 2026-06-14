from lexer import DIV, EOF, MULT, NUMERO, PAREN_DIR, PAREN_ESQ, SOMA, SUB

TIPOS_OPERADOR = {SOMA, SUB, MULT, DIV}


class ErroSintatico(Exception):
    def __init__(self, pos, msg):
        self.pos = pos
        super().__init__(f"Erro sintatico na posicao {pos}: {msg}")


# --- Nós da AST ---

class Exp:
    pass


class Const(Exp):
    def __init__(self, valor):
        self.valor = valor

    def avaliar(self):
        return self.valor

    def imprimir(self):
        return str(self.valor)


class OpBin(Exp):
    def __init__(self, op, esq, dir):
        self.op = op
        self.esq = esq
        self.dir = dir

    def avaliar(self):
        v_esq = self.esq.avaliar()
        v_dir = self.dir.avaliar()
        if self.op == '+':
            return v_esq + v_dir
        if self.op == '-':
            return v_esq - v_dir
        if self.op == '*':
            return v_esq * v_dir
        if self.op == '/':
            return v_esq // v_dir

    def imprimir(self):
        return f'({self.esq.imprimir()} {self.op} {self.dir.imprimir()})'


# --- Analisador sintático ---

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def _proximo_token(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _peek(self):
        return self.tokens[self.pos]

    def _verifica_prox(self, tipo):
        tok = self._proximo_token()
        if tok.tipo != tipo:
            lexema = tok.lexema if tok.lexema else tok.tipo
            raise ErroSintatico(tok.pos, f"esperado '{tipo}', encontrado '{lexema}'")
        return tok

    def analisa_exp(self):
        tok = self._proximo_token()
        if tok.tipo == NUMERO:
            return Const(int(tok.lexema))
        if tok.tipo == PAREN_ESQ:
            esq = self.analisa_exp()
            op = self.analisa_operador()
            dire = self.analisa_exp()
            self._verifica_prox(PAREN_DIR)
            return OpBin(op, esq, dire)
        lexema = tok.lexema if tok.lexema else tok.tipo
        raise ErroSintatico(tok.pos, f"esperado numero ou '(', encontrado '{lexema}'")

    def analisa_operador(self):
        tok = self._proximo_token()
        if tok.tipo in TIPOS_OPERADOR:
            return tok.lexema
        lexema = tok.lexema if tok.lexema else tok.tipo
        raise ErroSintatico(tok.pos, f"esperado operador, encontrado '{lexema}'")

    def analisar(self):
        arvore = self.analisa_exp()
        prox = self._peek()
        if prox.tipo != EOF:
            lexema = prox.lexema if prox.lexema else prox.tipo
            raise ErroSintatico(prox.pos, f"tokens inesperados apos expressao: '{lexema}'")
        return arvore


def analisar(tokens):
    return Parser(tokens).analisar()
