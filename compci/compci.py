# Driver de linha de comando do compilador EC1.
# Atividade 04: --tokens imprime a sequencia de tokens (analisador lexico).
# Atividade 05: analise sintatica, AST e interpretacao por varredura da arvore.

import sys

from lexer import EOF, ErroLexico, formatar, tokenizar
from parser import ErroSintatico, analisar


def main():
    args = sys.argv[1:]

    modo_tokens = "--tokens" in args
    args = [a for a in args if a != "--tokens"]

    if len(args) != 1:
        print("uso: python3 compci.py [--tokens] arquivo.ci", file=sys.stderr)
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

    print(f"arvore: {arvore.imprimir()}")
    print(f"valor: {arvore.avaliar()}")


if __name__ == "__main__":
    main()
