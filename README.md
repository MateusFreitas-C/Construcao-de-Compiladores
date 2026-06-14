# Compilador EC1

Compilador completo para a linguagem **EC1 (Expressoes Constantes 1)** —
Atividade 06. Um programa EC1 e uma expressao aritmetica totalmente parentizada
com `+ - * /` e literais inteiros (ex.: `(33 + (912 * 11))`).

O compilador percorre as tres etapas classicas e gera assembly x86-64 pronto
para ser montado e executado:

1. **Analise lexica** (`compci/lexer.py`) — transforma o texto em tokens.
2. **Analise sintatica** (`compci/parser.py`) — constroi a arvore de sintaxe
   abstrata (AST) com os nos `Const` e `OpBin`.
3. **Geracao de codigo** (`compci/codegen.py`) — percorre a AST e emite assembly.

## Uso

```
python3 compci/compci.py caminho/para/arquivo.ci
```

No modo padrao o compilador grava o assembly em `arquivo.s`, completo e pronto
para montar. Flags disponiveis:

| Flag       | Efeito                                                   |
|------------|----------------------------------------------------------|
| (nenhuma)  | Gera `arquivo.s` (geracao de codigo — Atividade 06).     |
| `--stdout` | Imprime o assembly na saida padrao, sem gravar arquivo.  |
| `--ast`    | Imprime a arvore sintatica e seu valor (Atividade 05).   |
| `--tokens` | Imprime a sequencia de tokens (Atividade 04).            |

## Erros

| Situacao                              | Saida                | Codigo de saida |
|---------------------------------------|----------------------|-----------------|
| Erro lexico (caractere invalido)      | mensagem em `stderr` | 2               |
| Erro sintatico (expressao malformada) | mensagem em `stderr` | 3               |

## Esquema de geracao de codigo

O resultado da expressao termina em `RAX`; o programa entao chama `imprime_num`
e `sair` (definidos em `compci/runtime.s`). Valores intermediarios sao guardados
na pilha, usando apenas dois registradores independente do tamanho da expressao:

- Constante `n`: `mov $n, %rax`.
- Operacao binaria: gera o operando **direito** primeiro e o empilha
  (`push %rax`), gera o operando esquerdo, desempilha o direito em `RBX`
  (`pop %rbx`) e aplica a operacao. Assim o esquerdo fica em `RAX` e o direito
  em `RBX`, o que produz a ordem correta para subtracao e divisao.

Operadores: `+` → `add`, `-` → `sub`, `*` → `imul`, `/` → `cqo` + `idiv %rbx`.

## Montar e executar

`compci/build.sh` automatiza compilacao, montagem (`as`), ligacao (`ld`) e
execucao:

```
cd compci && bash build.sh tests/ok.ci
```

Requer `runtime.s` no diretorio de trabalho (o assembly gerado usa
`.include "runtime.s"`).

## Rodar os testes

A suite usa [cram](https://bitheap.org/cram/) e cobre as tres etapas:

- `compci/tests/lexer.t` — tokens (Atividade 04).
- `compci/tests/parser.t` — arvore e valor, e casos de erro (Atividade 05).
- `compci/tests/codegen.t` — assembly deterministico e testes **end-to-end** que
  montam, linkam e executam o binario, conferindo o resultado numerico.

Os testes de geracao de codigo precisam de `as`/`ld` (binutils); por isso a forma
recomendada de rodar a suite completa e via Docker:

```
docker build -t compci compci/
docker run --rm compci    # roda lexer.t, parser.t e codegen.t
```

Localmente, sem binutils, da para rodar as etapas que nao montam codigo:

```
pip install cram
cram compci/tests/lexer.t compci/tests/parser.t
```

## Nota sobre otimizacao

Como toda expressao EC1 e constante, o programa inteiro poderia ser avaliado em
tempo de compilacao e reduzido a um unico `mov $resultado, %rax` (propagacao de
constantes). O compilador atual gera o codigo fiel ao esquema de pilha, sem essa
otimizacao; ela fica registrada como possivel melhoria futura.
