Extensoes simples do Projeto Final: operador de resto (%), comando de
impressao (escreve) e operadores logicos (&&, ||, !) com curto-circuito.

Como em codegen.t, funcoes.t e arrays.t, os testes end-to-end montam, linkam e
executam o binario, e o resultado e cruzado com o interpretador (`--ast`).
Aqui o cruzamento e mais forte que nos outros arquivos: com `escreve`, um
programa produz varias linhas de saida, e as duas implementacoes tem que
concordar em todas elas — nao so no valor final.

  $ cp "$TESTDIR/../runtime.s" .

  $ roda() {
  >   python3 "$TESTDIR/../compci.py" --stdout "$1" > prog.s
  >   as --64 -o prog.o prog.s
  >   ld -o prog prog.o
  >   ./prog
  > }

`interpreta` descarta a arvore impressa por --ast e mostra so o que o programa
escreveu, para comparar linha a linha com o binario:

  $ interpreta() {
  >   python3 "$TESTDIR/../compci.py" --ast "$1" \
  >     | sed -n '/^valor:/q;p' | tac | sed -n '/^}$/q;p' | tac
  > }

Operador de resto. A precedencia e a mesma da multiplicacao e da divisao, e
`7 + 10 % 3` agrupa como `7 + (10 % 3)`:

  $ roda "$TESTDIR/op_resto.ci"
  1
  2
  0
  8
  2

Resto com operando negativo. O `idiv` deixa em RDX um resto com o sinal do
DIVIDENDO (resto truncado), enquanto o `%` do Python segue o sinal do divisor
— o interpretador deriva o resto do quociente truncado para concordar com o
assembly. A terceira linha confere a identidade `a == a%b + a/b*b`:

  $ roda "$TESTDIR/op_resto_negativo.ci"
  -2
  -1
  -7
  0

  $ interpreta "$TESTDIR/op_resto_negativo.ci"
  -2
  -1
  -7

Assembly do resto: a mesma instrucao idiv produz quociente em RAX e resto em
RDX, entao o resto sai de graca — basta ler o outro registrador:

  $ python3 "$TESTDIR/../compci.py" --stdout "$TESTDIR/op_resto.ci" | grep -A3 'cqo' | head -4
      cqo
      idiv %rbx
      mov %rdx, %rax
      call imprime_num

Comando escreve dentro de um laco, terminando com um negativo. O valor
negativo tambem exercita a correcao do runtime.s: ao escrever o sinal '-', o
contador de tamanho da string precisa ser incrementado, senao o write sai um
byte curto e engole o '\n' final, grudando duas linhas:

  $ roda "$TESTDIR/escreve_loop.ci"
  1
  4
  9
  16
  25
  -42
  0

  $ interpreta "$TESTDIR/escreve_loop.ci"
  1
  4
  9
  16
  25
  -42

Tabela-verdade completa de && , || e !. Os operadores produzem sempre 1 ou 0,
como as comparacoes, e qualquer valor diferente de zero conta como verdadeiro
(por isso `!!7` da 1):

  $ roda "$TESTDIR/logicos_tabela.ci"
  1
  0
  0
  0
  1
  1
  1
  0
  1
  0
  1
  0

  $ interpreta "$TESTDIR/logicos_tabela.ci"
  1
  0
  0
  0
  1
  1
  1
  0
  1
  0
  1

Curto-circuito. `marca(v)` registra em `s` a ordem das chamadas, entao o valor
de `s` revela quais operandos foram realmente avaliados:

`marca(0) && marca(1)` da 0 (o esquerdo e falso, o direito nao roda);
`marca(9) || marca(1)` da 9 (o esquerdo e verdadeiro, o direito nao roda);
`marca(1) && marca(2)` da 12 (os dois rodam).

  $ roda "$TESTDIR/logicos_curto.ci"
  0
  9
  12
  0

  $ interpreta "$TESTDIR/logicos_curto.ci"
  0
  9
  12

Precedencia dos cinco niveis. `1 || 0 && 0` agrupa como `1 || (0 && 0)`, e as
comparacoes ligam mais forte que os logicos:

  $ roda "$TESTDIR/logicos_precedencia.ci"
  1
  1
  1
  1
  0

  $ interpreta "$TESTDIR/logicos_precedencia.ci"
  1
  1
  1
  1

Arvore sintatica mostrando a associatividade e a precedencia dos logicos:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/logicos_precedencia.ci" | head -6
  arvore:
  main {
    escreve (1 || (0 && 0));
    escreve ((2 > 1) && (3 > 2));
    escreve ((!1) || (5 > 3));
    escreve (((1 + 1) == 2) && ((6 % 4) == 2));

Assembly do curto-circuito de `&&`: o operando esquerdo e gerado primeiro
(ao contrario das operacoes binarias, que geram o direito primeiro), e o
codigo do direito fica sob um salto condicional:

  $ printf 'main {\n  return 1 && 0;\n}\n' > curto.ci

  $ python3 "$TESTDIR/../compci.py" --stdout curto.ci | sed -n '/_start:/,/call imprime/p'
  _start:
      mov $1, %rax
      cmp $0, %rax
      jz .Lcurto0
      mov $0, %rax
      cmp $0, %rax
      jz .Lcurto0
      mov $1, %rax
      jmp .Lfim0
  .Lcurto0:
      mov $0, %rax
  .Lfim0:
      call imprime_num

As tres extensoes trabalhando juntas com os arrays: preenche com `%`, imprime
o vetor desordenado, ordena com bubble sort e imprime de novo. As linhas -1 e
-2 sao apenas separadores (a linguagem nao tem strings):

  $ roda "$TESTDIR/array_bubble_escreve.ci"
  -1
  11
  48
  35
  22
  9
  46
  33
  20
  -2
  9
  11
  20
  22
  33
  35
  46
  48
  9
