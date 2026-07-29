# Compilador Cmd

Compilador completo para a linguagem **Cmd** — Atividade 09. É a primeira
linguagem Turing-completa do projeto: além das expressões aritméticas com
variáveis que já existiam na linguagem EV, ela tem um comando condicional, um
comando de repetição e um comando de atribuição, o que basta para expressar
qualquer algoritmo.

Um programa Cmd é composto por zero ou mais declarações, seguidas de um corpo
delimitado por chaves com zero ou mais comandos e uma expressão de resultado
introduzida por `return`.

```
n = 1;
m = 10;
soma = 0;
{
  while n < m {
    soma = soma + n;
    n = n + 1;
  }
  return soma;
}
```

O programa acima soma os inteiros de `n` até `m - 1`, resultando em 45.

O menor programa possível é apenas o corpo:

```
{
  return 7 * 6;
}
```

O compilador percorre as quatro etapas clássicas e gera assembly x86-64 pronto
para ser montado e executado:

1. **Análise léxica** (`compci/lexer.py`) — transforma o texto em tokens,
   incluindo operadores de dois caracteres e palavras-chave.
2. **Análise sintática** (`compci/parser.py`) — constrói a árvore de sintaxe
   abstrata (AST) com os nós de expressão `Const`, `Var` e `OpBin`, os nós de
   comando `Se`, `Enquanto` e `Atribuicao`, e a raiz `Programa`.
3. **Análise semântica** (`compci/semantic.py`) — verifica se toda variável
   usada em expressões foi declarada, e se toda atribuição tem como alvo uma
   variável já declarada.
4. **Geração de código** (`compci/codegen.py`) — percorre a AST e emite
   assembly com seção `.bss` para as variáveis, saltos e rótulos para os
   comandos.

## Gramática

```
programa ::= decl* corpo
decl     ::= ident '=' exp ';'
corpo    ::= '{' cmd* 'return' exp ';' '}'
cmd      ::= se | enquanto | atrib
se       ::= 'if' exp bloco ('else' bloco)?
enquanto ::= 'while' exp bloco
bloco    ::= '{' cmd* '}'
atrib    ::= ident '=' exp ';'
exp      ::= exp_a ((op_comp) exp_a)*
exp_a    ::= exp_m (('+' | '-') exp_m)*
exp_m    ::= prim (('*' | '/') prim)*
prim     ::= num | ident | '(' exp ')'
op_comp  ::= '<' | '>' | '<=' | '>=' | '==' | '!='
num      ::= digito digito*
ident    ::= letra (letra | digito)*
```

As chaves nos corpos do `if` e do `while` **não** são opcionais.

O comando de atribuição tem a mesma sintaxe da declaração de uma variável, mas
declarações só podem aparecer antes do corpo, e atribuições só em lugares que
aceitam comandos. A atribuição **não cria** variáveis: qualquer variável usada
no programa precisa ser declarada no começo. A distinção entre as duas formas é
puramente posicional — antes do `{` é declaração, dentro é comando.

`return` não é um comando, e portanto não pode aparecer dentro de um `if` ou de
um `while`.

### Precedência

Três níveis, do mais baixo para o mais alto, todos associativos à esquerda:

| Nível          | Operadores                    | Associatividade |
|----------------|-------------------------------|-----------------|
| Comparação     | `<` `>` `<=` `>=` `==` `!=`   | esquerda        |
| Aditivo        | `+` `-`                       | esquerda        |
| Multiplicativo | `*` `/`                       | esquerda        |

Assim `1 + 2 < 4` agrupa como `(1 + 2) < 4`, e `7 + 5 * 3` como `7 + (5 * 3)`.
Parênteses continuam disponíveis para forçar outra ordem.

O analisador sintático descendente recursivo tem uma função por não-terminal
(`analisa_exp`, `analisa_exp_a`, `analisa_exp_m`, `analisa_prim`); cada uma
trata a repetição `(op ...)*` com um laço que consulta o próximo token sem
consumi-lo (`_peek`) e só avança (`_proximo_token`) quando o token é um operador
do nível esperado. Isso evita recursão à esquerda e gera árvores associativas à
esquerda, já que cada `OpBin` intermediário vira o operando esquerdo do próximo
operador.

### Valores de verdade

A linguagem não tem um tipo booleano separado. Um valor igual a zero é
considerado falso, e qualquer valor diferente de zero é verdadeiro. Os
operadores de comparação produzem exatamente `1` ou `0`.

## Diferenças em relação ao guia

A Atividade 09 permite alterar a sintaxe concreta e implementar extensões. Esta
implementação tem três desvios em relação à linguagem Cmd como especificada no
guia:

1. **Operadores `<=`, `>=` e `!=`** — acrescentados ao mesmo nível de
   precedência das demais comparações. O guia só define `<`, `>` e `==`, o que
   obriga a contornos como escrever `m + 1 > n` para dizer `m >= n`.
2. **Braço `else` opcional** — o guia torna o `else` obrigatório, o que força
   ramos artificiais como `delta = delta;`. Aqui o `else` pode ser omitido; a
   ambiguidade é resolvida com um lookahead de um token após o bloco `then`,
   ligando o `else` ao `if` mais interno.
3. **Correção de erratas da gramática do guia** — a produção impressa,
   `<exp> ::= <exp_a> (('<' | '>' | '=')* <exp_a>)*`, tem um `*` a mais e usa
   `'='` onde a seção de análise léxica descreve o operador de igualdade como
   `==`. Adotamos `==` e a forma repetida convencional.

Não foram implementados: operadores booleanos `and`/`or`/`not`, comando de
entrada de dados, criação implícita de variável por atribuição, nem escopo
léxico aninhado.

## Uso

```
python3 compci/compci.py caminho/para/arquivo.ci
```

No modo padrão o compilador grava o assembly em `arquivo.s`, completo e pronto
para montar. Flags disponíveis:

| Flag       | Efeito                                                        |
|------------|---------------------------------------------------------------|
| (nenhuma)  | Gera `arquivo.s`.                                             |
| `--stdout` | Imprime o assembly na saída padrão, sem gravar arquivo.       |
| `--ast`    | Imprime a árvore sintática e **interpreta** o programa.       |
| `--tokens` | Imprime a sequência de tokens.                                |

O modo `--ast` não apenas mostra a árvore: ele executa o programa, percorrendo
os comandos e avaliando o `return`. Isso o torna uma conferência independente
do assembly gerado — se o valor impresso por `--ast` e a saída do binário
divergirem, há bug na geração de código. A suíte de testes usa exatamente esse
cruzamento.

## Erros

| Situação                                 | Saída                | Código de saída |
|------------------------------------------|----------------------|-----------------|
| Erro léxico (caractere inválido)          | mensagem em `stderr` | 2               |
| Erro sintático (programa malformado)      | mensagem em `stderr` | 3               |
| Erro semântico (variável não declarada)   | mensagem em `stderr` | 4               |

Os erros semânticos cobrem dois casos, com mensagens distintas: uso de variável
não declarada em uma expressão, e atribuição cujo alvo não foi declarado.

## Esquema de geração de código

O resultado da expressão de `return` termina em `RAX`; o programa então chama
`imprime_num` e `sair` (definidos em `compci/runtime.s`). Valores intermediários
são guardados na pilha, usando apenas dois registradores independente do
tamanho da expressão:

- Constante `n`: `mov $n, %rax`.
- Operação binária: gera o operando **direito** primeiro e o empilha
  (`push %rax`), gera o operando esquerdo, desempilha o direito em `RBX`
  (`pop %rbx`) e aplica a operação. Assim o esquerdo fica em `RAX` e o direito
  em `RBX`, o que produz a ordem correta para subtração e divisão.

Operadores aritméticos: `+` → `add`, `-` → `sub`, `*` → `imul`,
`/` → `cqo` + `idiv %rbx`.

Variáveis são alocadas na seção `.bss` com `.lcomm var_nome, 8`. Declarar e
atribuir avaliam a expressão (resultado em `RAX`) e emitem `mov %rax, var_nome`;
usar uma variável emite `mov var_nome, %rax`. Como a atribuição não cria
variáveis, a seção `.bss` é alimentada apenas pelas declarações.

### Espaço de nomes dos símbolos

O montador tem um único espaço de nomes para tudo: variáveis, rótulos de salto e
símbolos do `runtime.s` disputam o mesmo conjunto. Definir o mesmo nome duas
vezes é erro de montagem. Como o programador escolhe livremente os nomes das
variáveis, os três grupos precisam ser separados **por construção**, e não por
convenção:

| Origem | Forma | Por que não colide |
|--------|-------|--------------------|
| Variáveis do programa | `var_nome` | o prefixo as afasta de `buffer` e `sair`, do runtime |
| Rótulos gerados | `.Lfim0`, `.Linicio0`, `.Lfalso0` | um identificador Cmd tem que começar com letra, então nenhum programa produz um símbolo iniciado por `.` |

Sem isso, um programa que declarasse uma variável chamada `Lfim0` ou `buffer`
geraria assembly que não monta. O prefixo `.L` tem ainda a vantagem de ser
reconhecido pelo GNU `as` como símbolo local, que não vai para a tabela de
símbolos do executável.

### Comparações

Para `A op B`, com o operando direito já empilhado e desempilhado em `RBX`:

```
    xor %rcx, %rcx
    cmp %rbx, %rax
    setl %cl            # setl, setg, setle, setge, setz ou setnz
    mov %rcx, %rax
```

`cmp` faz a subtração `A - B` sem armazenar o resultado, apenas alterando os
*flags*. As instruções `SETcc` leem esses flags e colocam 0 ou 1 num operando de
8 bits — daí o uso de `%cl`, o sub-registrador de `RCX`.

O `xor %rcx, %rcx` está ali por dois motivos, e a **ordem importa**: ele zera
`RCX` inteiro, porque `SETcc` só escreve nos 8 bits baixos e deixaria lixo nos
56 bits altos; mas `xor` também limpa ZF, SF e OF. Por isso ele precisa vir
*antes* do `cmp` — invertida, a ordem destruiria justamente os flags que o
`SETcc` vai ler.

Mapeamento: `<` → `setl`, `>` → `setg`, `<=` → `setle`, `>=` → `setge`,
`==` → `setz`, `!=` → `setnz`.

### Condicional

```
    <codigo_cond>
    cmp $0, %rax
    jz Lfalso0
    <codigo_entao>
    jmp Lfim0
Lfalso0:
    <codigo_senao>
Lfim0:
```

`cmp $0, %rax` testa se o resultado da condição é zero (falso); nesse caso `JZ`
salta para o braço falso. Quando o `else` é omitido, `<codigo_senao>` é vazio e
os dois rótulos continuam sendo emitidos — o `jmp` seguido do rótulo vira uma
instrução morta, mas manter uma única forma de emissão evita um segundo caminho
de código.

### Repetição

```
Linicio0:
    <codigo_cond>
    cmp $0, %rax
    jz Lfim0
    <codigo_corpo>
    jmp Linicio0
Lfim0:
```

### Rótulos

Cada `if` e cada `while` recebe um id único de um contador. O `if` gera
`Lfalso<n>` e `Lfim<n>`; o `while` gera `Linicio<n>` e `Lfim<n>`. Como os ids
são únicos entre todas as construções, o `Lfim` compartilhado entre os dois
modelos nunca colide, inclusive com laços aninhados.

O contador vive na instância da classe `Gerador`, não no módulo: cada
compilação começa do zero, o que mantém o assembly determinístico e testável.

## Montar e executar

`compci/build.sh` automatiza compilação, montagem (`as`), ligação (`ld`) e
execução:

```
cd compci && bash build.sh tests/soma_loop.ci
```

Requer `runtime.s` no diretório de trabalho (o assembly gerado usa
`.include "runtime.s"`).

## Rodar os testes

A suíte usa [cram](https://bitheap.org/cram/) e cobre as quatro etapas:

- `compci/tests/lexer.t` — tokens, incluindo a distinção entre `=` e `==`, os
  operadores de dois caracteres (`<=`, `>=`, `!=`), palavras-chave versus
  identificadores que começam com elas (`ifx`), e erros léxicos.
- `compci/tests/parser.t` — árvores de `if`/`else`, `if` sem `else`, `while` e
  atribuição; precedência e associatividade dos três níveis; erros sintáticos.
- `compci/tests/semantic.t` — variável não declarada em expressão, dentro de
  `if` e de `while`, e atribuição a variável não declarada.
- `compci/tests/codegen.t` — assembly determinístico (comparação, `if`, `while`,
  seção `.bss`) e testes **end-to-end** que montam, linkam e executam o binário,
  conferindo o resultado numérico. Inclui `colisao_rotulo.ci` e
  `colisao_runtime.ci`, que declaram variáveis com os nomes dos rótulos gerados
  e dos símbolos do runtime — os casos que o esquema de prefixos existe para
  tornar impossíveis.

Os programas de exemplo do guia estão incluídos e são executados de ponta a
ponta:

| Programa             | O que calcula                                   | Resultado |
|----------------------|-------------------------------------------------|-----------|
| `tests/delta.ci`     | valor absoluto do discriminante (a=1, b=2, c=3) | 8         |
| `tests/soma_loop.ci` | soma dos inteiros de 1 a 9                      | 45        |
| `tests/resto.ci`     | resto de 10 por 4, por subtração sucessiva      | 2         |
| `tests/mdc.ci`       | máximo divisor comum de 18 e 12                 | 6         |

Para cada um deles, o teste compara a saída do binário com o valor calculado
pelo interpretador (`--ast`), de modo que uma divergência aponta bug na geração
de código.

Os testes de geração de código precisam de `as`/`ld` (binutils); por isso a
forma recomendada de rodar a suíte completa é via Docker:

```
docker build -t compci compci/
docker run --rm compci    # roda lexer.t, parser.t, semantic.t e codegen.t
```

Localmente, com binutils instalado:

```
pip install cram
cd compci && cram tests/lexer.t tests/parser.t tests/semantic.t tests/codegen.t
```

Sem binutils, dá para rodar as etapas que não montam código:

```
cram compci/tests/lexer.t compci/tests/parser.t compci/tests/semantic.t
```
