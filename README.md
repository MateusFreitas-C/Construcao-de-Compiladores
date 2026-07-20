# Compilador EV (Expressões com Variáveis)

Compilador completo para a linguagem **EV (Expressões com Variáveis)** —
Atividade 08. Um programa EV é uma série de zero ou mais declarações de 
variáveis seguidas de uma expressão final. As expressões aritméticas 
suportam `+ - * /`, variáveis e literais inteiros, em que os parênteses são 
**opcionais**: a ordem das operações segue as convenções usuais de 
precedência (`*` e `/` antes de `+` e `-`) e associatividade à esquerda.

Exemplos validos:

```
x = 7 + 5 * 3;     # multiplicacao antes da soma
y = x - 8 - 2;     # associatividade a esquerda: (22 - 8) - 2 = 12
= (x + y) * 3      # parenteses forcam a soma primeiro: (22 + 12) * 3 = 102
```

O compilador percorre as tres etapas classicas e gera assembly x86-64 pronto
para ser montado e executado:

1. **Análise léxica** (`compci/lexer.py`) — transforma o texto em tokens.
2. **Análise sintática** (`compci/parser.py`) — constrói a árvore de sintaxe
   abstrata (AST) com os nós `Programa`, `Declaracao`, `Var`, `Const` e `OpBin`.
3. **Análise semântica** (`compci/semantic.py`) — verifica se todas as variáveis 
   utilizadas nas expressões foram previamente declaradas.
4. **Geração de código** (`compci/codegen.py`) — percorre a AST e emite
   assembly com seção `.bss` para as variáveis declaradas.

## Gramatica

```
programa ::= decl* result
decl     ::= ident '=' exp_a ';'
result   ::= '=' exp_a
exp_a    ::= exp_m (('+' | '-') exp_m)*
exp_m    ::= prim (('*' | '/') prim)*
prim     ::= num | ident | '(' exp_a ')'
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
| Erro léxico (caractere inválido)      | mensagem em `stderr` | 2               |
| Erro sintático (expressão malformada) | mensagem em `stderr` | 3               |
| Erro semântico (variável não declarada)| mensagem em `stderr` | 4               |

## Esquema de geracao de codigo

O resultado da expressao termina em `RAX`; o programa entao chama `imprime_num`
e `sair` (definidos em `compci/runtime.s`). Valores intermediarios sao guardados
na pilha, usando apenas dois registradores independente do tamanho da expressao:

- Constante `n`: `mov $n, %rax`.
- Operacao binaria: gera o operando **direito** primeiro e o empilha
  (`push %rax`), gera o operando esquerdo, desempilha o direito em `RBX`
  (`pop %rbx`) e aplica a operacao. Assim o esquerdo fica em `RAX` e o direito
  em `RBX`, o que produz a ordem correta para subtracao e divisao.

Variáveis são alocadas na seção `.bss` utilizando `.lcomm var_name, 8`.
- Declarar e atribuir: a expressão é avaliada (resultado em `RAX`), e então `mov %rax, var_name`.
- Usar variável: `mov var_name, %rax`.

Operadores binários mantêm a lógica de empilhar resultados temporários: `+` → `add`, `-` → `sub`, `*` → `imul`, `/` → `cqo` + `idiv %rbx`.

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

- `compci/tests/lexer.t` — tokens, incluindo detecção de erros em números com letras (`237axy`).
- `compci/tests/parser.t` — árvore, valor e casos de erros sintáticos.
- `compci/tests/semantic.t` — análise de declarações e verificação de variáveis não declaradas.
- `compci/tests/codegen.t` — assembly determinístico e testes **end-to-end** que
  montam, linkam e executam o binário, conferindo o resultado numérico.

Os testes de geracao de codigo precisam de `as`/`ld` (binutils); por isso a forma
recomendada de rodar a suite completa e via Docker:

```
docker build -t compci compci/
docker run --rm compci    # roda lexer.t, parser.t, semantic.t e codegen.t
```

Localmente, sem binutils, da para rodar as etapas que nao montam codigo:

```
pip install cram
cram compci/tests/lexer.t compci/tests/parser.t compci/tests/semantic.t
```
