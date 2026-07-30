Gerador de codigo Fun (Atividade 10).

Os testes end-to-end montam (as), linkam (ld) e executam o binario, conferindo
a saida numerica. Rodam dentro do diretorio temporario do cram, para onde o
runtime.s e copiado (o assembly gerado usa .include "runtime.s").

Copia o runtime para o diretorio de trabalho do teste:

  $ cp "$TESTDIR/../runtime.s" .

Assembly deterministico para (7 + 11) — esquema de pilha, operando direito
primeiro:

  $ python3 "$TESTDIR/../compci.py" --stdout "$TESTDIR/soma.ci"
      #
      # codigo gerado pelo compilador Fun
      #
      .section .text
      .globl _start
  _start:
      mov $11, %rax
      push %rax
      mov $7, %rax
      pop %rbx
      add %rbx, %rax
      call imprime_num
      call sair
  
      .include "runtime.s"

Assembly deterministico de uma comparacao — note o `xor` ANTES do `cmp` (ele
limpa ZF/SF/OF, entao inverter a ordem destruiria os flags que o SETcc le) e o
uso de %cl porque SETcc so escreve 8 bits:

  $ python3 "$TESTDIR/../compci.py" --stdout "$TESTDIR/prec_comparacao.ci"
      #
      # codigo gerado pelo compilador Fun
      #
      .section .text
      .globl _start
  _start:
      mov $4, %rax
      push %rax
      mov $2, %rax
      push %rax
      mov $1, %rax
      pop %rbx
      add %rbx, %rax
      pop %rbx
      xor %rcx, %rcx
      cmp %rbx, %rax
      setl %cl
      mov %rcx, %rax
      call imprime_num
      call sair
  
      .include "runtime.s"

Assembly deterministico do comando de repeticao — rotulos na coluna zero,
`.Linicio0` no topo e `.Lfim0` na saida. Variaveis levam o prefixo `var_` e
rotulos o prefixo `.L`, de modo que os dois conjuntos de nomes nao podem se
encontrar (ver o teste de colisao mais abaixo):

  $ python3 "$TESTDIR/../compci.py" --stdout "$TESTDIR/while_simples.ci" | sed -n '/_start:/,/call imprime_num/p'
  _start:
      mov $1, %rax
      mov %rax, var_n
      mov $10, %rax
      mov %rax, var_m
      mov $0, %rax
      mov %rax, var_soma
  .Linicio0:
      mov var_m, %rax
      push %rax
      mov var_n, %rax
      pop %rbx
      xor %rcx, %rcx
      cmp %rbx, %rax
      setl %cl
      mov %rcx, %rax
      cmp $0, %rax
      jz .Lfim0
      mov var_n, %rax
      push %rax
      mov var_soma, %rax
      pop %rbx
      add %rbx, %rax
      mov %rax, var_soma
      mov $1, %rax
      push %rax
      mov var_n, %rax
      pop %rbx
      add %rbx, %rax
      mov %rax, var_n
      jmp .Linicio0
  .Lfim0:
      mov var_soma, %rax
      call imprime_num

Secao .bss com as variaveis declaradas, em ordem alfabetica:

  $ python3 "$TESTDIR/../compci.py" --stdout "$TESTDIR/while_simples.ci" | head -4
      .section .bss
      .lcomm var_m, 8
      .lcomm var_n, 8
      .lcomm var_soma, 8

Assembly deterministico do condicional sem `else` — os dois rotulos continuam
sendo emitidos, com o braco falso vazio:

  $ python3 "$TESTDIR/../compci.py" --stdout "$TESTDIR/if_sem_else.ci" | sed -n '/jz \.Lfalso/,/^\.Lfim0:/p'
      jz .Lfalso0
      mov var_delta, %rax
      push %rax
      mov $0, %rax
      pop %rbx
      sub %rbx, %rax
      mov %rax, var_delta
      jmp .Lfim0
  .Lfalso0:
  .Lfim0:

Funcao auxiliar: compila, monta, linka e executa um programa .ci.

  $ roda() {
  >   python3 "$TESTDIR/../compci.py" --stdout "$1" > prog.s
  >   as --64 -o prog.o prog.s
  >   ld -o prog prog.o
  >   ./prog
  > }

Funcao auxiliar: imprime so o valor calculado pelo interpretador, para cruzar
com o resultado do binario.

  $ interpreta() {
  >   python3 "$TESTDIR/../compci.py" --ast "$1" | tail -1
  > }

Literal isolado:

  $ roda "$TESTDIR/literal.ci"
  333

Soma:

  $ roda "$TESTDIR/soma.ci"
  18

Multiplicacao:

  $ roda "$TESTDIR/mult.ci"
  42

Subtracao — valida a ordem dos operandos (11 - 7, nao 7 - 11):

  $ roda "$TESTDIR/sub.ci"
  4

Divisao — valida a ordem dos operandos (20 / 4, nao 4 / 20):

  $ roda "$TESTDIR/div.ci"
  5

Expressao do exemplo do PDF:

  $ roda "$TESTDIR/ok.ci"
  10065

Expressao aninhada com as quatro operacoes:

  $ roda "$TESTDIR/complexo.ci"
  2657

Precedencia sem parenteses — multiplicacao antes da soma:

  $ roda "$TESTDIR/precedencia.ci"
  22

Associatividade a esquerda — subtracao encadeada:

  $ roda "$TESTDIR/assoc_sub.ci"
  0

Associatividade a esquerda — divisao encadeada:

  $ roda "$TESTDIR/assoc_div.ci"
  10

Expressao sem parenteses com as quatro operacoes:

  $ roda "$TESTDIR/sem_parenteses.ci"
  11

Parenteses ainda funcionam para forcar outra ordem:

  $ roda "$TESTDIR/parenteses_opcionais.ci"
  36

Programa com variaveis:

  $ roda "$TESTDIR/test_vars.ci"
  60467

Comparacao produz 1 para verdadeiro:

  $ roda "$TESTDIR/prec_comparacao.ci"
  1

Os seis operadores de comparacao, verdadeiros e falsos:

  $ roda "$TESTDIR/comparadores.ci"
  6

  $ interpreta "$TESTDIR/comparadores.ci"
  valor: 6

Exemplo do guia — valor absoluto do discriminante (a=1, b=2, c=3):

  $ roda "$TESTDIR/delta.ci"
  8

  $ interpreta "$TESTDIR/delta.ci"
  valor: 8

O mesmo programa com a extensao de `if` sem `else`:

  $ roda "$TESTDIR/if_sem_else.ci"
  8

Exemplo do guia — soma dos inteiros de 1 a 9:

  $ roda "$TESTDIR/soma_loop.ci"
  45

  $ interpreta "$TESTDIR/soma_loop.ci"
  valor: 45

Exemplo do guia — resto de 10 por 4:

  $ roda "$TESTDIR/resto.ci"
  2

  $ interpreta "$TESTDIR/resto.ci"
  valor: 2

Exemplo do guia — mdc de 18 e 12, com while aninhado:

  $ roda "$TESTDIR/mdc.ci"
  6

  $ interpreta "$TESTDIR/mdc.ci"
  valor: 6

Lacos aninhados — rotulos distintos por construcao, sem colisao:

  $ roda "$TESTDIR/while_aninhado.ci"
  18

  $ interpreta "$TESTDIR/while_aninhado.ci"
  valor: 18

Variaveis com o mesmo nome dos rotulos gerados. `Lfim0` e `Linicio0` sao
identificadores Cmd validos; sem o prefixo `.L` nos rotulos, o montador veria
duas definicoes do mesmo simbolo e recusaria o arquivo:

  $ roda "$TESTDIR/colisao_rotulo.ci"
  3

  $ interpreta "$TESTDIR/colisao_rotulo.ci"
  valor: 3

Variaveis com o mesmo nome dos simbolos do runtime.s. `buffer` e `sair` sao os
unicos simbolos do runtime alcancaveis por um identificador Cmd — os demais
(`imprime_num`, `mark_neg`, `printzero_L0`) tem underscore, que a gramatica de
identificadores nao aceita. Sem o prefixo `var_` nas variaveis, o montador
recusaria o arquivo ao processar o .include:

  $ roda "$TESTDIR/colisao_runtime.ci"
  8

  $ interpreta "$TESTDIR/colisao_runtime.ci"
  valor: 8
