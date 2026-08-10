# Compilador Fun

Compilador completo para a linguagem **Fun**, gerando assembly x86-64. Partiu
da Atividade 10 (funções) e, no **Projeto Final**, ganhou quatro extensões.

## Extensões implementadas no Projeto Final

O enunciado pede **uma extensão de complexidade média ou alta, ou pelo menos
três simples**. Este projeto entrega os dois critérios:

| Extensão | Complexidade | Seção do enunciado |
|----------|--------------|--------------------|
| **Arrays de inteiros** | média | 1.2 |
| **Operador de resto** `%` | simples | 1.1 (novos operadores aritméticos) |
| **Comando de impressão** `escreve` | simples | 1.1 (primitivas para imprimir valores) |
| **Operadores lógicos** `&&`, `\|\|`, `!` | simples | 1.1 (operadores lógicos) |

Os operadores de comparação `<=`, `>=` e `!=`, que também constam da lista de
extensões simples do enunciado, **já existiam** desde a Atividade 09 e por isso
não são contados aqui.

Além das extensões, foram corrigidos **quatro bugs pré-existentes** encontrados
durante o trabalho — ver [Bugs corrigidos](#bugs-corrigidos).

### Arrays de inteiros

```
var a[8];
var n = 8;
var i = 0;
var j = 0;
var tmp = 0;
main {
  i = 0;
  while i < n {
    a[i] = (n - i) * 3;
    i = i + 1;
  }
  i = 0;
  while i < n - 1 {
    j = 0;
    while j < n - 1 - i {
      if a[j] > a[j + 1] {
        tmp = a[j];
        a[j] = a[j + 1];
        a[j + 1] = tmp;
      }
      j = j + 1;
    }
    i = i + 1;
  }
  return a[0] * 100 + a[n - 1];
}
```

Bubble sort de 8 elementos, rodando como binário nativo. Os detalhes estão na
seção [Arrays](#arrays); o resumo é: declaração `var a[N];` com `N` constante,
leitura `a[exp]` como expressão primária, escrita `a[exp] = exp;` como comando,
verificação semântica de uso indevido, e alocação na seção `.bss` com acesso
por endereçamento indexado do x86-64.

### Operador de resto `%`

Mesma precedência de `*` e `/`, e o resto segue o sinal do **dividendo**
(resto truncado), como manda a instrução `idiv`. Detalhes em
[Resto](#resto).

| Expressão | Valor | Observação |
|-----------|-------|------------|
| `10 % 3` | `1` | |
| `7 + 10 % 3` | `8` | agrupa como `7 + (10 % 3)` |
| `(0 - 7) % 3` | `-1` | sinal do dividendo, como o `idiv` |

### Comando de impressão `escreve`

Antes desta extensão, um programa Fun produzia **exatamente um** número: o
valor do `return`. Agora pode imprimir quantos quiser, em qualquer ponto.
Detalhes em [Escreve](#escreve).

```
i = 1;
while i <= 5 {
  escreve i * i;
  i = i + 1;
}
```

### Operadores lógicos `&&`, `||`, `!`

Com **curto-circuito**: em `a && b`, se `a` for falso, `b` nunca é avaliado.
Dois níveis de precedência novos, abaixo das comparações. Detalhes em
[Operadores lógicos](#operadores-lógicos).

```
if x > 0 && a[x] != 0 {
  escreve a[x];
}
```

Se `x` não for positivo, `a[x]` nunca é lido — é o curto-circuito servindo de
guarda contra um índice inválido.

### Bugs corrigidos

Quatro bugs pré-existentes, todos encontrados por cruzamento entre o
interpretador e o binário, ou ao exercitar caminhos que nenhum teste cobria:

| Bug | Efeito | Onde |
|-----|--------|------|
| Função não enxergava variáveis globais | `--ast` falhava onde o binário funcionava | [Ambiente do interpretador](#ambiente-do-interpretador) |
| Ordem de avaliação divergente | interpretador e binário davam resultados diferentes com efeitos colaterais | [Ordem de avaliação](#ordem-de-avaliação) |
| `imprime_num` não contava o sinal `-` | números negativos saíam sem o `\n`, grudando linhas | [Escreve](#escreve) |
| `build.sh` não montava nem executava | o script prometia (no README) montar, linkar e rodar, mas só gerava o `.s` | [Montar e executar](#montar-e-executar) |

## A linguagem

A base é a linguagem Fun da Atividade 10, que estendeu a Cmd (Atividade 09) com
**funções**: declaração com a palavra-chave `fun`, parâmetros, variáveis locais,
chamada como expressão, recursão direta, e um bloco `main` que marca o programa
principal.

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
   Atividade 10 acrescentou o token de vírgula e as palavras-chave `fun`, `var`
   e `main`, e o Projeto Final acrescenta os colchetes `[` e `]`, o `%`, os
   operadores `&&`, `||` e `!`, e a palavra-chave `escreve`.
2. **Análise sintática** (`compci/parser.py`) — constrói a árvore de sintaxe
   abstrata (AST). Além dos nós de Cmd (`Const`, `Var`, `OpBin`, `Se`,
   `Enquanto`, `Atribuicao`, `Declaracao`) e dos de Fun (`FuncDecl` e
   `Chamada`), o Projeto Final acrescenta `DeclaracaoArray`, `IndiceArray`
   (leitura `a[i]`, uma expressão primária), `AtribuicaoArray` (escrita
   `a[i] = e;`, um comando), `OpLogico` (`&&` e `||`, com curto-circuito),
   `Nao` (`!`) e `Escreve`. `Programa.declaracoes` guarda `Declaracao`s,
   `DeclaracaoArray`s e `FuncDecl`s **na ordem em que aparecem no texto** —
   essa ordem importa para a análise semântica.
3. **Análise semântica** (`compci/semantic.py`) — verifica variáveis não
   declaradas, chamadas de função (se existe, se o nome não pertence a uma
   variável e vice-versa, e se a aridade bate) e, agora, usos indevidos de
   array. Mantém uma tabela global (variáveis, arrays e funções) e, ao entrar
   no corpo de uma função, uma tabela local (parâmetros e variáveis locais)
   que tem precedência sobre a global.
4. **Geração de código** (`compci/codegen.py`) — emite a seção `.bss`, saltos e
   rótulos, um rótulo/prólogo/epílogo por função usando a pilha do sistema para
   parâmetros e variáveis locais (convenção de chamada detalhada mais abaixo),
   o acesso indexado aos arrays, e os saltos de curto-circuito dos operadores
   lógicos.

## Gramática

Regras acrescentadas pelo Projeto Final estão marcadas com um comentário
indicando a extensão que as trouxe.

```
programa ::= decl* 'main' '{' cmd* 'return' exp ';' '}'
decl     ::= vardecl | arraydecl | fundecl
vardecl  ::= 'var' ident '=' exp ';'
arraydecl::= 'var' ident '[' num ']' ';'                  # array
fundecl  ::= 'fun' ident '(' arglist? ')'
             '{' vardecl* cmd* 'return' exp ';' '}'
arglist  ::= ident (',' ident)*
cmd      ::= se | enquanto | atrib | atrib_array | escreve
se       ::= 'if' exp bloco ('else' bloco)?
enquanto ::= 'while' exp bloco
bloco    ::= '{' cmd* '}'
atrib    ::= ident '=' exp ';'
atrib_array ::= ident '[' exp ']' '=' exp ';'             # array
escreve  ::= 'escreve' exp ';'                            # escreve
exp      ::= exp_ou
exp_ou   ::= exp_e ('||' exp_e)*                          # logicos
exp_e    ::= exp_c ('&&' exp_c)*                          # logicos
exp_c    ::= exp_a ((op_comp) exp_a)*
exp_a    ::= exp_m (('+' | '-') exp_m)*
exp_m    ::= prim (('*' | '/' | '%') prim)*               # % = resto
prim     ::= '!' prim                                     # logicos
           | num | ident | '(' exp ')' | chamada | indice
chamada  ::= ident '(' params? ')'
indice   ::= ident '[' exp ']'                            # array
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

Para diferenciar uma referência a variável (`ident`), uma chamada de função
(`ident '(' ... ')'`) e uma indexação (`ident '[' ... ']'`) em `prim`, o
analisador olha **um token além** do identificador: `(` é chamada, `[` é
indexação, qualquer outra coisa é variável (seção 4 do guia). O mesmo lookahead
de um token resolve os três casos, então a gramática continua LL(1) sobre o par
(identificador, token seguinte). A declaração `var a[10];` versus `var a = e;`
e o comando `a[i] = e;` versus `a = e;` usam exatamente o mesmo teste.

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

### Arrays

Extensão do Projeto Final. Um array é uma sequência de inteiros de 64 bits, de
tamanho fixo, no escopo global.

| Forma | O que é |
|-------|---------|
| `var a[10];` | declaração: tamanho constante, sem inicializador |
| `a[i] = 42;` | escrita (comando) |
| `x = a[i + 1];` | leitura (expressão primária) |

(A linguagem não tem sintaxe de comentário — `#` é erro léxico. Os `#` que
aparecem nos blocos de gramática e de assembly deste README são anotações da
documentação e do próprio assembly, não código Fun.)

- **O tamanho é uma constante inteira positiva**, conhecida em tempo de
  compilação — é o que permite reservar o espaço estaticamente na seção `.bss`.
  Não é uma expressão: `var a[n];` não é válido.
- **Não há inicializador.** Todos os elementos começam em zero, e isso sai de
  graça: a `.bss` já é entregue zerada pelo carregador, então nenhuma instrução
  de inicialização é emitida.
- **O índice é uma expressão qualquer** — `a[j + 1]`, `a[f(x)]`, `a[a[0]]`.
- Um array **não pode ser usado como valor escalar**: `return a;` e `a = 5;`
  são erros semânticos, com mensagem sugerindo a forma indexada.
- Um parâmetro ou variável local com o mesmo nome de um array global **esconde**
  o array dentro da função, exatamente como já acontecia com escalares.

#### Limitações (deliberadas)

Três coisas ficaram de fora, por decisão de escopo:

| Limitação | Motivo |
|-----------|--------|
| Arrays só no escopo global | O registro de ativação reserva 8 bytes por variável local (ver `codegen._offsets_locais`); um array local exigiria slots de tamanho variável. Rejeitado explicitamente, com mensagem própria, em vez de gerar deslocamentos errados |
| Array não pode ser parâmetro de função | Exigiria passagem por referência — o array viraria um endereço base. Funções acessam arrays **globais** normalmente, o que cobre a maior parte dos usos |
| Sem verificação de limites em tempo de execução | `a[100]` num array de 10 lê ou escreve memória fora do array, como em C. Uma checagem exigiria emitir comparação e salto a cada acesso |

O primeiro caso é detectado e reportado; os outros dois são o comportamento
esperado da linguagem, não erros silenciosos do compilador.

### Resto

O operador `%` tem a mesma precedência de `*` e `/` e é associativo à esquerda.
O resto segue o sinal do **dividendo** (resto truncado):

| Expressão | Valor |
|-----------|-------|
| `10 % 3` | `1` |
| `(0 - 7) % 3` | `-1` |
| `7 % (0 - 3)` | `1` |

Essa escolha não é arbitrária: é o que a instrução `idiv` faz, e o
interpretador precisa concordar com ela para continuar servindo de oráculo. O
`%` do Python segue o sinal do *divisor*, então o interpretador deriva o resto
do quociente truncado (`parser._div_trunc`) em vez de usar `%` diretamente —
mesmo cuidado que já existia para a divisão. A identidade
`a == a % b + a / b * b` vale para todos os sinais, e é testada em
`tests/op_resto_negativo.ci`.

### Escreve

`escreve exp;` avalia a expressão e imprime o valor seguido de nova linha.

É um **comando**, não uma função primitiva chamada como `escreve(x)`. O motivo
é gramatical: Fun não tem comando-expressão — uma chamada de função só aparece
dentro de uma expressão, e uma expressão solta não é um comando válido. Como
comando, `escreve` encaixa na gramática existente sem abrir esse buraco.

Antes desta extensão, um programa Fun produzia exatamente um número: o valor do
`return`. Isso limitava bastante o que dava para demonstrar — um algoritmo de
ordenação, por exemplo, só podia mostrar um elemento do resultado.

O `escreve` também tornou o cruzamento com o oráculo **mais forte**: um
programa agora produz várias linhas de saída, e o interpretador e o binário
precisam concordar em todas elas, não só no valor final.

### Operadores lógicos

`&&`, `||` (binários, com curto-circuito) e `!` (unário prefixo). Produzem
sempre `1` ou `0`, como as comparações, e qualquer valor diferente de zero
conta como verdadeiro — por isso `!!7` dá `1`.

**Curto-circuito** significa que o operando direito só é avaliado se o esquerdo
não decidir o resultado sozinho:

| Expressão | Avalia o direito? |
|-----------|-------------------|
| `0 && f()` | não — o resultado já é `0` |
| `1 \|\| f()` | não — o resultado já é `1` |
| `1 && f()` | sim |

Isso torna os operadores lógicos os únicos da linguagem em que o operando
**esquerdo** é avaliado primeiro. Todos os demais avaliam o direito primeiro
(ver [Ordem de avaliação](#ordem-de-avaliação)), porque o gerador os empilha; um
operando sob salto condicional não pode ser empilhado antes de se saber se ele
vai rodar. Interpretador e gerador seguem a mesma regra, e `tests/extensoes.t`
prova o curto-circuito nos dois com uma função que registra a ordem em que foi
chamada.

### Precedência

Cinco níveis, do mais baixo para o mais alto, todos associativos à esquerda:

| Nível          | Operadores                    | Associatividade |
|----------------|-------------------------------|-----------------|
| Ou lógico      | `\|\|`                        | esquerda        |
| E lógico       | `&&`                          | esquerda        |
| Comparação     | `<` `>` `<=` `>=` `==` `!=`   | esquerda        |
| Aditivo        | `+` `-`                       | esquerda        |
| Multiplicativo | `*` `/` `%`                   | esquerda        |

A negação `!` é **unária e prefixa**, e liga mais forte que todos eles — está
no nível de `prim`, então `!a == b` agrupa como `(!a) == b`.

Assim `1 + 2 < 4` agrupa como `(1 + 2) < 4`, `7 + 5 * 3` como `7 + (5 * 3)`,
`7 + 10 % 3` como `7 + (10 % 3)`, e `1 || 0 && 0` como `1 || (0 && 0)`.
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

### Ambiente do interpretador

Para o cruzamento acima valer, o interpretador precisa resolver nomes
**exatamente** como o gerador de código. A classe `Ambiente` (`parser.py`)
guarda dois escopos — `globais` e `locais` — e aplica a mesma regra que
`codegen._operando`: procura primeiro nos locais, cai nas globais se o nome não
for local. Cada chamada cria um `Ambiente` novo, com locais próprios mas
compartilhando as globais, do mesmo jeito que cada ativação ganha seu próprio
registro na pilha mas enxerga a mesma `.bss`.

Essa classe surgiu de um **bug real**, encontrado durante o Projeto Final e
presente desde a Atividade 10: `Chamada.avaliar` montava o ambiente da função
apenas com parâmetros e variáveis locais, sem as globais. O efeito é que uma
função lendo uma global funcionava no binário (o gerador sempre resolveu isso)
mas quebrava em `--ast`:

```
var g = 10;
fun f() { return g + 1; }
main { return f(); }
```

Antes: `--ast` → `erro na avaliacao: 'g'`, binário → `11`. Depois: ambos `11`.
O caso não era coberto por nenhum teste da suíte anterior — é justamente o tipo
de divergência que o oráculo existe para pegar, e que só apareceu quando um
programa de teste de array precisou ler um array global de dentro de uma
função. `tests/arrays.t` agora tem um caso de regressão para isso
(`fun_le_global.ci`).

### Ordem de avaliação

Corrigir o `Ambiente` **destapou uma segunda divergência**, da mesma família.
Com as globais finalmente visíveis e escrevíveis de dentro de uma função, uma
chamada passou a poder ter efeito colateral observável — e aí a *ordem* em que
os operandos são avaliados deixou de ser irrelevante:

```
var g = 1;
fun f() { g = 99; return 0; }
main { g = f() + g; return g; }
```

O gerador avalia o operando **direito primeiro** (gera a direita, empilha, gera
a esquerda — necessário para que subtração e divisão fiquem na ordem certa),
então lê `g` valendo 1 antes de `f()` alterá-la: resultado `1`. O interpretador
avaliava o esquerdo primeiro: resultado `99`. O mesmo valia para os argumentos
de uma chamada, que o gerador empilha em ordem inversa.

Ambos foram alinhados ao gerador (`OpBin.avaliar` e `Chamada.avaliar`). A
regra da linguagem, portanto, é: **operandos e argumentos são avaliados da
direita para a esquerda**. Isso não é uma escolha de design — é uma consequência
do esquema de pilha da geração de código, e o interpretador segue o gerador
porque é ele quem define a verdade. Testes de regressão em `tests/arrays.t`:
`fun_escreve_global.ci`, `array_func_escreve.ci`, `ordem_operandos.ci` e
`ordem_args.ci`.

## Erros

| Situação                                       | Saída                | Código de saída |
|-------------------------------------------------|----------------------|-----------------|
| Erro léxico (caractere inválido, `&` ou `\|` solto) | mensagem em `stderr` | 2           |
| Erro sintático (programa malformado)            | mensagem em `stderr` | 3               |
| Erro semântico (variável/função)                | mensagem em `stderr` | 4               |

Erros semânticos cobrem: variável não declarada em expressão; atribuição a
variável não declarada; chamada a função não declarada; chamada com número de
parâmetros diferente do declarado; um nome de variável usado como se fosse
função (e vice-versa); e os quatro casos de array — array usado como valor
escalar, atribuição a array sem índice, indexação de um escalar, e indexação de
array não declarado.

Dois erros de array são **sintáticos** (código 3), porque são detectados já na
forma do programa: array declarado dentro de uma função, e tamanho de array
menor ou igual a zero.

Com a chegada do `!` como operador de negação, um `!` solto **deixou de ser
erro léxico**: `return 1 ! 2;` agora falha no analisador sintático (código 3),
não mais no léxico. Em compensação, `&` e `|` sozinhos passaram a ser erros
léxicos, já que só existem nos pares `&&` e `||`.

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

### Arrays (geração de código)

Um array de `N` elementos é alocado na `.bss` com `.lcomm var_a, 8*N` — mesma
seção e mesmo prefixo das variáveis escalares, só que maior. Como a `.bss` já
vem zerada, não há código de inicialização.

O acesso aproveita o modo de endereçamento **base + índice escalado** do
x86-64, que calcula `base + indice*8` dentro da própria instrução:

```
    <codigo_indice>                 # indice em RAX
    mov var_a(,%rax,8), %rax        # leitura: a[i]
```

O `8` é o fator de escala (tamanho do elemento), então não é preciso emitir uma
multiplicação explícita nem gastar um registrador com o endereço calculado — o
esquema de dois registradores do resto do compilador continua valendo sem
nenhuma exceção.

Na escrita, o valor é gerado **primeiro** e empilhado, e só depois o índice:

```
    <codigo_valor>                  # valor em RAX
    push %rax
    <codigo_indice>                 # indice em RAX
    mov %rax, %rbx                  # indice para RBX
    pop %rax                        # valor de volta em RAX
    mov %rax, var_a(,%rbx,8)        # escrita: a[i] = valor
```

É a mesma ordem das operações binárias, e pelo mesmo motivo: a expressão do
índice pode ser arbitrariamente complexa e usar `RAX`, `RBX` e a pilha à
vontade, então o valor a ser gravado precisa estar protegido na pilha enquanto
ela é avaliada. O interpretador replica essa ordem (`AtribuicaoArray.executar`)
para que os dois concordem mesmo com efeitos colaterais no índice.

Um exemplo completo, de `tests/array_simples.ci`:

```
    .section .bss
    .lcomm var_a, 24          # 3 elementos x 8 bytes
    ...
    mov $7, %rax              # a[1] = 7
    push %rax
    mov $1, %rax
    mov %rax, %rbx
    pop %rax
    mov %rax, var_a(,%rbx,8)
    mov $1, %rax              # return a[1]
    mov var_a(,%rax,8), %rax
```

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
execução. **Correção do Projeto Final:** o script prometia isso no README mas
só rodava o compilador, gerando o `.s` e parando ali — agora ele de fato monta,
linka e executa:

```
cd compci && bash build.sh tests/fun_fatorial.ci
```

Requer `runtime.s` no diretório de trabalho (o assembly gerado usa
`.include "runtime.s"`).

## Rodar os testes

A suíte usa [cram](https://bitheap.org/cram/) e cobre as quatro etapas, mais um
arquivo dedicado a funções:

- `compci/tests/lexer.t` — tokens, incluindo a distinção entre `=` e `==` e
  entre `!=` e `!`, os operadores de dois caracteres (`<=`, `>=`, `!=`, `&&`,
  `||`), a vírgula, os colchetes, o `%`, as palavras-chave
  `var`/`main`/`fun`/`escreve` versus identificadores que começam com elas, e
  erros léxicos (caractere inválido, `&` e `|` soltos).
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
- `compci/tests/arrays.t` — testes do Projeto Final: assembly determinístico da
  alocação `.lcomm var_a, 24` e das duas formas de acesso indexado; bubble sort
  de 8 elementos end-to-end (`array_bubble.ci`); índice como expressão
  aritmética (`array_indice_exp.ci`); array global lido de dentro de uma função
  (`array_em_funcao.ci`); parâmetro escondendo um array global
  (`array_param_shadow.ci`); a regressão do interpretador
  (`fun_le_global.ci`); os seis erros de array (quatro semânticos, dois
  sintáticos); e as regressões de ordem de avaliação (`fun_escreve_global.ci`,
  `array_func_escreve.ci`, `ordem_operandos.ci`, `ordem_args.ci`).
- `compci/tests/extensoes.t` — testes das três extensões simples: `%` com
  operandos positivos e negativos e a identidade `a == a%b + a/b*b`
  (`op_resto.ci`, `op_resto_negativo.ci`); `escreve` dentro de laço e com
  negativo, que é o caso da correção do `runtime.s` (`escreve_loop.ci`);
  tabela-verdade completa de `&&`, `||` e `!` (`logicos_tabela.ci`); prova de
  curto-circuito nos dois lados via função que registra a ordem das chamadas
  (`logicos_curto.ci`); precedência dos cinco níveis (`logicos_precedencia.ci`);
  o assembly do resto e do curto-circuito; e as três extensões trabalhando
  junto com os arrays (`array_bubble_escreve.ci`).

  Neste arquivo o cruzamento com o oráculo é mais forte: com `escreve`, um
  programa produz várias linhas, e interpretador e binário precisam concordar em
  todas — não só no valor final.

Os programas de exemplo do guia de Cmd continuam incluídos e são executados de
ponta a ponta:

| Programa             | O que calcula                                   | Resultado |
|----------------------|-------------------------------------------------|-----------|
| `tests/delta.ci`     | valor absoluto do discriminante (a=1, b=2, c=3) | 8         |
| `tests/soma_loop.ci` | soma dos inteiros de 1 a 9                      | 45        |
| `tests/resto.ci`     | resto de 10 por 4, por subtração sucessiva      | 2         |
| `tests/mdc.ci`       | máximo divisor comum de 18 e 12                 | 6         |
| `tests/fun_fatorial.ci` | fatorial de 5, com função recursiva          | 120       |
| `tests/array_bubble.ci` | bubble sort de 8 elementos (menor*100+maior) | 324       |
| `tests/array_bubble_escreve.ci` | bubble sort imprimindo o vetor antes e depois | 9 |

Para cada um deles, o teste compara a saída do binário com o valor calculado
pelo interpretador (`--ast`), de modo que uma divergência aponta bug na geração
de código.

Os testes de geração de código precisam de `as`/`ld` (binutils); por isso a
forma recomendada de rodar a suíte completa é via Docker:

```
docker build -t compci compci/
docker run --rm compci    # roda os 7 arquivos de teste
```

Localmente, com binutils instalado:

```
pip install cram
cd compci && cram tests/*.t
```

Sem binutils, dá para rodar as etapas que não montam código:

```
cram compci/tests/lexer.t compci/tests/parser.t compci/tests/semantic.t
```
