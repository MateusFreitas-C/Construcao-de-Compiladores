Analise semantica — variavel usada em expressao sem ter sido declarada:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/test_undeclared.ci" 2>&1
  Erro semantico: variavel 'y' nao declarada
  [4]

Atribuicao a variavel nao declarada — a linguagem Cmd nao permite criar
variaveis por atribuicao:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/sem_atrib_nao_decl.ci" 2>&1
  Erro semantico: atribuicao a variavel 'y' nao declarada
  [4]

Variavel nao declarada usada dentro do braco de um `if`:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/sem_if_nao_decl.ci" 2>&1
  Erro semantico: variavel 'z' nao declarada
  [4]

Variavel nao declarada na condicao de um `while`:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/sem_while_nao_decl.ci" 2>&1
  Erro semantico: variavel 'limite' nao declarada
  [4]

Atribuicao a variavel declarada e valida — a tabela de simbolos nao cresce, mas
o valor muda:

  $ python3 "$TESTDIR/../compci.py" --ast "$TESTDIR/sem_atrib_ok.ci"
  arvore:
  x = 1;
  {
    x = (x + 41);
    return x;
  }
  valor: 42
