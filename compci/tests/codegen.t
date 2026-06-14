Gerador de codigo EC1 (Atividade 06).

Os testes end-to-end montam (as), linkam (ld) e executam o binario, conferindo
a saida numerica. Rodam dentro do diretorio temporario do cram, para onde o
runtime.s e copiado (o assembly gerado usa .include "runtime.s").

Copia o runtime para o diretorio de trabalho do teste:

  $ cp "$TESTDIR/../runtime.s" .

Assembly deterministico para (7 + 11) — esquema de pilha, operando direito
primeiro:

  $ python3 "$TESTDIR/../compci.py" --stdout "$TESTDIR/soma.ci"
      #
      # codigo gerado pelo compilador EC1
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

Funcao auxiliar: compila, monta, linka e executa um programa .ci.

  $ roda() {
  >   python3 "$TESTDIR/../compci.py" --stdout "$1" > prog.s
  >   as --64 -o prog.o prog.s
  >   ld -o prog prog.o
  >   ./prog
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
