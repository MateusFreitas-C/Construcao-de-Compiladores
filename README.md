# Compilador EC2

Compilador completo para a linguagem **EC2 (Expressoes Constantes 2)** —
Atividade 07. Um programa EC2 e uma expressao aritmetica com `+ - * /` e
literais inteiros, em que os parenteses sao **opcionais**: a ordem das
operacoes segue as convencoes usuais de precedencia (`*` e `/` antes de `+`
e `-`) e associatividade a esquerda. Parenteses continuam podendo ser
usados para forcar outra ordem, ex.: `(7 + 5) * 3`.

Exemplos validos:

```
7 + 5 * 3          # = 22 (multiplicacao antes da soma)
10 - 8 - 2         # = 0  (associatividade a esquerda: (10 - 8) - 2)
(7 + 5) * 3        # = 36 (parenteses forcam a soma primeiro)
(33 + (912 * 11))  # totalmente parentizado (EC1) continua valido
```

O compilador percorre as tres etapas classicas e gera assembly x86-64 pronto
para ser montado e executado:

1. **Analise lexica** (`compci/lexer.py`) — transforma o texto em tokens.
2. **Analise sintatica** (`compci/parser.py`) — constroi a arvore de sintaxe
   abstrata (AST) com os nos `Const` e `OpBin`, aplicando precedencia e
   associatividade (ver "Gramatica" abaixo).
3. **Geracao de codigo** (`compci/codegen.py`) — percorre a AST e emite
   assembly (inalterada desde a Atividade 06).

## Gramatica

```
exp_a ::= exp_m (('+' | '-') exp_m)*
exp_m ::= prim (('*' | '/') prim)*
prim  ::= num | '(' exp_a ')'
```

`exp_a` e o nivel aditivo (precedencia mais baixa), `exp_m` e o nivel
multiplicativo, e `prim` reconhece constantes inteiras ou uma subexpressao
entre parenteses. O analisador sintatico descendente recursivo tem uma
funcao por nao-terminal (`analisa_exp_a`, `analisa_exp_m`, `analisa_prim`
em `compci/parser.py`); cada uma trata a repeticao `(op ...)*` com um laco
que consulta o proximo token sem consumi-lo (`_peek`) e so avanca
(`_proximo_token`) quando o token e um operador do nivel esperado. Isso
evita recursao a esquerda e gera arvores associativas a esquerda, ja que
cada `OpBin` intermediario vira o operando esquerdo do proximo operador.

Como `prim` ainda aceita `'(' exp_a ')'`, todo programa EC1 (totalmente
parentizado) continua sendo um programa EC2 valido, com a mesma arvore.

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

Esse esquema nao mudou em relacao a Atividade 06: a precedencia e
associatividade sao resolvidas inteiramente na analise sintatica, entao a
geracao de codigo so ve uma AST ja com a arvore correta.

## Montar e executar

`compci/build.sh` automatiza compilacao, montagem (`as`), ligacao (`ld`) e
execucao:

```
cd compci && bash build.sh tests/sem_parenteses.ci
```

Requer `runtime.s` no diretorio de trabalho (o assembly gerado usa
`.include "runtime.s"`).

## Rodar os testes

A suite usa [cram](https://bitheap.org/cram/) e cobre as tres etapas:

- `compci/tests/lexer.t` — tokens (Atividade 04).
- `compci/tests/parser.t` — arvore e valor, incluindo os casos de
  precedencia/associatividade sem parenteses da Atividade 07, e casos de
  erro (Atividade 05).
- `compci/tests/codegen.t` — assembly deterministico e testes **end-to-end** que
  montam, linkam e executam o binario, conferindo o resultado numerico,
  inclusive para as expressoes sem parenteses.

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

Como toda expressao EC2 e constante, o programa inteiro poderia ser avaliado em
tempo de compilacao e reduzido a um unico `mov $resultado, %rax` (propagacao de
constantes). O compilador atual gera o codigo fiel ao esquema de pilha, sem essa
otimizacao; ela fica registrada como possivel melhoria futura.
