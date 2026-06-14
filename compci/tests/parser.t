Literal isolado — arvore e valor:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/literal.ci"
  arvore: 333
  valor: 333

Expressao do exemplo do PDF — arvore e valor:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/ok.ci"
  arvore: (33 + (912 * 11))
  valor: 10065

Expressao com varios tipos de espaco em branco:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/espacos.ci"
  arvore: (3 + (4 + (11 * 7)))
  valor: 84

Erro lexico — exit code 2:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/erro.ci" 2>&1
  Erro lexico na posicao 3: caractere invalido '$'
  [2]

Erro sintatico: operador esperado mas encontrou numero:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/erro_sint_op.ci" 2>&1
  Erro sintatico na posicao 4: esperado operador, encontrado '33'
  [3]

Erro sintatico: parentese fechando ausente:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/erro_sint_fecha.ci" 2>&1
  Erro sintatico na posicao 9: esperado 'ParenDir', encontrado 'EOF'
  [3]

Erro sintatico: tokens extras apos a expressao:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/erro_sint_extra.ci" 2>&1
  Erro sintatico na posicao 3: tokens inesperados apos expressao: '99'
  [3]
