from lexer import (
    CHAVE_DIR,
    CHAVE_ESQ,
    DIFERENTE,
    DIV,
    ENQUANTO,
    EOF,
    IDENTIFICADOR,
    IGUAL,
    IGUALDADE,
    MAIOR,
    MAIOR_IGUAL,
    MENOR,
    MENOR_IGUAL,
    MULT,
    NUMERO,
    PAREN_DIR,
    PAREN_ESQ,
    PONTO_VIRGULA,
    RETORNO,
    SE,
    SENAO,
    SOMA,
    SUB,
)

NIVEL_COMPARACAO = {MENOR, MAIOR, MENOR_IGUAL, MAIOR_IGUAL, IGUALDADE, DIFERENTE}
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
            # idiv trunca em direcao a zero; o // do Python arredonda para
            # baixo. A diferenca so aparece com operandos negativos, mas o
            # interpretador e o oraculo dos testes end-to-end, entao precisa
            # concordar com o assembly.
            quociente = abs(v_esq) // abs(v_dir)
            return quociente if (v_esq < 0) == (v_dir < 0) else -quociente
        # comparacoes produzem 1 ou 0 (inteiros, nao bool) para casar
        # exatamente com o que SETcc coloca no registrador
        if self.op == '<':
            return 1 if v_esq < v_dir else 0
        if self.op == '>':
            return 1 if v_esq > v_dir else 0
        if self.op == '<=':
            return 1 if v_esq <= v_dir else 0
        if self.op == '>=':
            return 1 if v_esq >= v_dir else 0
        if self.op == '==':
            return 1 if v_esq == v_dir else 0
        if self.op == '!=':
            return 1 if v_esq != v_dir else 0
        raise ValueError(f"operador desconhecido: {self.op}")

    def imprimir(self):
        return f'({self.esq.imprimir()} {self.op} {self.dir.imprimir()})'


class Programa(Exp):
    def __init__(self, declaracoes, comandos, exp_retorno):
        self.declaracoes = declaracoes
        self.comandos = comandos
        self.exp_retorno = exp_retorno

    def avaliar(self, env):
        for decl in self.declaracoes:
            env[decl.nome] = decl.exp.avaliar(env)
        for cmd in self.comandos:
            cmd.executar(env)
        return self.exp_retorno.avaliar(env)

    def imprimir(self):
        linhas = [decl.imprimir() for decl in self.declaracoes]
        linhas.append("{")
        linhas.extend(cmd.imprimir(1) for cmd in self.comandos)
        linhas.append(f"  return {self.exp_retorno.imprimir()};")
        linhas.append("}")
        return "\n".join(linhas)


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


# --- Nós de comando ---
#
# Comandos nao produzem valor: `executar` altera o ambiente.
# `imprimir` recebe o nivel de indentacao (dois espacos por nivel).

def _ind(nivel):
    return "  " * nivel


class Cmd:
    pass


class Atribuicao(Cmd):
    def __init__(self, nome, exp):
        self.nome = nome
        self.exp = exp

    def executar(self, env):
        env[self.nome] = self.exp.avaliar(env)

    def imprimir(self, nivel):
        return f"{_ind(nivel)}{self.nome} = {self.exp.imprimir()};"


class Se(Cmd):
    def __init__(self, cond, entao, senao):
        self.cond = cond
        self.entao = entao
        self.senao = senao

    def executar(self, env):
        ramo = self.entao if self.cond.avaliar(env) != 0 else self.senao
        for cmd in ramo:
            cmd.executar(env)

    def imprimir(self, nivel):
        ind = _ind(nivel)
        linhas = [f"{ind}if {self.cond.imprimir()} {{"]
        linhas.extend(cmd.imprimir(nivel + 1) for cmd in self.entao)
        if self.senao:
            linhas.append(f"{ind}}} else {{")
            linhas.extend(cmd.imprimir(nivel + 1) for cmd in self.senao)
        linhas.append(f"{ind}}}")
        return "\n".join(linhas)


class Enquanto(Cmd):
    def __init__(self, cond, corpo):
        self.cond = cond
        self.corpo = corpo

    def executar(self, env):
        while self.cond.avaliar(env) != 0:
            for cmd in self.corpo:
                cmd.executar(env)

    def imprimir(self, nivel):
        ind = _ind(nivel)
        linhas = [f"{ind}while {self.cond.imprimir()} {{"]
        linhas.extend(cmd.imprimir(nivel + 1) for cmd in self.corpo)
        linhas.append(f"{ind}}}")
        return "\n".join(linhas)


# --- Analisador sintático ---
#
# Gramatica Cmd (Atividade 09):
#
#   programa ::= decl* corpo
#   decl     ::= ident '=' exp ';'
#   corpo    ::= '{' cmd* 'return' exp ';' '}'
#   cmd      ::= se | enquanto | atrib
#   se       ::= 'if' exp bloco ('else' bloco)?      # else opcional (extensao)
#   enquanto ::= 'while' exp bloco
#   bloco    ::= '{' cmd* '}'
#   atrib    ::= ident '=' exp ';'
#   exp      ::= exp_a ((op_comp) exp_a)*
#   exp_a    ::= exp_m (('+' | '-') exp_m)*
#   exp_m    ::= prim (('*' | '/') prim)*
#   prim     ::= num | ident | '(' exp ')'
#   op_comp  ::= '<' | '>' | '<=' | '>=' | '==' | '!='
#
# Tres niveis de precedencia, do mais baixo para o mais alto: comparacao,
# aditivo, multiplicativo. Todos associativos a esquerda.

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
        # declaracoes e atribuicoes tem a mesma forma `ident = exp;`; a
        # distincao e posicional — antes do '{' e declaracao, dentro e comando
        declaracoes = []
        while self._peek().tipo == IDENTIFICADOR:
            declaracoes.append(self.analisa_declaracao())
        comandos, exp_retorno = self.analisa_corpo()
        return Programa(declaracoes, comandos, exp_retorno)

    def analisa_declaracao(self):
        tok_id = self._verifica_prox(IDENTIFICADOR)
        self._verifica_prox(IGUAL)
        exp = self.analisa_exp()
        self._verifica_prox(PONTO_VIRGULA)
        return Declaracao(tok_id.lexema, exp)

    def analisa_corpo(self):
        self._verifica_prox(CHAVE_ESQ)
        comandos = self.analisa_lista_cmd()
        self._verifica_prox(RETORNO)
        exp = self.analisa_exp()
        self._verifica_prox(PONTO_VIRGULA)
        self._verifica_prox(CHAVE_DIR)
        return comandos, exp

    def analisa_lista_cmd(self):
        # Encerra em qualquer token que nao inicie um comando — cabe a quem
        # chamou exigir '}' (blocos) ou 'return' (corpo do programa). Como
        # `return` nao e um comando, um `return` dentro de um bloco encerra a
        # lista e `analisa_bloco` reporta a chave faltante.
        comandos = []
        while True:
            tipo = self._peek().tipo
            if tipo == SE:
                comandos.append(self.analisa_se())
            elif tipo == ENQUANTO:
                comandos.append(self.analisa_enquanto())
            elif tipo == IDENTIFICADOR:
                comandos.append(self.analisa_atrib())
            else:
                return comandos

    def analisa_bloco(self):
        self._verifica_prox(CHAVE_ESQ)
        comandos = self.analisa_lista_cmd()
        self._verifica_prox(CHAVE_DIR)
        return comandos

    def analisa_se(self):
        self._verifica_prox(SE)
        cond = self.analisa_exp()
        entao = self.analisa_bloco()
        # o braco `else` e opcional (extensao); o lookahead liga o `else` ao
        # `if` mais interno
        senao = []
        if self._peek().tipo == SENAO:
            self._proximo_token()
            senao = self.analisa_bloco()
        return Se(cond, entao, senao)

    def analisa_enquanto(self):
        self._verifica_prox(ENQUANTO)
        cond = self.analisa_exp()
        corpo = self.analisa_bloco()
        return Enquanto(cond, corpo)

    def analisa_atrib(self):
        tok_id = self._verifica_prox(IDENTIFICADOR)
        self._verifica_prox(IGUAL)
        exp = self.analisa_exp()
        self._verifica_prox(PONTO_VIRGULA)
        return Atribuicao(tok_id.lexema, exp)

    def analisa_exp(self):
        esq = self.analisa_exp_a()
        tok = self._peek()
        while tok.tipo in NIVEL_COMPARACAO:
            self._proximo_token()
            dire = self.analisa_exp_a()
            esq = OpBin(tok.lexema, esq, dire)
            tok = self._peek()
        return esq

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
            exp = self.analisa_exp()
            self._verifica_prox(PAREN_DIR)
            return exp
        lexema = tok.lexema if tok.lexema else tok.tipo
        raise ErroSintatico(
            tok.pos, f"esperado numero, identificador ou '(', encontrado '{lexema}'"
        )

    def analisar(self):
        arvore = self.analisa_programa()
        prox = self._peek()
        if prox.tipo != EOF:
            lexema = prox.lexema if prox.lexema else prox.tipo
            raise ErroSintatico(prox.pos, f"tokens inesperados apos expressao: '{lexema}'")
        return arvore


def analisar(tokens):
    return Parser(tokens).analisar()
