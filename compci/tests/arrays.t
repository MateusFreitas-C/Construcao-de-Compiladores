Arrays de inteiros (Projeto Final).

Arrays sao globais, de tamanho constante conhecido em tempo de compilacao, e
ficam na secao .bss — que o carregador ja entrega zerada, entao nao ha codigo
de inicializacao. A leitura e a escrita usam o modo de enderecamento base +
indice escalado do x86-64, `var_a(,%reg,8)`, que resolve o calculo do endereco
em uma unica instrucao.

Os testes end-to-end montam (as), linkam (ld) e executam o binario, conferindo
a saida contra o oraculo do interpretador (`--ast`), igual a codegen.t e
funcoes.t.

Copia o runtime para o diretorio de trabalho do teste:

  $ cp "$TESTDIR/../runtime.s" .

  $ roda() {
  >   python3 "$TESTDIR/../compci.py" --stdout "$1" > prog.s
  >   as --64 -o prog.o prog.s
  >   ld -o prog prog.o
  >   ./prog
  > }

  $ interpreta() {
  >   python3 "$TESTDIR/../compci.py" --ast "$1" | tail -1
  > }

Assembly deterministico. Note `.lcomm var_a, 24` (3 elementos de 8 bytes) e as
duas formas de acesso. Na escrita o valor e gerado primeiro e empilhado, e so
depois o indice — mesma ordem das operacoes binarias, para que uma expressao
de indice complexa nao destrua o valor a ser gravado:

  $ python3 "$TESTDIR/../compci.py" --stdout "$TESTDIR/array_simples.ci"
      .section .bss
      .lcomm var_a, 24
  
      #
      # codigo gerado pelo compilador Fun
      #
      .section .text
      .globl _start
  _start:
      mov $7, %rax
      push %rax
      mov $1, %rax
      mov %rax, %rbx
      pop %rax
      mov %rax, var_a(,%rbx,8)
      mov $1, %rax
      mov var_a(,%rax,8), %rax
      call imprime_num
      call sair
  
      .include "runtime.s"



Arvore sintatica: a declaracao de array aparece sem inicializador, e a
indexacao e uma primaria como qualquer outra:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/array_simples.ci"
  arvore:
  var a[3];
  main {
    a[1] = 7;
    return a[1];
  }
  valor: 7

Bubble sort de 8 elementos preenchidos em ordem decrescente. Exercita
indexacao com expressao (`a[j + 1]`), escrita e leitura dentro de lacos
aninhados. Retorna o menor elemento vezes 100 mais o maior — 3 e 24 apos a
ordenacao:

  $ roda "$TESTDIR/array_bubble.ci"
  324

  $ interpreta "$TESTDIR/array_bubble.ci"
  valor: 324

Indice sendo uma expressao aritmetica arbitraria, nos dois lados:

  $ roda "$TESTDIR/array_indice_exp.ci"
  99

  $ interpreta "$TESTDIR/array_indice_exp.ci"
  valor: 99

Array global lido de dentro de uma funcao (soma dos 4 elementos):

  $ roda "$TESTDIR/array_em_funcao.ci"
  100

  $ interpreta "$TESTDIR/array_em_funcao.ci"
  valor: 100

Um parametro de funcao com o mesmo nome de um array global esconde o array
dentro da funcao, exatamente como ja acontecia com variaveis escalares. Aqui
`f(a)` usa o parametro como inteiro, enquanto o `main` continua indexando o
array global: f(7) + a[0] = 8 + 5:

  $ roda "$TESTDIR/array_param_shadow.ci"
  13

  $ interpreta "$TESTDIR/array_param_shadow.ci"
  valor: 13

Regressao do interpretador: uma funcao lendo uma variavel global escalar. O
gerador de codigo sempre resolveu isso (`codegen._operando` cai no simbolo
global quando o nome nao e local), mas o interpretador montava o ambiente da
funcao apenas com parametros e locais, e falhava. Como o interpretador e o
oraculo dos testes end-to-end, os dois precisam concordar:

  $ roda "$TESTDIR/fun_le_global.ci"
  11

  $ interpreta "$TESTDIR/fun_le_global.ci"
  valor: 11

Erros semanticos. Usar um array como valor escalar, sem indice:

  $ python3 "$TESTDIR/../compci.py" --stdout "$TESTDIR/sem_array_como_valor.ci"
  Erro semantico: 'a' e um array e nao pode ser usado como valor; use um indice, como 'a[i]'
  [4]

Atribuir a um array inteiro, sem indice:

  $ python3 "$TESTDIR/../compci.py" --stdout "$TESTDIR/sem_array_atrib_sem_indice.ci"
  Erro semantico: 'a' e um array; atribuicao exige um indice, como 'a[i] = ...'
  [4]

Indexar uma variavel escalar:

  $ python3 "$TESTDIR/../compci.py" --stdout "$TESTDIR/sem_array_escalar_indexado.ci"
  Erro semantico: 'x' nao e um array
  [4]

Indexar um array nao declarado:

  $ python3 "$TESTDIR/../compci.py" --stdout "$TESTDIR/sem_array_nao_decl.ci"
  Erro semantico: array 'b' nao declarado
  [4]

Erros sintaticos. Array local a uma funcao nao e suportado: o registro de
ativacao reserva 8 bytes por variavel local, entao um array local exigiria
slots de tamanho variavel. A rejeicao e explicita, com mensagem propria, em
vez de gerar deslocamentos de pilha errados:

  $ python3 "$TESTDIR/../compci.py" --stdout "$TESTDIR/erro_array_local.ci"
  Erro sintatico na posicao 12: array 'v' local a funcao nao suportado; arrays devem ser declarados no escopo global
  [3]

Tamanho de array precisa ser positivo:

  $ python3 "$TESTDIR/../compci.py" --stdout "$TESTDIR/erro_array_tamanho.ci"
  Erro sintatico na posicao 6: tamanho de array deve ser positivo, encontrado 0
  [3]

Uma funcao escrevendo numa variavel global. O gerador emite `mov %rax,
var_g`, alterando a global de verdade; o interpretador precisa fazer o mesmo,
e nao criar um local silenciosamente:

  $ roda "$TESTDIR/fun_escreve_global.ci"
  1

  $ interpreta "$TESTDIR/fun_escreve_global.ci"
  valor: 1

Uma funcao escrevendo em elementos de um array global:

  $ roda "$TESTDIR/array_func_escreve.ci"
  56

  $ interpreta "$TESTDIR/array_func_escreve.ci"
  valor: 56

Ordem de avaliacao dos operandos de uma operacao binaria. O gerador avalia o
operando DIREITO primeiro (gera a direita, empilha, gera a esquerda), entao o
interpretador tambem precisa. `reg` registra em `s` a ordem em que foi
chamada: 21 significa que reg(2) rodou antes de reg(1):

  $ roda "$TESTDIR/ordem_operandos.ci"
  21

  $ interpreta "$TESTDIR/ordem_operandos.ci"
  valor: 21

Ordem de avaliacao dos argumentos de uma chamada. O gerador os empilha em
ordem inversa, entao os efeitos colaterais acontecem da direita para a
esquerda — mesma leitura de `s`:

  $ roda "$TESTDIR/ordem_args.ci"
  21

  $ interpreta "$TESTDIR/ordem_args.ci"
  valor: 21
