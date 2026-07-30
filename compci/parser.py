from lexer import (
    CHAVE_DIR,
    CHAVE_ESQ,
    DIFERENTE,
    DIV,
    ENQUANTO,
    EOF,
    FUN,
    IDENTIFICADOR,
    IGUAL,
    IGUALDADE,
    MAIN,
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
    VAR,
    VIRGULA,
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
        # declaracoes mistura Declaracao (variavel global) e FuncDecl (funcao),
        # na ordem em que aparecem no texto: a analise semantica processa essa
        # lista sequencialmente, entao a ordem importa (permite referenciar
        # apenas o que foi declarado antes, exceto recursao direta)
        self.declaracoes = declaracoes
        self.comandos = comandos
        self.exp_retorno = exp_retorno

    def avaliar(self, env):
        funcoes = {}
        for decl in self.declaracoes:
            if isinstance(decl, FuncDecl):
                funcoes[decl.nome] = decl
            else:
                env[decl.nome] = decl.exp.avaliar(env)
        env["__funcoes__"] = funcoes
        for cmd in self.comandos:
            cmd.executar(env)
        return self.exp_retorno.avaliar(env)

    def imprimir(self):
        linhas = [decl.imprimir() for decl in self.declaracoes]
        linhas.append("main {")
        linhas.extend(cmd.imprimir(1) for cmd in self.comandos)
        linhas.append(f"  return {self.exp_retorno.imprimir()};")
        linhas.append("}")
        return "\n".join(linhas)


class Declaracao:
    def __init__(self, nome, exp):
        self.nome = nome
        self.exp = exp

    def imprimir(self):
        return f"var {self.nome} = {self.exp.imprimir()};"


class FuncDecl:
    def __init__(self, nome, params, vardecls, comandos, exp_retorno):
        self.nome = nome
        self.params = params
        self.vardecls = vardecls
        self.comandos = comandos
        self.exp_retorno = exp_retorno

    def imprimir(self):
        linhas = [f"fun {self.nome}({', '.join(self.params)}) {{"]
        linhas.extend(f"  {v.imprimir()}" for v in self.vardecls)
        linhas.extend(cmd.imprimir(1) for cmd in self.comandos)
        linhas.append(f"  return {self.exp_retorno.imprimir()};")
        linhas.append("}")
        return "\n".join(linhas)


class Chamada(Exp):
    def __init__(self, nome, args):
        self.nome = nome
        self.args = args

    def avaliar(self, env):
        func = env["__funcoes__"][self.nome]
        valores = [arg.avaliar(env) for arg in self.args]
        env_local = dict(zip(func.params, valores))
        for vardecl in func.vardecls:
            env_local[vardecl.nome] = vardecl.exp.avaliar(env_local)
        env_local["__funcoes__"] = env["__funcoes__"]
        for cmd in func.comandos:
            cmd.executar(env_local)
        return func.exp_retorno.avaliar(env_local)

    def imprimir(self):
        args = ", ".join(arg.imprimir() for arg in self.args)
        return f"{self.nome}({args})"


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
# Gramatica Fun (Atividade 10):
#
#   programa ::= decl* 'main' '{' cmd* 'return' exp ';' '}'
#   decl     ::= vardecl | fundecl
#   vardecl  ::= 'var' ident '=' exp ';'
#   fundecl  ::= 'fun' ident '(' arglist? ')'
#                '{' vardecl* cmd* 'return' exp ';' '}'
#   arglist  ::= ident (',' ident)*
#   cmd      ::= se | enquanto | atrib
#   se       ::= 'if' exp bloco ('else' bloco)?      # else opcional (extensao)
#   enquanto ::= 'while' exp bloco
#   bloco    ::= '{' cmd* '}'
#   atrib    ::= ident '=' exp ';'
#   exp      ::= exp_a ((op_comp) exp_a)*
#   exp_a    ::= exp_m (('+' | '-') exp_m)*
#   exp_m    ::= prim (('*' | '/') prim)*
#   prim     ::= num | ident | '(' exp ')' | chamada
#   chamada  ::= ident '(' params? ')'
#   params   ::= exp (',' exp)*
#   op_comp  ::= '<' | '>' | '<=' | '>=' | '==' | '!='
#
# Tres niveis de precedencia, do mais baixo para o mais alto: comparacao,
# aditivo, multiplicativo. Todos associativos a esquerda.
#
# Para diferenciar uma referencia a variavel de uma chamada de funcao em
# `prim`, ambas comecando com IDENTIFICADOR, e preciso olhar um token alem:
# se vier um '(' logo depois do identificador, e chamada; caso contrario, e
# variavel (secao 4 do guia da Atividade 10).

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
        # decl* : 'var' inicia uma declaracao de variavel global, 'fun' inicia
        # uma declaracao de funcao; qualquer outro token encerra a lista de
        # declaracoes e exige a palavra-chave 'main'
        declaracoes = []
        while True:
            tipo = self._peek().tipo
            if tipo == VAR:
                declaracoes.append(self.analisa_vardecl())
            elif tipo == FUN:
                declaracoes.append(self.analisa_fundecl())
            else:
                break
        self._verifica_prox(MAIN)
        comandos, exp_retorno = self.analisa_corpo()
        return Programa(declaracoes, comandos, exp_retorno)

    def analisa_vardecl(self):
        self._verifica_prox(VAR)
        tok_id = self._verifica_prox(IDENTIFICADOR)
        self._verifica_prox(IGUAL)
        exp = self.analisa_exp()
        self._verifica_prox(PONTO_VIRGULA)
        return Declaracao(tok_id.lexema, exp)

    def analisa_fundecl(self):
        self._verifica_prox(FUN)
        tok_id = self._verifica_prox(IDENTIFICADOR)
        self._verifica_prox(PAREN_ESQ)
        params = self.analisa_lista_parametros_formais()
        self._verifica_prox(PAREN_DIR)
        self._verifica_prox(CHAVE_ESQ)
        vardecls = []
        while self._peek().tipo == VAR:
            vardecls.append(self.analisa_vardecl())
        comandos = self.analisa_lista_cmd()
        self._verifica_prox(RETORNO)
        exp_retorno = self.analisa_exp()
        self._verifica_prox(PONTO_VIRGULA)
        self._verifica_prox(CHAVE_DIR)
        return FuncDecl(tok_id.lexema, params, vardecls, comandos, exp_retorno)

    def analisa_lista_parametros_formais(self):
        # loop no estilo do pseudo-codigo do guia (secao 4): olha o proximo
        # token ate encontrar ')', consumindo uma virgula entre parametros
        params = []
        if self._peek().tipo == PAREN_DIR:
            return params
        params.append(self._verifica_prox(IDENTIFICADOR).lexema)
        while self._peek().tipo == VIRGULA:
            self._proximo_token()
            params.append(self._verifica_prox(IDENTIFICADOR).lexema)
        return params

    def analisa_lista_argumentos(self):
        args = []
        if self._peek().tipo == PAREN_DIR:
            return args
        args.append(self.analisa_exp())
        while self._peek().tipo == VIRGULA:
            self._proximo_token()
            args.append(self.analisa_exp())
        return args

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
            if self._peek().tipo == PAREN_ESQ:
                self._proximo_token()
                args = self.analisa_lista_argumentos()
                self._verifica_prox(PAREN_DIR)
                return Chamada(tok.lexema, args)
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
