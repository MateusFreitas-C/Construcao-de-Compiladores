Literal isolado — arvore e valor:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/literal.ci"
  arvore:
  {
    return 333;
  }
  valor: 333

Expressao do exemplo do PDF:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/ok.ci"
  arvore:
  {
    return (33 + (912 * 11));
  }
  valor: 10065

Expressao com varios tipos de espaco em branco:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/espacos.ci"
  arvore:
  {
    return (3 + (4 + (11 * 7)));
  }
  valor: 84

Erro lexico — exit code 2:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/erro.ci" 2>&1
  Erro lexico na posicao 14: caractere invalido '$'
  [2]

Erro sintatico: fecha-parenteses esperado mas encontrou numero:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/erro_sint_op.ci" 2>&1
  Erro sintatico na posicao 15: esperado 'ParenDir', encontrado '33'
  [3]

Erro sintatico: parentese fechando ausente:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/erro_sint_fecha.ci" 2>&1
  Erro sintatico na posicao 19: esperado 'ParenDir', encontrado ';'
  [3]

Erro sintatico: tokens extras depois do corpo:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/erro_sint_extra.ci" 2>&1
  Erro sintatico na posicao 17: tokens inesperados apos expressao: '99'
  [3]

Precedencia: multiplicacao antes da soma, sem parenteses:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/precedencia.ci"
  arvore:
  {
    return (7 + (5 * 3));
  }
  valor: 22

Associatividade a esquerda na subtracao:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/assoc_sub.ci"
  arvore:
  {
    return ((10 - 8) - 2);
  }
  valor: 0

Associatividade a esquerda na divisao:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/assoc_div.ci"
  arvore:
  {
    return ((100 / 5) / 2);
  }
  valor: 10

Expressao sem nenhum parenteses, com as quatro operacoes:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/sem_parenteses.ci"
  arvore:
  {
    return ((2 + (3 * 4)) - (6 / 2));
  }
  valor: 11

Parenteses continuam opcionais para forcar outra ordem:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/parenteses_opcionais.ci"
  arvore:
  {
    return ((7 + 5) * 3);
  }
  valor: 36

Programa com variaveis:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/test_vars.ci"
  arvore:
  x = ((7 + 4) * 12);
  y = ((x * 3) + 11);
  {
    return (((x * y) + (x * 11)) + (y * 13));
  }
  valor: 60467

Comparacao tem precedencia mais baixa que a soma — `1 + 2 < 4` agrupa como
`((1 + 2) < 4)`, e o resultado e 1 (verdadeiro):

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/prec_comparacao.ci"
  arvore:
  {
    return ((1 + 2) < 4);
  }
  valor: 1

Comando condicional com os dois bracos:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/if_simples.ci"
  arvore:
  a = 1;
  b = 2;
  c = 3;
  delta = 0;
  {
    delta = ((b * b) - ((4 * a) * c));
    if (delta < 0) {
      delta = (0 - delta);
    } else {
      delta = delta;
    }
    return delta;
  }
  valor: 8

Comando condicional sem `else` (extensao) — mesmo resultado, sem o braco
artificial:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/if_sem_else.ci"
  arvore:
  a = 1;
  b = 2;
  c = 3;
  delta = 0;
  {
    delta = ((b * b) - ((4 * a) * c));
    if (delta < 0) {
      delta = (0 - delta);
    }
    return delta;
  }
  valor: 8

Comando de repeticao:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/while_simples.ci"
  arvore:
  n = 1;
  m = 10;
  soma = 0;
  {
    while (n < m) {
      soma = (soma + n);
      n = (n + 1);
    }
    return soma;
  }
  valor: 45

Erro sintatico: `return` nao e um comando, entao nao pode aparecer dentro de um
bloco — a lista de comandos encerra e o bloco exige a chave de fechamento:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/erro_return_fora.ci" 2>&1
  Erro sintatico na posicao 22: esperado 'ChaveDir', encontrado 'return'
  [3]

Erro sintatico: `else` sem `if`:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/erro_else_orfao.ci" 2>&1
  Erro sintatico na posicao 4: esperado 'Retorno', encontrado 'else'
  [3]

Erro sintatico: corpo do programa sem fechar — o erro so aparece no EOF:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/erro_chave.ci" 2>&1
  Erro sintatico na posicao 23: esperado 'ChaveDir', encontrado 'EOF'
  [3]
