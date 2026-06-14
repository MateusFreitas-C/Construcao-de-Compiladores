Analisador lexico EC1 — programa OK do exemplo do PDF:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/ok.ci"
  <ParenEsq, "(", 0>
  <Numero, "33", 1>
  <Soma, "+", 4>
  <ParenEsq, "(", 6>
  <Numero, "912", 7>
  <Mult, "*", 11>
  <Numero, "11", 13>
  <ParenDir, ")", 15>
  <ParenDir, ")", 16>

Literal isolado:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/literal.ci"
  <Numero, "333", 0>

Expressao com varios tipos de espaco em branco — mesma sequencia de tipos/lexemas:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/espacos.ci"
  <ParenEsq, "(", 0>
  <Numero, "3", 3>
  <Soma, "+", 7>
  <ParenEsq, "(", 12>
  <Numero, "4", 13>
  <Soma, "+", 15>
  <ParenEsq, "(", 17>
  <Numero, "11", 18>
  <Mult, "*", 21>
  <Numero, "7", 23>
  <ParenDir, ")", 24>
  <ParenDir, ")", 25>
  <ParenDir, ")", 29>

Erro lexico — mensagem em stderr (redirecionada) e exit code != 0:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/erro.ci" 2>&1
  Erro lexico na posicao 3: caractere invalido '$'
  [2]
