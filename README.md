# Compilador Fun

Compilador completo para a linguagem **Fun** — Atividade 10. Estende a
linguagem Cmd (Atividade 09) com **funções**: declaração com a palavra-chave
`fun`, parâmetros, variáveis locais, chamada como expressão, recursão direta, e
um bloco `main` que marca o programa principal.

```
fun fat(n) {
  var res = 0;
  if n < 2 {
    res = 1;
  } else {
    res = n * fat(n - 1);
  }
  return res;
}
main {
  return fat(5);
}
```

O programa acima calcula `5! = 120` usando uma função diretamente recursiva.

O menor programa possível continua sendo só o bloco `main`:

```
main {
  return 7 * 6;
}
```

O compilador percorre as quatro etapas clássicas e gera assembly x86-64 pronto
para ser montado e executado:

1. **Análise léxica** (`compci/lexer.py`) — transforma o texto em tokens; a
   Atividade 10 acrescenta o token de vírgula e as palavras-chave `fun`, `var`
   e `main`.
2. **Análise sintática** (`compci/parser.py`) — constrói a árvore de sintaxe
   abstrata (AST). Além dos nós de Cmd (`Const`, `Var`, `OpBin`, `Se`,
   `Enquanto`, `Atribuicao`, `Declaracao`), agora existem `FuncDecl` (uma
   declaração de função) e `Chamada` (uma chamada de função, que é uma
   expressão primária como qualquer outra). `Programa.declaracoes` guarda
   `Declaracao`s e `FuncDecl`s **na ordem em que aparecem no texto** — essa
   ordem importa para a análise semântica.
3. **Análise semântica** (`compci/semantic.py`) — além de verificar variáveis
   não declaradas, agora verifica chamadas de função: se a função existe, se o
   nome não pertence a uma variável (e vice-versa), e se o número de
   parâmetros da chamada bate com o da declaração. Mantém uma tabela global
   (variáveis e funções) e, ao entrar no corpo de uma função, uma tabela local
   (parâmetros e variáveis locais) que tem precedência sobre a global.
4. **Geração de código** (`compci/codegen.py`) — além do que já existia (seção
   `.bss`, saltos e rótulos), agora emite um rótulo, prólogo e epílogo para
   cada função, usando a pilha do sistema para parâmetros e variáveis locais
   (convenção de chamada detalhada mais abaixo).

## Gramática

```
programa ::= decl* 'main' '{' cmd* 'return' exp ';' '}'
decl     ::= vardecl | fundecl
vardecl  ::= 'var' ident '=' exp ';'
fundecl  ::= 'fun' ident '(' arglist? ')'
             '{' vardecl* cmd* 'return' exp ';' '}'
arglist  ::= ident (',' ident)*
cmd      ::= se | enquanto | atrib
se       ::= 'if' exp bloco ('else' bloco)?
enquanto ::= 'while' exp bloco
bloco    ::= '{' cmd* '}'
atrib    ::= ident '=' exp ';'
exp      ::= exp_a ((op_comp) exp_a)*
exp_a    ::= exp_m (('+' | '-') exp_m)*
exp_m    ::= prim (('*' | '/') prim)*
prim     ::= num | ident | '(' exp ')' | chamada
chamada  ::= ident '(' params? ')'
params   ::= exp (',' exp)*
op_comp  ::= '<' | '>' | '<=' | '>=' | '==' | '!='
num      ::= digito digito*
ident    ::= letra (letra | digito)*
```

As chaves nos corpos do `if` e do `while` **não** são opcionais. Variáveis
globais agora precisam da palavra-chave `var`, e o corpo principal do
programa é marcado por `main` (em vez de estar solto, como na Cmd).

A atribuição **não cria** variáveis: qualquer variável usada no programa
precisa ser declarada antes (como global, com `var`, ou como parâmetro/local
de uma função). `return` não é um comando, e portanto não pode aparecer dentro
de um `if` ou de um `while`.

Para diferenciar uma referência a variável (`ident`) de uma chamada de função
(`ident '(' ... ')'`) em `prim`, o analisador olha um token além do
identificador: se vier `(`, é chamada; senão, é variável (seção 4 do guia).

### Funções

- O corpo de uma função tem zero ou mais declarações de variáveis locais
  (sempre no início, antes de qualquer comando), zero ou mais comandos, e uma
  expressão de resultado após `return`.
- Parâmetros são tratados como variáveis locais. Uma variável local (ou
  parâmetro) com o mesmo nome de uma variável global **esconde** a global
  dentro da função.
- Funções podem ser **diretamente recursivas** (chamar a si mesmas). As
  declarações são processadas sequencialmente, e uma função é inserida na
  tabela de símbolos global antes de seu próprio corpo ser verificado — isso
  permite a recursão direta. Funções **mutuamente** recursivas (uma chamando
  outra declarada depois dela) são rejeitadas; suportar esse caso é o
  exercício opcional citado na seção 5.1 do guia, não implementado aqui.

### Precedência

Três níveis, do mais baixo para o mais alto, todos associativos à esquerda:

| Nível          | Operadores                    | Associatividade |
|----------------|-------------------------------|-----------------|
| Comparação     | `<` `>` `<=` `>=` `==` `!=`   | esquerda        |
| Aditivo        | `+` `-`                       | esquerda        |
| Multiplicativo | `*` `/`                       | esquerda        |

Assim `1 + 2 < 4` agrupa como `(1 + 2) < 4`, e `7 + 5 * 3` como `7 + (5 * 3)`.
Parênteses continuam disponíveis para forçar outra ordem.

### Valores de verdade

A linguagem não tem um tipo booleano separado. Um valor igual a zero é
considerado falso, e qualquer valor diferente de zero é verdadeiro. Os
operadores de comparação produzem exatamente `1` ou `0`.

## Diferenças em relação ao guia

Como na Atividade 09, esta implementação mantém os desvios já adotados para
Cmd (operadores `<=`, `>=`, `!=`; braço `else` opcional) e não implementa o
exercício opcional de recursão mútua entre funções (seção 5.1 do guia). Fora
isso, a linguagem Fun segue o guia à risca: mesma gramática, mesma convenção
de chamada (parâmetros na pilha, `RBP` como frame pointer, retorno em `RAX`).

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

O modo `--ast` não apenas mostra a árvore: ele executa o programa (incluindo
chamadas de função, recursivas ou não), avaliando o `return`. Isso o torna uma
conferência independente do assembly gerado — se o valor impresso por `--ast`
e a saída do binário divergirem, há bug na geração de código. A suíte de
testes usa exatamente esse cruzamento.

## Erros

| Situação                                       | Saída                | Código de saída |
|-------------------------------------------------|----------------------|-----------------|
| Erro léxico (caractere inválido)                | mensagem em `stderr` | 2               |
| Erro sintático (programa malformado)            | mensagem em `stderr` | 3               |
| Erro semântico (variável/função)                | mensagem em `stderr` | 4               |

Erros semânticos cobrem: variável não declarada em expressão; atribuição a
variável não declarada; chamada a função não declarada; chamada com número de
parâmetros diferente do declarado; um nome de variável usado como se fosse
função (e vice-versa).

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

Variáveis globais são alocadas na seção `.bss` com `.lcomm var_nome, 8`.
Declarar e atribuir avaliam a expressão (resultado em `RAX`) e emitem
`mov %rax, var_nome`; usar uma variável emite `mov var_nome, %rax`. Variáveis
locais e parâmetros não usam `.bss` — ficam no registro de ativação da função,
na pilha (ver "Convenção de chamada" abaixo).

### Espaço de nomes dos símbolos

O montador tem um único espaço de nomes para tudo: variáveis, funções, rótulos
de salto e símbolos do `runtime.s` disputam o mesmo conjunto. Definir o mesmo
nome duas vezes é erro de montagem. Como o programador escolhe livremente os
nomes de variáveis e funções, os grupos precisam ser separados **por
construção**, e não por convenção:

| Origem | Forma | Por que não colide |
|--------|-------|--------------------|
| Variáveis globais | `var_nome` | o prefixo as afasta de `buffer` e `sair`, do runtime |
| Funções | `fun_nome` | mesmo raciocínio — afasta de símbolos do runtime e evita colisão com variáveis (`var_` vs. `fun_`) |
| Rótulos gerados | `.Lfim0`, `.Linicio0`, `.Lfalso0` | um identificador Fun tem que começar com letra, então nenhum programa produz um símbolo iniciado por `.` |

Sem isso, um programa que declarasse uma variável ou função chamada `Lfim0` ou
`buffer` geraria assembly que não monta. O prefixo `.L` tem ainda a vantagem de
ser reconhecido pelo GNU `as` como símbolo local, que não vai para a tabela de
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
modelos nunca colide, inclusive com laços aninhados. O contador é reiniciado
para cada função (e para o bloco `main`), já que cada uma usa sua própria
instância de `Gerador`.

### Convenção de chamada

Parâmetros e variáveis locais ficam na pilha do sistema, o que permite que
cada chamada (inclusive chamadas recursivas) tenha sua própria cópia. O valor
de retorno sempre volta em `RAX`.

**Na chamada** (`f(a1, ..., an)`):

1. Calcula e empilha o valor de cada parâmetro, na ordem **inversa** — do
   último para o primeiro. Isso faz o primeiro parâmetro ficar mais perto do
   topo da pilha logo após o `call`.
2. `call fun_f`.
3. Depois do `call`, soma `8*n` a `RSP` para descartar os parâmetros
   empilhados (quem chama limpa a pilha).

**No corpo da função**, com `L` variáveis locais:

```
fun_f:
    push %rbp              # salva o RBP do chamador
    sub $8*L, %rsp          # espaco para as L variaveis locais (se L > 0)
    mov %rsp, %rbp          # RBP = base do registro de ativacao desta chamada
    ...                     # locais, comandos e expressao de resultado
    add $8*L, %rsp          # desfaz o espaco das locais (se L > 0)
    pop %rbp                # restaura o RBP do chamador
    ret
```

Deslocamentos relativos a `RBP` (calculados em `codegen._offsets_locais`):

- Variável local de índice `i` (na ordem declarada): `8*i` — a primeira local
  fica em `0(%rbp)`, a segunda em `8(%rbp)`, etc.
- Parâmetro de índice `i` (na ordem declarada): `8*L + 16 + 8*i` — os 16 bytes
  extras são o `RBP` salvo e o endereço de retorno empilhados entre as locais
  e os parâmetros.

Por exemplo, para `fun f(x) { var y = ...; var z = ...; return y*z; }`
(`L = 2`, um parâmetro): `y` em `0(%rbp)`, `z` em `8(%rbp)`, `x` em
`32(%rbp)` (= `8*2 + 16 + 8*0`). O teste `tests/funcoes.t` confere esse
assembly linha a linha.

Como o acesso a locais e parâmetros usa `RBP` (que só muda no prólogo/epílogo
da própria função) em vez de `RSP` (que sobe e desce a cada `push`/`pop` de
uma expressão), os deslocamentos continuam válidos durante toda a execução do
corpo, mesmo com expressões aninhadas usando a pilha para valores
intermediários.

## Montar e executar

`compci/build.sh` automatiza compilação, montagem (`as`), ligação (`ld`) e
execução:

```
cd compci && bash build.sh tests/fun_fatorial.ci
```

Requer `runtime.s` no diretório de trabalho (o assembly gerado usa
`.include "runtime.s"`).

## Rodar os testes

A suíte usa [cram](https://bitheap.org/cram/) e cobre as quatro etapas, mais um
arquivo dedicado a funções:

- `compci/tests/lexer.t` — tokens, incluindo a distinção entre `=` e `==`, os
  operadores de dois caracteres (`<=`, `>=`, `!=`), a vírgula, as palavras-chave
  `var`/`main`/`fun` versus identificadores que começam com elas, e erros
  léxicos.
- `compci/tests/parser.t` — árvores de `if`/`else`, `if` sem `else`, `while` e
  atribuição, agora com `var` e `main`; precedência e associatividade dos três
  níveis; erros sintáticos.
- `compci/tests/semantic.t` — variável não declarada em expressão, dentro de
  `if` e de `while`, e atribuição a variável não declarada.
- `compci/tests/codegen.t` — assembly determinístico (comparação, `if`,
  `while`, seção `.bss`) e testes **end-to-end** que montam, linkam e executam
  o binário, conferindo o resultado numérico. Inclui `colisao_rotulo.ci` e
  `colisao_runtime.ci`, que declaram variáveis com os nomes dos rótulos gerados
  e dos símbolos do runtime — os casos que o esquema de prefixos existe para
  tornar impossíveis.
- `compci/tests/funcoes.t` — testes específicos da Atividade 10: função
  diretamente recursiva (`fun_fatorial.ci`, fatorial de 5), função sem
  parâmetros e sem locais chamada duas vezes (`fun_sem_param_sem_local.ci`),
  função com parâmetros e sem locais (`fun_param_sem_local.ci`), função com
  locais e sem parâmetros (`fun_local_sem_param.ci`), uma função chamando
  outra (`fun_chama_outra.ci`), o exemplo do guia com dois locais e um
  parâmetro (`fun_guia.ci`, conferindo os deslocamentos de pilha linha a
  linha), variável local escondendo uma global de mesmo nome
  (`fun_shadow.ci`), e os erros semânticos específicos de função (chamada não
  declarada, aridade errada, nome de variável usado como função e vice-versa,
  recursão mútua rejeitada).

Os programas de exemplo do guia de Cmd continuam incluídos e são executados de
ponta a ponta:

| Programa             | O que calcula                                   | Resultado |
|----------------------|-------------------------------------------------|-----------|
| `tests/delta.ci`     | valor absoluto do discriminante (a=1, b=2, c=3) | 8         |
| `tests/soma_loop.ci` | soma dos inteiros de 1 a 9                      | 45        |
| `tests/resto.ci`     | resto de 10 por 4, por subtração sucessiva      | 2         |
| `tests/mdc.ci`       | máximo divisor comum de 18 e 12                 | 6         |
| `tests/fun_fatorial.ci` | fatorial de 5, com função recursiva          | 120       |

Para cada um deles, o teste compara a saída do binário com o valor calculado
pelo interpretador (`--ast`), de modo que uma divergência aponta bug na geração
de código.

Os testes de geração de código precisam de `as`/`ld` (binutils); por isso a
forma recomendada de rodar a suíte completa é via Docker:

```
docker build -t compci compci/
docker run --rm compci    # roda lexer.t, parser.t, semantic.t, codegen.t e funcoes.t
```

Localmente, com binutils instalado:

```
pip install cram
cd compci && cram tests/lexer.t tests/parser.t tests/semantic.t tests/codegen.t tests/funcoes.t
```

Sem binutils, dá para rodar as etapas que não montam código:

```
cram compci/tests/lexer.t compci/tests/parser.t compci/tests/semantic.t
```
