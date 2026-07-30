from parser import Atribuicao, Chamada, Const, Declaracao, Enquanto, FuncDecl, OpBin, Se, Var

# instrucao aritmetica por operador (esquerdo em RAX, direito em RBX)
INSTRUCAO = {
    "+": "add %rbx, %rax",
    "-": "sub %rbx, %rax",
    "*": "imul %rbx, %rax",
}

# instrucao SETcc por operador de comparacao
COMPARACAO = {
    "<": "setl",
    ">": "setg",
    "<=": "setle",
    ">=": "setge",
    "==": "setz",
    "!=": "setnz",
}

# modelo de saida completo (Secao 5 / Atividade 02; secao 7 / Atividade 10)
PROLOGO = [
    "    #",
    "    # codigo gerado pelo compilador Fun",
    "    #",
    "    .section .text",
    "    .globl _start",
    "_start:",
]

EPILOGO = [
    "    call imprime_num",
    "    call sair",
]

RODAPE = [
    '    .include "runtime.s"',
]


def _simbolo(nome):
    """Nome de uma variavel global Fun na secao .bss.

    O prefixo evita colisao com os simbolos definidos no runtime.s
    (`buffer`, `sair`, `imprime_num`): sem ele, um programa que declare uma
    variavel com um desses nomes gera assembly que nao monta.
    """
    return f"var_{nome}"


def _rotulo(nome, n):
    """Rotulo de salto, unico por construcao (if/while).

    O ponto inicial e o que torna a colisao com variaveis impossivel, e nao
    apenas improvavel: um identificador Fun tem que comecar com letra, entao
    nenhum programa consegue produzir um simbolo `.Lfim0`. De brinde, o GNU as
    trata simbolos iniciados em `.L` como locais e nao os exporta.
    """
    return f".L{nome}{n}"


def _rotulo_func(nome):
    """Rotulo de uma funcao Fun, com o mesmo prefixo `fun_` para evitar
    colisao com simbolos do runtime/palavras reservadas, no mesmo espirito do
    prefixo `var_` das variaveis globais."""
    return f"fun_{nome}"


def _offsets_locais(func):
    """Deslocamentos (em bytes, relativos a RBP) de cada variavel local e
    parametro de uma funcao, seguindo a convencao de chamada da secao 6.1 do
    guia: locais em 0, 8, 16, ... e parametros em 8*L + 16 + 8*i (L = numero
    de locais, i = indice do parametro na lista de parametros)."""
    offsets = {}
    for i, vardecl in enumerate(func.vardecls):
        offsets[vardecl.nome] = 8 * i
    l = len(func.vardecls)
    for i, param in enumerate(func.params):
        offsets[param] = 8 * l + 16 + 8 * i
    return offsets


class Gerador:
    """Acumula instrucoes e distribui ids de rotulo.

    O contador vive na instancia, nao no modulo: cada compilacao comeca do
    zero, o que mantem o assembly deterministico.

    `tabela_local` e None ao gerar o bloco `main` (so ha variaveis globais).
    Ao gerar o corpo de uma funcao, e um dict nome -> deslocamento em bytes
    relativo a RBP, usado para decidir se uma `Var`/`Atribuicao` acessa uma
    variavel local/parametro (via `offset(%rbp)`) ou uma global (via
    `_simbolo`, na secao .bss).
    """

    def __init__(self, tabela_local=None):
        self.linhas = []
        self.contador = 0
        self.tabela_local = tabela_local

    def _novo_id(self):
        n = self.contador
        self.contador += 1
        return n

    def emitir(self, instr):
        self.linhas.append(instr)

    def _operando(self, nome):
        if self.tabela_local is not None and nome in self.tabela_local:
            return f"{self.tabela_local[nome]}(%rbp)"
        return _simbolo(nome)

    def gerar_exp(self, no):
        if isinstance(no, Const):
            self.emitir(f"mov ${no.valor}, %rax")
            return
        if isinstance(no, Var):
            self.emitir(f"mov {self._operando(no.nome)}, %rax")
            return
        if isinstance(no, Chamada):
            for arg in reversed(no.args):
                self.gerar_exp(arg)
                self.emitir("push %rax")
            self.emitir(f"call {_rotulo_func(no.nome)}")
            if no.args:
                self.emitir(f"add ${8 * len(no.args)}, %rsp")
            return
        if isinstance(no, OpBin):
            self.gerar_exp(no.dir)
            self.emitir("push %rax")
            self.gerar_exp(no.esq)
            self.emitir("pop %rbx")
            if no.op in COMPARACAO:
                # xor vem antes do cmp: ele zera RCX inteiro (SETcc so escreve
                # em CL e deixaria lixo nos 56 bits altos) mas tambem limpa
                # ZF/SF/OF, entao precisa acontecer antes de o cmp grava-los
                self.emitir("xor %rcx, %rcx")
                self.emitir("cmp %rbx, %rax")
                self.emitir(f"{COMPARACAO[no.op]} %cl")
                self.emitir("mov %rcx, %rax")
            elif no.op == "/":
                self.emitir("cqo")
                self.emitir("idiv %rbx")
            else:
                self.emitir(INSTRUCAO[no.op])
            return
        raise TypeError(f"no de AST desconhecido: {no!r}")

    def gerar_lista_cmd(self, comandos):
        for cmd in comandos:
            self.gerar_cmd(cmd)

    def gerar_cmd(self, cmd):
        if isinstance(cmd, Atribuicao):
            # a semantica ja garantiu que o simbolo existe (local ou global)
            self.gerar_exp(cmd.exp)
            self.emitir(f"mov %rax, {self._operando(cmd.nome)}")
            return
        if isinstance(cmd, Se):
            n = self._novo_id()
            falso = _rotulo("falso", n)
            fim = _rotulo("fim", n)
            self.gerar_exp(cmd.cond)
            self.emitir("cmp $0, %rax")
            self.emitir(f"jz {falso}")
            self.gerar_lista_cmd(cmd.entao)
            self.emitir(f"jmp {fim}")
            self.emitir(f"{falso}:")
            self.gerar_lista_cmd(cmd.senao)
            self.emitir(f"{fim}:")
            return
        if isinstance(cmd, Enquanto):
            n = self._novo_id()
            inicio = _rotulo("inicio", n)
            fim = _rotulo("fim", n)
            self.emitir(f"{inicio}:")
            self.gerar_exp(cmd.cond)
            self.emitir("cmp $0, %rax")
            self.emitir(f"jz {fim}")
            self.gerar_lista_cmd(cmd.corpo)
            self.emitir(f"jmp {inicio}")
            self.emitir(f"{fim}:")
            return
        raise TypeError(f"comando de AST desconhecido: {cmd!r}")


def _formatar_linhas(linhas):
    # rotulos ficam na coluna zero; instrucoes, indentadas
    return [linha if linha.endswith(":") else "    " + linha for linha in linhas]


def gerar_funcao(func):
    """Gera o rotulo, prologo, corpo e epilogo de uma funcao Fun, seguindo o
    resumo da secao 6.1.4 do guia. Retorna a lista de linhas de assembly
    (rotulo incluso, ja formatada)."""
    offsets = _offsets_locais(func)
    l = len(func.vardecls)
    ger = Gerador(tabela_local=offsets)

    for vardecl in func.vardecls:
        ger.gerar_exp(vardecl.exp)
        ger.emitir(f"mov %rax, {offsets[vardecl.nome]}(%rbp)")
    ger.gerar_lista_cmd(func.comandos)
    ger.gerar_exp(func.exp_retorno)

    corpo = ["push %rbp"]
    if l:
        corpo.append(f"sub ${8 * l}, %rsp")
    corpo.append("mov %rsp, %rbp")
    corpo.extend(ger.linhas)
    if l:
        corpo.append(f"add ${8 * l}, %rsp")
    corpo.append("pop %rbp")
    corpo.append("ret")

    return [f"{_rotulo_func(func.nome)}:"] + _formatar_linhas(corpo)


def gerar_programa(arvore):
    """Retorna o assembly completo (string) para a arvore sintatica dada."""
    var_decls = [d for d in arvore.declaracoes if isinstance(d, Declaracao)]
    func_decls = [d for d in arvore.declaracoes if isinstance(d, FuncDecl)]

    ger = Gerador()
    for decl in var_decls:
        ger.gerar_exp(decl.exp)
        ger.emitir(f"mov %rax, {_simbolo(decl.nome)}")
    ger.gerar_lista_cmd(arvore.comandos)
    ger.gerar_exp(arvore.exp_retorno)

    bss_linhas = []
    if var_decls:
        bss_linhas.append("    .section .bss")
        for var in sorted(set(d.nome for d in var_decls)):
            bss_linhas.append(f"    .lcomm {_simbolo(var)}, 8")
        bss_linhas.append("")

    linhas = list(bss_linhas) + list(PROLOGO)
    linhas.extend(_formatar_linhas(ger.linhas))
    linhas.extend(EPILOGO)

    for func in func_decls:
        linhas.append("")
        linhas.extend(gerar_funcao(func))

    linhas.append("")
    linhas.extend(RODAPE)
    return "\n".join(linhas) + "\n"
