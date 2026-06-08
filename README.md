# Compilador EC1

Compilador para a linguagem **EC1 (Expressoes Constantes 1)** — expressao aritmetica totalmente parentizada com `+ - * /` e literais inteiros (ex.: `(33 + (912 * 11))`).

O compilador realiza analise lexica e sintatica, produz a arvore de sintaxe abstrata (AST) e interpreta o programa por varredura da arvore.

## Uso

```
python3 compci/compci.py caminho/para/arquivo.ci
```

Saida para uma entrada valida:

```
arvore: (33 + (912 * 11))
valor: 10065
```

Para imprimir apenas a sequencia de tokens (comportamento da Atividade 04):

```
python3 compci/compci.py --tokens caminho/para/arquivo.ci
```

## Erros

| Situacao | Saida | Codigo de saida |
|---|---|---|
| Erro lexico (caractere invalido) | mensagem em `stderr` | 2 |
| Erro sintatico (expressao malformada) | mensagem em `stderr` | 3 |

## Rodar os testes

A suite usa [cram](https://bitheap.org/cram/):

```
pip install cram
cram compci/tests/lexer.t   # testes do analisador lexico (Atividade 04)
cram compci/tests/parser.t  # testes do analisador sintatico e interpretador (Atividade 05)
```

## Docker

```
docker build -t compci compci/
docker run --rm compci                       # roda cram tests/lexer.t
docker run --rm -v "$PWD":/work compci \
    python3 compci.py /work/arquivo.ci       # analisa um arquivo arbitrario
```
