from parser import Atribuicao, Const, Enquanto, OpBin, Se, Var

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

# modelo de saida completo (Secao 5 / Atividade 02)
PROLOGO = [
    "    #",
    "    # codigo gerado pelo compilador Cmd",
    "    #",
    "    .section .text",
    "    .globl _start",
    "_start:",
]

EPILOGO = [
    "    call imprime_num",
    "    call sair",
    '    .include "runtime.s"',
]


def _simbolo(nome):
    """Nome de uma variavel Cmd na secao .bss.

    O prefixo evita colisao com os simbolos definidos no runtime.s
    (`buffer`, `sair`, `imprime_num`): sem ele, um programa que declare uma
    variavel com um desses nomes gera assembly que nao monta.
    """
    return f"var_{nome}"


def _rotulo(nome, n):
    """Rotulo de salto, unico por construcao (if/while).

    O ponto inicial e o que torna a colisao com variaveis impossivel, e nao
    apenas improvavel: um identificador Cmd tem que comecar com letra, entao
    nenhum programa consegue produzir um simbolo `.Lfim0`. De brinde, o GNU as
    trata simbolos iniciados em `.L` como locais e nao os exporta.
    """
    return f".L{nome}{n}"


class Gerador:
    """Acumula instrucoes e distribui ids de rotulo.

    O contador vive na instancia, nao no modulo: cada compilacao comeca do
    zero, o que mantem o assembly deterministico.
    """

    def __init__(self):
        self.linhas = []
        self.contador = 0

    def _novo_id(self):
        n = self.contador
        self.contador += 1
        return n

    def emitir(self, instr):
        self.linhas.append(instr)

    def gerar_exp(self, no):
        if isinstance(no, Const):
            self.emitir(f"mov ${no.valor}, %rax")
            return
        if isinstance(no, Var):
            self.emitir(f"mov {_simbolo(no.nome)}, %rax")
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
            # a semantica ja garantiu que o simbolo existe no .bss
            self.gerar_exp(cmd.exp)
            self.emitir(f"mov %rax, {_simbolo(cmd.nome)}")
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


def gerar_programa(arvore):
    """Retorna o assembly completo (string) para a arvore sintatica dada."""
    ger = Gerador()

    for decl in arvore.declaracoes:
        ger.gerar_exp(decl.exp)
        ger.emitir(f"mov %rax, {_simbolo(decl.nome)}")

    ger.gerar_lista_cmd(arvore.comandos)
    ger.gerar_exp(arvore.exp_retorno)

    bss_linhas = []
    if arvore.declaracoes:
        bss_linhas.append("    .section .bss")
        variaveis = set(decl.nome for decl in arvore.declaracoes)
        for var in sorted(variaveis):
            bss_linhas.append(f"    .lcomm {_simbolo(var)}, 8")
        bss_linhas.append("")

    linhas = list(bss_linhas) + list(PROLOGO)
    for instr in ger.linhas:
        # rotulos ficam na coluna zero; instrucoes, indentadas
        linhas.append(instr if instr.endswith(":") else "    " + instr)
    linhas.extend(EPILOGO)
    return "\n".join(linhas) + "\n"
