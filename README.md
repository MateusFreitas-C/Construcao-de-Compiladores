# Analisador Lexico EC1

Analisador lexico para a linguagem **EC1 (Expressoes Constantes 1)** — Atividade
04. EC1 e uma expressao aritmetica totalmente parentizada com `+ - * /` e
literais inteiros (ex.: `(33 + (912 * 11))`).

O programa le um arquivo `.ci` passado como argumento e imprime a sequencia de
tokens, um por linha, no formato `<tipo, "lexema", posicao>` (posicao = indice
do caractere na entrada). Tipos: `ParenEsq`, `ParenDir`, `Soma`, `Sub`, `Mult`,
`Div`, `Numero`.

## Rodar o analisador

Em um arquivo qualquer:

```
python3 compci.py caminho/para/arquivo.ci
```

Saida em caso de erro lexico (caractere fora de `() + - * /` ou digitos): a
mensagem `Erro lexico na posicao N: caractere invalido 'X'` vai para `stderr` e
o processo sai com codigo != 0.

## Rodar os testes

A suite usa [cram](https://bitheap.org/cram/). Localmente:

```
pip install cram
cram compci/tests/lexer.t
```

Os testes cobrem: o programa-exemplo do enunciado, um literal isolado, uma
expressao com varios espacos em branco, e um caso de erro lexico.

## Docker

```
docker build -t compci compci/
docker run --rm compci                       # roda cram tests/lexer.t
docker run --rm -v "$PWD":/work compci \
    python3 compci.py /work/arquivo.ci       # analisa um arquivo arbitrario
```
