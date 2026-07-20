Analisador lexico EC1 — programa OK do exemplo do PDF:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/ok.ci"
  <Igual, "=", 0>
  <ParenEsq, "(", 2>
  <Numero, "33", 3>
  <Soma, "+", 6>
  <ParenEsq, "(", 8>
  <Numero, "912", 9>
  <Mult, "*", 13>
  <Numero, "11", 15>
  <ParenDir, ")", 17>
  <ParenDir, ")", 18>

Literal isolado:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/literal.ci"
  <Igual, "=", 0>
  <Numero, "333", 2>

Expressao com varios tipos de espaco em branco — mesma sequencia de tipos/lexemas:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/espacos.ci"
  <Igual, "=", 0>
  <ParenEsq, "(", 2>
  <Numero, "3", 5>
  <Soma, "+", 9>
  <ParenEsq, "(", 14>
  <Numero, "4", 15>
  <Soma, "+", 17>
  <ParenEsq, "(", 19>
  <Numero, "11", 20>
  <Mult, "*", 23>
  <Numero, "7", 25>
  <ParenDir, ")", 26>
  <ParenDir, ")", 27>
  <ParenDir, ")", 31>

Erro lexico — mensagem em stderr (redirecionada) e exit code != 0:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/erro.ci" 2>&1
  Erro lexico na posicao 5: caractere invalido '$'
  [2]

Erro lexico com variavel (numero seguido de letra):

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/test_lex_err.ci" 2>&1
  Erro lexico na posicao 7: caractere invalido 'a'
  [2]
