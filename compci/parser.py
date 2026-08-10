from lexer import (
    CHAVE_DIR,
    CHAVE_ESQ,
    COLCHETE_DIR,
    COLCHETE_ESQ,
    DIFERENTE,
    DIV,
    E_LOGICO,
    ENQUANTO,
    EOF,
    ESCREVE,
    FUN,
    NAO_LOGICO,
    OU_LOGICO,
    RESTO,
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
NIVEL_MULTIPLICATIVO = {MULT, DIV, RESTO}


class ErroSintatico(Exception):
    def __init__(self, pos, msg):
        self.pos = pos
        super().__init__(f"Erro sintatico na posicao {pos}: {msg}")


# --- Ambiente de avaliação ---

class Ambiente:
    """Dois escopos para o interpretador: `locais` (parametros e variaveis
    locais da funcao em execucao) e `globais`.

    A regra de resolucao replica exatamente `codegen._operando`: leitura e
    escrita procuram primeiro nos locais e caem nas globais se o nome nao for
    local. Isso importa porque o interpretador e o oraculo dos testes
    end-to-end — se as duas resolucoes divergirem, o cruzamento perde o valor.

    `locais` e None no escopo global (bloco `main` e inicializadores de
    variaveis globais).
    """

    def __init__(self, globais, funcoes, locais=None):
        self.globais = globais
        self.funcoes = funcoes
        self.locais = locais

    def ler(self, nome):
        if self.locais is not None and nome in self.locais:
            return self.locais[nome]
        return self.globais[nome]

    def escrever(self, nome, valor):
        if self.locais is not None and nome in self.locais:
            self.locais[nome] = valor
        else:
            self.globais[nome] = valor


# --- Nós da AST ---

def _div_trunc(a, b):
    """Divisao inteira truncada em direcao a zero, como a instrucao idiv."""
    quociente = abs(a) // abs(b)
    return quociente if (a < 0) == (b < 0) else -quociente


class Exp:
    pass


class Const(Exp):
    def __init__(self, valor):
        self.valor = valor

    def avaliar(self, amb):
        return self.valor

    def imprimir(self):
        return str(self.valor)


class OpBin(Exp):
    def __init__(self, op, esq, dir):
        self.op = op
        self.esq = esq
        self.dir = dir

    def avaliar(self, amb):
        # o operando DIREITO e avaliado primeiro, porque e isso que o gerador
        # de codigo faz (ver Gerador.gerar_exp: gera a direita, empilha, gera a
        # esquerda). A ordem so e observavel quando um operando tem efeito
        # colateral — uma chamada de funcao que escreve numa variavel global —
        # mas nesse caso os dois PRECISAM concordar, porque o interpretador e o
        # oraculo dos testes end-to-end
        v_dir = self.dir.avaliar(amb)
        v_esq = self.esq.avaliar(amb)
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
            return _div_trunc(v_esq, v_dir)
        if self.op == '%':
            # o resto que o idiv deixa em RDX tem o sinal do DIVIDENDO (resto
            # truncado), enquanto o % do Python segue o sinal do divisor.
            # Derivar do quociente truncado mantem os dois de acordo.
            return v_esq - _div_trunc(v_esq, v_dir) * v_dir
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


class OpLogico(Exp):
    """`&&` e `||` com curto-circuito.

    Nao e um OpBin porque a avaliacao do operando direito e CONDICIONAL: em
    `a && b`, se `a` for falso, `b` nunca e avaliado. Isso importa quando o
    operando tem efeito colateral, e e por isso que aqui o operando ESQUERDO e
    avaliado primeiro — ao contrario de OpBin, que avalia o direito primeiro
    para casar com o esquema de pilha do gerador. O gerador faz o mesmo com
    saltos condicionais, entao os dois continuam de acordo.

    O resultado e sempre 0 ou 1, como nas comparacoes.
    """

    def __init__(self, op, esq, dir):
        self.op = op
        self.esq = esq
        self.dir = dir

    def avaliar(self, amb):
        v_esq = self.esq.avaliar(amb)
        if self.op == '&&':
            if v_esq == 0:
                return 0
        else:  # '||'
            if v_esq != 0:
                return 1
        return 1 if self.dir.avaliar(amb) != 0 else 0

    def imprimir(self):
        return f'({self.esq.imprimir()} {self.op} {self.dir.imprimir()})'


class Nao(Exp):
    """Negacao logica unaria `!exp`: 1 se a expressao for zero, 0 caso
    contrario."""

    def __init__(self, exp):
        self.exp = exp

    def avaliar(self, amb):
        return 1 if self.exp.avaliar(amb) == 0 else 0

    def imprimir(self):
        return f'(!{self.exp.imprimir()})'


class Programa(Exp):
    def __init__(self, declaracoes, comandos, exp_retorno):
        # declaracoes mistura Declaracao (variavel global) e FuncDecl (funcao),
        # na ordem em que aparecem no texto: a analise semantica processa essa
        # lista sequencialmente, entao a ordem importa (permite referenciar
        # apenas o que foi declarado antes, exceto recursao direta)
        self.declaracoes = declaracoes
        self.comandos = comandos
        self.exp_retorno = exp_retorno

    def avaliar(self, amb=None):
        # o programa e a raiz: cria o proprio ambiente global, entao ignora
        # qualquer ambiente recebido (mantido so pela assinatura comum de Exp)
        globais = {}
        funcoes = {}
        amb = Ambiente(globais, funcoes)
        for decl in self.declaracoes:
            if isinstance(decl, FuncDecl):
                funcoes[decl.nome] = decl
            elif isinstance(decl, DeclaracaoArray):
                # a .bss ja zera a memoria, entao o interpretador tambem
                # comeca com todos os elementos em zero
                globais[decl.nome] = [0] * decl.tamanho
            else:
                globais[decl.nome] = decl.exp.avaliar(amb)
        for cmd in self.comandos:
            cmd.executar(amb)
        return self.exp_retorno.avaliar(amb)

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


class DeclaracaoArray:
    """Declaracao de um array global: `var a[10];`

    O tamanho e uma constante inteira conhecida em tempo de compilacao — e o
    que permite reservar o espaco na secao .bss. Nao ha inicializador: a .bss
    ja e zerada pelo carregador, entao os elementos comecam em zero de graca.
    """

    def __init__(self, nome, tamanho):
        self.nome = nome
        self.tamanho = tamanho

    def imprimir(self):
        return f"var {self.nome}[{self.tamanho}];"


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

    def avaliar(self, amb):
        func = amb.funcoes[self.nome]
        # os argumentos sao avaliados no ambiente do CHAMADOR, antes de o
        # ambiente da funcao existir, e da DIREITA para a ESQUERDA: o gerador
        # de codigo os empilha em ordem inversa (ver Gerador.gerar_exp), entao
        # e nessa ordem que os efeitos colaterais acontecem no binario
        valores = [arg.avaliar(amb) for arg in reversed(self.args)]
        valores.reverse()
        locais = dict(zip(func.params, valores))
        # o novo ambiente compartilha as globais mas tem locais proprios: por
        # isso uma chamada recursiva nao enxerga os locais da chamada anterior,
        # do mesmo jeito que cada ativacao tem seu proprio registro na pilha
        amb_local = Ambiente(amb.globais, amb.funcoes, locais)
        for vardecl in func.vardecls:
            locais[vardecl.nome] = vardecl.exp.avaliar(amb_local)
        for cmd in func.comandos:
            cmd.executar(amb_local)
        return func.exp_retorno.avaliar(amb_local)

    def imprimir(self):
        args = ", ".join(arg.imprimir() for arg in self.args)
        return f"{self.nome}({args})"


class Var(Exp):
    def __init__(self, nome):
        self.nome = nome

    def avaliar(self, amb):
        return amb.ler(self.nome)

    def imprimir(self):
        return self.nome


class IndiceArray(Exp):
    """Leitura de um elemento: `a[i]`, com `i` uma expressao qualquer."""

    def __init__(self, nome, indice):
        self.nome = nome
        self.indice = indice

    def avaliar(self, amb):
        return amb.ler(self.nome)[self.indice.avaliar(amb)]

    def imprimir(self):
        return f"{self.nome}[{self.indice.imprimir()}]"


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

    def executar(self, amb):
        amb.escrever(self.nome, self.exp.avaliar(amb))

    def imprimir(self, nivel):
        return f"{_ind(nivel)}{self.nome} = {self.exp.imprimir()};"


class Escreve(Cmd):
    """Comando `escreve exp;` — imprime o valor da expressao seguido de nova
    linha.

    E um COMANDO, e nao uma funcao primitiva chamada como `escreve(x)`, porque
    Fun nao tem comando-expressao: uma chamada so aparece dentro de uma
    expressao, e uma expressao solta nao e um comando valido. Como comando, a
    construcao encaixa na gramatica existente sem abrir esse buraco.

    No binario, reaproveita `imprime_num` do runtime.s — a mesma rotina que ja
    imprimia o valor final do programa.
    """

    def __init__(self, exp):
        self.exp = exp

    def executar(self, amb):
        print(self.exp.avaliar(amb))

    def imprimir(self, nivel):
        return f"{_ind(nivel)}escreve {self.exp.imprimir()};"


class AtribuicaoArray(Cmd):
    """Escrita em um elemento: `a[i] = exp;`"""

    def __init__(self, nome, indice, exp):
        self.nome = nome
        self.indice = indice
        self.exp = exp

    def executar(self, amb):
        # a ordem casa com o codegen: valor primeiro, depois indice
        valor = self.exp.avaliar(amb)
        amb.ler(self.nome)[self.indice.avaliar(amb)] = valor

    def imprimir(self, nivel):
        return (
            f"{_ind(nivel)}{self.nome}[{self.indice.imprimir()}] = "
            f"{self.exp.imprimir()};"
        )


class Se(Cmd):
    def __init__(self, cond, entao, senao):
        self.cond = cond
        self.entao = entao
        self.senao = senao

    def executar(self, amb):
        ramo = self.entao if self.cond.avaliar(amb) != 0 else self.senao
        for cmd in ramo:
            cmd.executar(amb)

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

    def executar(self, amb):
        while self.cond.avaliar(amb) != 0:
            for cmd in self.corpo:
                cmd.executar(amb)

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
#   decl     ::= vardecl | arraydecl | fundecl
#   vardecl  ::= 'var' ident '=' exp ';'
#   arraydecl::= 'var' ident '[' num ']' ';'
#   fundecl  ::= 'fun' ident '(' arglist? ')'
#                '{' vardecl* cmd* 'return' exp ';' '}'
#   arglist  ::= ident (',' ident)*
#   cmd      ::= se | enquanto | atrib | atrib_array | escreve
#   se       ::= 'if' exp bloco ('else' bloco)?      # else opcional (extensao)
#   enquanto ::= 'while' exp bloco
#   bloco    ::= '{' cmd* '}'
#   atrib    ::= ident '=' exp ';'
#   atrib_array ::= ident '[' exp ']' '=' exp ';'
#   escreve  ::= 'escreve' exp ';'
#   exp      ::= exp_ou
#   exp_ou   ::= exp_e ('||' exp_e)*
#   exp_e    ::= exp_c ('&&' exp_c)*
#   exp_c    ::= exp_a ((op_comp) exp_a)*
#   exp_a    ::= exp_m (('+' | '-') exp_m)*
#   exp_m    ::= prim (('*' | '/' | '%') prim)*
#   prim     ::= '!' prim | num | ident | '(' exp ')' | chamada | indice
#   chamada  ::= ident '(' params? ')'
#   indice   ::= ident '[' exp ']'
#   params   ::= exp (',' exp)*
#   op_comp  ::= '<' | '>' | '<=' | '>=' | '==' | '!='
#
# Cinco niveis de precedencia, do mais baixo para o mais alto: ou-logico,
# e-logico, comparacao, aditivo, multiplicativo. Todos associativos a esquerda.
# A negacao `!` e unaria e liga mais forte que todos eles, no nivel de `prim`.
#
# Para diferenciar uma referencia a variavel de uma chamada de funcao em
# `prim`, ambas comecando com IDENTIFICADOR, e preciso olhar um token alem:
# se vier um '(' logo depois do identificador, e chamada; caso contrario, e
# variavel (secao 4 do guia da Atividade 10). Os arrays entram no mesmo
# ponto de decisao: um '[' apos o identificador indica indexacao. O mesmo
# lookahead de um token resolve os tres casos, entao a gramatica continua
# LL(1) sobre o par (identificador, token seguinte).

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
        # `var a[10];` (array) e `var a = exp;` (escalar) so se distinguem pelo
        # token que segue o identificador — mesmo lookahead de um token usado
        # em `analisa_prim`
        self._verifica_prox(VAR)
        tok_id = self._verifica_prox(IDENTIFICADOR)
        if self._peek().tipo == COLCHETE_ESQ:
            self._proximo_token()
            tok_num = self._verifica_prox(NUMERO)
            tamanho = int(tok_num.lexema)
            if tamanho <= 0:
                raise ErroSintatico(
                    tok_num.pos, f"tamanho de array deve ser positivo, encontrado {tamanho}"
                )
            self._verifica_prox(COLCHETE_DIR)
            self._verifica_prox(PONTO_VIRGULA)
            return DeclaracaoArray(tok_id.lexema, tamanho)
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
            pos = self._peek().pos
            decl = self.analisa_vardecl()
            # arrays sao apenas globais nesta versao: o registro de ativacao
            # reserva 8 bytes por local (ver codegen._offsets_locais), entao um
            # array local exigiria slots de tamanho variavel. Rejeitar aqui, com
            # mensagem clara, e melhor do que gerar deslocamentos errados.
            if isinstance(decl, DeclaracaoArray):
                raise ErroSintatico(
                    pos,
                    f"array '{decl.nome}' local a funcao nao suportado; "
                    "arrays devem ser declarados no escopo global",
                )
            vardecls.append(decl)
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
            elif tipo == ESCREVE:
                comandos.append(self.analisa_escreve())
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

    def analisa_escreve(self):
        self._verifica_prox(ESCREVE)
        exp = self.analisa_exp()
        self._verifica_prox(PONTO_VIRGULA)
        return Escreve(exp)

    def analisa_atrib(self):
        # mesmo lookahead de sempre: um '[' apos o identificador indica
        # atribuicao a elemento de array
        tok_id = self._verifica_prox(IDENTIFICADOR)
        if self._peek().tipo == COLCHETE_ESQ:
            self._proximo_token()
            indice = self.analisa_exp()
            self._verifica_prox(COLCHETE_DIR)
            self._verifica_prox(IGUAL)
            exp = self.analisa_exp()
            self._verifica_prox(PONTO_VIRGULA)
            return AtribuicaoArray(tok_id.lexema, indice, exp)
        self._verifica_prox(IGUAL)
        exp = self.analisa_exp()
        self._verifica_prox(PONTO_VIRGULA)
        return Atribuicao(tok_id.lexema, exp)

    def analisa_exp(self):
        return self.analisa_exp_ou()

    def analisa_exp_ou(self):
        esq = self.analisa_exp_e()
        tok = self._peek()
        while tok.tipo == OU_LOGICO:
            self._proximo_token()
            dire = self.analisa_exp_e()
            esq = OpLogico(tok.lexema, esq, dire)
            tok = self._peek()
        return esq

    def analisa_exp_e(self):
        esq = self.analisa_exp_c()
        tok = self._peek()
        while tok.tipo == E_LOGICO:
            self._proximo_token()
            dire = self.analisa_exp_c()
            esq = OpLogico(tok.lexema, esq, dire)
            tok = self._peek()
        return esq

    def analisa_exp_c(self):
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
        # `!` e unaria e prefixa; a recursao em analisa_prim permite `!!x` e
        # faz a negacao ligar mais forte que qualquer operador binario
        if self._peek().tipo == NAO_LOGICO:
            self._proximo_token()
            return Nao(self.analisa_prim())
        tok = self._proximo_token()
        if tok.tipo == NUMERO:
            return Const(int(tok.lexema))
        if tok.tipo == IDENTIFICADOR:
            if self._peek().tipo == PAREN_ESQ:
                self._proximo_token()
                args = self.analisa_lista_argumentos()
                self._verifica_prox(PAREN_DIR)
                return Chamada(tok.lexema, args)
            if self._peek().tipo == COLCHETE_ESQ:
                self._proximo_token()
                indice = self.analisa_exp()
                self._verifica_prox(COLCHETE_DIR)
                return IndiceArray(tok.lexema, indice)
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
