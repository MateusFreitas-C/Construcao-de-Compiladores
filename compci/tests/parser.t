Literal isolado — arvore e valor:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/literal.ci"
  arvore: = 333
  valor: 333

Expressao do exemplo do PDF — arvore e valor:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/ok.ci"
  arvore: = (33 + (912 * 11))
  valor: 10065

Expressao com varios tipos de espaco em branco:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/espacos.ci"
  arvore: = (3 + (4 + (11 * 7)))
  valor: 84

Erro lexico — exit code 2:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/erro.ci" 2>&1
  Erro lexico na posicao 5: caractere invalido '$'
  [2]

Erro sintatico: fecha-parenteses esperado mas encontrou numero (sem producao <exp> <op> <exp> na EC2):

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/erro_sint_op.ci" 2>&1
  Erro sintatico na posicao 6: esperado 'ParenDir', encontrado '33'
  [3]

Erro sintatico: parentese fechando ausente:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/erro_sint_fecha.ci" 2>&1
  Erro sintatico na posicao 11: esperado 'ParenDir', encontrado 'EOF'
  [3]

Erro sintatico: tokens extras apos a expressao:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/erro_sint_extra.ci" 2>&1
  Erro sintatico na posicao 5: tokens inesperados apos expressao: '99'
  [3]

Precedencia: multiplicacao antes da soma, sem parenteses:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/precedencia.ci"
  arvore: = (7 + (5 * 3))
  valor: 22

Associatividade a esquerda na subtracao:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/assoc_sub.ci"
  arvore: = ((10 - 8) - 2)
  valor: 0

Associatividade a esquerda na divisao:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/assoc_div.ci"
  arvore: = ((100 / 5) / 2)
  valor: 10

Expressao sem nenhum parenteses, com as quatro operacoes:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/sem_parenteses.ci"
  arvore: = ((2 + (3 * 4)) - (6 / 2))
  valor: 11

Parenteses continuam opcionais para forcar outra ordem:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/parenteses_opcionais.ci"
  arvore: = ((7 + 5) * 3)
  valor: 36

Programa com variaveis:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/test_vars.ci"
  arvore: x = ((7 + 4) * 12); y = ((x * 3) + 11); = (((x * y) + (x * 11)) + (y * 13))
  valor: 60467
