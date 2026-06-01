# Driver de linha de comando do compilador EC1.
# Atividade 04: imprime a sequencia de tokens produzida pelo analisador lexico.

import sys

from lexer import tokenizar, formatar, ErroLexico, EOF


def main():
    if len(sys.argv) != 2:
        print("uso: python3 compci.py arquivo.ci", file=sys.stderr)
        sys.exit(1)

    nome_entrada = sys.argv[1]

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

    for tok in tokens:
        if tok.tipo == EOF:
            continue
        print(formatar(tok))


if __name__ == "__main__":
    main()
