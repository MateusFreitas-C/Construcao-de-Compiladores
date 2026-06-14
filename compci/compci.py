# Driver de linha de comando do compilador EC1.
# Atividade 04: --tokens imprime a sequencia de tokens (analisador lexico).
# Atividade 05: --ast imprime a arvore sintatica e seu valor (interpretacao).
# Atividade 06: modo padrao gera assembly x86-64 e grava arquivo.s.

import sys

from lexer import EOF, ErroLexico, formatar, tokenizar
from parser import ErroSintatico, analisar
from codegen import gerar_programa


def main():
    args = sys.argv[1:]

    modo_tokens = "--tokens" in args
    modo_ast = "--ast" in args
    modo_stdout = "--stdout" in args
    args = [a for a in args if a not in ("--tokens", "--ast", "--stdout")]

    if len(args) != 1:
        print(
            "uso: python3 compci.py [--tokens | --ast | --stdout] arquivo.ci",
            file=sys.stderr,
        )
        sys.exit(1)

    nome_entrada = args[0]

    try:
        with open(nome_entrada) as f:
            texto = f.read()
    except FileNotFoundError:
        print(f"erro: arquivo '{nome_entrada}' nao encontrado", file=sys.stderr)
        sys.exit(1)

    try:
        tokens = tokenizar(texto)
    except ErroLexico as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)

    if modo_tokens:
        for tok in tokens:
            if tok.tipo == EOF:
                continue
            print(formatar(tok))
        return

    try:
        arvore = analisar(tokens)
    except ErroSintatico as e:
        print(str(e), file=sys.stderr)
        sys.exit(3)

    if modo_ast:
        print(f"arvore: {arvore.imprimir()}")
        print(f"valor: {arvore.avaliar()}")
        return

    # modo padrao (Atividade 06): geracao de codigo
    assembly = gerar_programa(arvore)

    if modo_stdout:
        sys.stdout.write(assembly)
        return

    if nome_entrada.endswith(".ci"):
        nome_saida = nome_entrada[: -len(".ci")] + ".s"
    else:
        nome_saida = nome_entrada + ".s"

    with open(nome_saida, "w") as f:
        f.write(assembly)


if __name__ == "__main__":
    main()
