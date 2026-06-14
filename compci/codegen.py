from parser import Const, OpBin

# instrucao aritmetica por operador (esquerdo em RAX, direito em RBX)
INSTRUCAO = {
    "+": "add %rbx, %rax",
    "-": "sub %rbx, %rax",
    "*": "imul %rbx, %rax",
}


def _gerar_exp(no, linhas):
    if isinstance(no, Const):
        linhas.append(f"mov ${no.valor}, %rax")
        return
    if isinstance(no, OpBin):
        _gerar_exp(no.dir, linhas)
        linhas.append("push %rax")
        _gerar_exp(no.esq, linhas)
        linhas.append("pop %rbx")
        if no.op == "/":
            linhas.append("cqo")
            linhas.append("idiv %rbx")
        else:
            linhas.append(INSTRUCAO[no.op])
        return
    raise TypeError(f"no de AST desconhecido: {no!r}")


# modelo de saida completo (Secao 5 / Atividade 02)
PROLOGO = [
    "    #",
    "    # codigo gerado pelo compilador EC1",
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


def gerar_programa(arvore):
    """Retorna o assembly completo (string) para a arvore sintatica dada."""
    corpo = []
    _gerar_exp(arvore, corpo)
    linhas = list(PROLOGO)
    linhas.extend("    " + instr for instr in corpo)
    linhas.extend(EPILOGO)
    return "\n".join(linhas) + "\n"
