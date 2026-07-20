from lexer import DIV, EOF, MULT, NUMERO, PAREN_DIR, PAREN_ESQ, SOMA, SUB, IGUAL, IDENTIFICADOR, PONTO_VIRGULA

NIVEL_ADITIVO = {SOMA, SUB}
NIVEL_MULTIPLICATIVO = {MULT, DIV}


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

    def avaliar(self, env):
        return self.valor

    def imprimir(self):
        return str(self.valor)


class OpBin(Exp):
    def __init__(self, op, esq, dir):
        self.op = op
        self.esq = esq
        self.dir = dir

    def avaliar(self, env):
        v_esq = self.esq.avaliar(env)
        v_dir = self.dir.avaliar(env)
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


class Programa(Exp):
    def __init__(self, declaracoes, exp_final):
        self.declaracoes = declaracoes
        self.exp_final = exp_final

    def avaliar(self, env):
        for decl in self.declaracoes:
            env[decl.nome] = decl.exp.avaliar(env)
        return self.exp_final.avaliar(env)

    def imprimir(self):
        decls = "".join(f"{decl.imprimir()} " for decl in self.declaracoes)
        return f"{decls}= {self.exp_final.imprimir()}"


class Declaracao:
    def __init__(self, nome, exp):
        self.nome = nome
        self.exp = exp

    def imprimir(self):
        return f"{self.nome} = {self.exp.imprimir()};"


class Var(Exp):
    def __init__(self, nome):
        self.nome = nome

    def avaliar(self, env):
        return env[self.nome]

    def imprimir(self):
        return self.nome


# --- Analisador sintático ---
#
# Gramatica EC2 (precedencia e associatividade, sem parenteses obrigatorios):
#
#   exp_a ::= exp_m (('+' | '-') exp_m)*
#   exp_m ::= prim (('*' | '/') prim)*
#   prim  ::= num | '(' exp_a ')'

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

    def analisa_programa(self):
        declaracoes = []
        tok = self._peek()
        while tok.tipo == IDENTIFICADOR:
            dec = self.analisa_declaracao()
            declaracoes.append(dec)
            tok = self._peek()
        
        tok = self._proximo_token()
        if tok.tipo != IGUAL:
            lexema = tok.lexema if tok.lexema else tok.tipo
            raise ErroSintatico(tok.pos, f"esperado '=', encontrado '{lexema}'")
        
        exp_final = self.analisa_exp_a()
        return Programa(declaracoes, exp_final)

    def analisa_declaracao(self):
        tok_id = self._verifica_prox(IDENTIFICADOR)
        self._verifica_prox(IGUAL)
        exp = self.analisa_exp_a()
        self._verifica_prox(PONTO_VIRGULA)
        return Declaracao(tok_id.lexema, exp)

    def analisa_exp_a(self):
        esq = self.analisa_exp_m()
        tok = self._peek()
        while tok.tipo in NIVEL_ADITIVO:
            self._proximo_token()
            dire = self.analisa_exp_m()
            esq = OpBin(tok.lexema, esq, dire)
            tok = self._peek()
        return esq

    def analisa_exp_m(self):
        esq = self.analisa_prim()
        tok = self._peek()
        while tok.tipo in NIVEL_MULTIPLICATIVO:
            self._proximo_token()
            dire = self.analisa_prim()
            esq = OpBin(tok.lexema, esq, dire)
            tok = self._peek()
        return esq

    def analisa_prim(self):
        tok = self._proximo_token()
        if tok.tipo == NUMERO:
            return Const(int(tok.lexema))
        if tok.tipo == IDENTIFICADOR:
            return Var(tok.lexema)
        if tok.tipo == PAREN_ESQ:
            exp = self.analisa_exp_a()
            self._verifica_prox(PAREN_DIR)
            return exp
        lexema = tok.lexema if tok.lexema else tok.tipo
        raise ErroSintatico(tok.pos, f"esperado numero ou '(', encontrado '{lexema}'")

    def analisar(self):
        arvore = self.analisa_programa()
        prox = self._peek()
        if prox.tipo != EOF:
            lexema = prox.lexema if prox.lexema else prox.tipo
            raise ErroSintatico(prox.pos, f"tokens inesperados apos expressao: '{lexema}'")
        return arvore


def analisar(tokens):
    return Parser(tokens).analisar()
