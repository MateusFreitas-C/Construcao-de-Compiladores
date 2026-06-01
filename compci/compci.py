# le o arquivo, confere que o conteudo eh uma constante inteira
# e gerar um arquivo .s com o assembly correspondente.

import sys

# modelo de saida: a linha do mov eh montada com o valor lido
modelo = """\
  #
  # codigo gerado pelo compilador CI
  #
  .section .text
  .globl _start
_start:
  mov ${valor}, %rax
  call imprime_num
  call sair
  .include "runtime.s"
"""


def main():
    # 1. ler argumento da linha de comando
    if len(sys.argv) != 2:
        print("uso: python3 compci.py arquivo.ci", file=sys.stderr)
        sys.exit(1)

    nome_entrada = sys.argv[1]

    # 2. ler o arquivo de entrada
    try:
        with open(nome_entrada) as f:
            texto = f.read().strip()
    except FileNotFoundError:
        print(f"erro: arquivo '{nome_entrada}' nao encontrado",
              file=sys.stderr)
        sys.exit(1)

    # 3. analise: verificar se o conteudo eh uma constante inteira
    if texto == "":
        print("erro de sintaxe: arquivo vazio", file=sys.stderr)
        sys.exit(1)

    for i, c in enumerate(texto):
        if not c.isdigit():
            print(f"erro de sintaxe: caractere invalido '{c}' "
                  f"na posicao {i}", file=sys.stderr)
            sys.exit(1)

    valor = int(texto)

    # 4. sintese: gerar o assembly a partir do modelo
    assembly = modelo.format(valor=valor)

    # 5. escrever o arquivo de saida (mesmo nome, extensao .s)
    if nome_entrada.endswith(".ci"):
        nome_saida = nome_entrada[:-3] + ".s"
    else:
        nome_saida = nome_entrada + ".s"

    with open(nome_saida, "w") as f:
        f.write(assembly)

    print(f"gerado: {nome_saida}")


main()