Testes de funcoes da linguagem Fun (Atividade 10).

Os testes end-to-end montam (as), linkam (ld) e executam o binario, conferindo
a saida numerica contra o oraculo do interpretador (`--ast`), igual ao que
`codegen.t` ja faz para a linguagem Cmd. Rodam dentro do diretorio temporario
do cram, para onde o runtime.s e copiado.

Copia o runtime para o diretorio de trabalho do teste:

  $ cp "$TESTDIR/../runtime.s" .

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

Funcao recursiva direta — fatorial de 5, calculado chamando `fat` dentro do
seu proprio corpo (secao 5.1 do guia permite recursao direta):

  $ roda "$TESTDIR/fun_fatorial.ci"
  120

  $ interpreta "$TESTDIR/fun_fatorial.ci"
  valor: 120

Funcao sem parametros e sem variaveis locais, chamada duas vezes:

  $ roda "$TESTDIR/fun_sem_param_sem_local.ci"
  14

  $ interpreta "$TESTDIR/fun_sem_param_sem_local.ci"
  valor: 14

Funcao com parametros e sem variaveis locais:

  $ roda "$TESTDIR/fun_param_sem_local.ci"
  6

  $ interpreta "$TESTDIR/fun_param_sem_local.ci"
  valor: 6

Funcao com variaveis locais e sem parametros:

  $ roda "$TESTDIR/fun_local_sem_param.ci"
  37

  $ interpreta "$TESTDIR/fun_local_sem_param.ci"
  valor: 37

Uma funcao chamando outra (nao recursiva):

  $ roda "$TESTDIR/fun_chama_outra.ci"
  20

  $ interpreta "$TESTDIR/fun_chama_outra.ci"
  valor: 20

Exemplo do guia (secao 6.1.4): funcao com um parametro e duas variaveis
locais, chamada com o parametro constante 42 — usado tambem para conferir os
deslocamentos de pilha (`0(%rbp)`/`8(%rbp)` para as duas locais `y`/`z`, e
`32(%rbp)` para o parametro `x`, ja que L=2 e o offset do parametro e
`8*L + 16 + 8*indice` = `8*2 + 16 + 0`):

  $ roda "$TESTDIR/fun_guia.ci"
  131714583

  $ interpreta "$TESTDIR/fun_guia.ci"
  valor: 131714583

  $ python3 "$TESTDIR/../compci.py" --stdout "$TESTDIR/fun_guia.ci" | sed -n '/^fun_f:/,/^    ret$/p'
  fun_f:
      push %rbp
      sub $16, %rsp
      mov %rsp, %rbp
      mov $7, %rax
      push %rax
      mov 32(%rbp), %rax
      push %rax
      mov 32(%rbp), %rax
      pop %rbx
      imul %rbx, %rax
      pop %rbx
      add %rbx, %rax
      mov %rax, 0(%rbp)
      mov $9, %rax
      push %rax
      mov 32(%rbp), %rax
      push %rax
      mov 0(%rbp), %rax
      pop %rbx
      imul %rbx, %rax
      pop %rbx
      sub %rbx, %rax
      mov %rax, 8(%rbp)
      mov 8(%rbp), %rax
      push %rax
      mov 0(%rbp), %rax
      pop %rbx
      imul %rbx, %rax
      add $16, %rsp
      pop %rbp
      ret

Variavel local (ou parametro) esconde uma global de mesmo nome — a global `x`
vale 100, mas dentro de `f` o parametro `x` e usado; o resultado e
`f(1) + x = 2 + 100`:

  $ roda "$TESTDIR/fun_shadow.ci"
  102

  $ interpreta "$TESTDIR/fun_shadow.ci"
  valor: 102

Chamada a funcao nao declarada:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/sem_fun_nao_decl.ci" 2>&1
  Erro semantico: funcao 'naoexiste' nao declarada
  [4]

Chamada com numero errado de parametros:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/sem_fun_aridade.ci" 2>&1
  Erro semantico: funcao 'f' espera 2 parametro(s), recebeu 1
  [4]

Uma variavel global usada como se fosse uma funcao:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/sem_fun_var_nao_e_funcao.ci" 2>&1
  Erro semantico: 'f' nao e uma funcao
  [4]

Um nome de funcao usado como se fosse uma variavel (sem parenteses, isso nao e
uma chamada — precisa ser uma variavel declarada, e funcoes nao sao):

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/sem_fun_como_var.ci" 2>&1
  Erro semantico: variavel 'g' nao declarada
  [4]

Funcoes mutuamente recursivas sao rejeitadas: as declaracoes sao processadas
sequencialmente, entao `par` nao pode chamar `impar` (declarada depois).
Suportar isso fica como exercicio opcional (secao 5.1 do guia):

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/sem_fun_mutua_rejeitada.ci" 2>&1
  Erro semantico: funcao 'impar' nao declarada
  [4]
