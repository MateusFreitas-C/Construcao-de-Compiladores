Analisador lexico Cmd — programa OK do exemplo do PDF:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/ok.ci"
  <ChaveEsq, "{", 0>
  <Retorno, "return", 4>
  <ParenEsq, "(", 11>
  <Numero, "33", 12>
  <Soma, "+", 15>
  <ParenEsq, "(", 17>
  <Numero, "912", 18>
  <Mult, "*", 22>
  <Numero, "11", 24>
  <ParenDir, ")", 26>
  <ParenDir, ")", 27>
  <PontoVirgula, ";", 28>
  <ChaveDir, "}", 30>

Literal isolado:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/literal.ci"
  <ChaveEsq, "{", 0>
  <Retorno, "return", 4>
  <Numero, "333", 11>
  <PontoVirgula, ";", 14>
  <ChaveDir, "}", 16>

Expressao com varios tipos de espaco em branco — mesma sequencia de tipos/lexemas:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/espacos.ci"
  <ChaveEsq, "{", 0>
  <Retorno, "return", 4>
  <ParenEsq, "(", 11>
  <Numero, "3", 14>
  <Soma, "+", 18>
  <ParenEsq, "(", 23>
  <Numero, "4", 24>
  <Soma, "+", 26>
  <ParenEsq, "(", 28>
  <Numero, "11", 29>
  <Mult, "*", 32>
  <Numero, "7", 34>
  <ParenDir, ")", 35>
  <ParenDir, ")", 36>
  <ParenDir, ")", 40>
  <PontoVirgula, ";", 41>
  <ChaveDir, "}", 43>

Erro lexico — mensagem em stderr (redirecionada) e exit code != 0:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/erro.ci" 2>&1
  Erro lexico na posicao 14: caractere invalido '$'
  [2]

Erro lexico com variavel (numero seguido de letra):

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/test_lex_err.ci" 2>&1
  Erro lexico na posicao 7: caractere invalido 'a'
  [2]

Os seis operadores de comparacao sao reconhecidos por maximal munch. O `sed`
remove a posicao para que este caso teste tipos e lexemas; posicoes tem um caso
dedicado logo abaixo:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/lex_operadores.ci" | sed 's/, [0-9]*>$/>/' | grep -E 'Igualdade|Diferente|Menor|Maior'
  <Igualdade, "==">
  <Diferente, "!=">
  <MenorIgual, "<=">
  <MaiorIgual, ">=">
  <Menor, "<">
  <Maior, ">">

`=` e `==` sao tokens diferentes: o arquivo tem 7 atribuicoes (uma declaracao
mais seis dentro dos `if`) e nenhuma delas vira Igualdade:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/lex_operadores.ci" | grep -c '^<Igual,'
  7

Chaves e a palavra-chave `if`:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/lex_operadores.ci" | head -6
  <Identificador, "a", 0>
  <Igual, "=", 2>
  <Numero, "1", 4>
  <PontoVirgula, ";", 5>
  <ChaveEsq, "{", 7>
  <Se, "if", 11>

Posicoes exatas — um token de dois caracteres reporta a posicao do PRIMEIRO
caractere, entao `<=` fica em 13 e nao em 14:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/lex_pos.ci"
  <ChaveEsq, "{", 0>
  <Retorno, "return", 4>
  <Numero, "1", 11>
  <MenorIgual, "<=", 13>
  <Numero, "2", 16>
  <PontoVirgula, ";", 17>
  <ChaveDir, "}", 19>

Identificador que comeca com palavra-chave continua sendo identificador, e
`return` de verdade vira palavra-chave:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/lex_palavras.ci" | sed 's/, [0-9]*>$/>/' | grep -E 'Identificador|Retorno|Senao|Enquanto'
  <Identificador, "ifx">
  <Identificador, "elsey">
  <Identificador, "whilez">
  <Identificador, "returno">
  <Retorno, "return">
  <Identificador, "ifx">

`!` sozinho e erro lexico:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/lex_bang.ci" 2>&1
  Erro lexico na posicao 13: caractere invalido '!'
  [2]
