Analisador lexico Fun — programa OK do exemplo do PDF, agora dentro do bloco
`main`:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/ok.ci"
  <Main, "main", 0>
  <ChaveEsq, "{", 5>
  <Retorno, "return", 9>
  <ParenEsq, "(", 16>
  <Numero, "33", 17>
  <Soma, "+", 20>
  <ParenEsq, "(", 22>
  <Numero, "912", 23>
  <Mult, "*", 27>
  <Numero, "11", 29>
  <ParenDir, ")", 31>
  <ParenDir, ")", 32>
  <PontoVirgula, ";", 33>
  <ChaveDir, "}", 35>

Literal isolado:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/literal.ci"
  <Main, "main", 0>
  <ChaveEsq, "{", 5>
  <Retorno, "return", 9>
  <Numero, "333", 16>
  <PontoVirgula, ";", 19>
  <ChaveDir, "}", 21>

Expressao com varios tipos de espaco em branco — mesma sequencia de tipos/lexemas:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/espacos.ci"
  <Main, "main", 0>
  <ChaveEsq, "{", 5>
  <Retorno, "return", 9>
  <ParenEsq, "(", 16>
  <Numero, "3", 19>
  <Soma, "+", 23>
  <ParenEsq, "(", 28>
  <Numero, "4", 29>
  <Soma, "+", 31>
  <ParenEsq, "(", 33>
  <Numero, "11", 34>
  <Mult, "*", 37>
  <Numero, "7", 39>
  <ParenDir, ")", 40>
  <ParenDir, ")", 41>
  <ParenDir, ")", 45>
  <PontoVirgula, ";", 46>
  <ChaveDir, "}", 48>

Erro lexico — mensagem em stderr (redirecionada) e exit code != 0:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/erro.ci" 2>&1
  Erro lexico na posicao 19: caractere invalido '$'
  [2]

Erro lexico com variavel (numero seguido de letra):

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/test_lex_err.ci" 2>&1
  Erro lexico na posicao 11: caractere invalido 'a'
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

Palavra-chave `var` na declaracao global, chaves e a palavra-chave `if`:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/lex_operadores.ci" | head -9
  <Var, "var", 0>
  <Identificador, "a", 4>
  <Igual, "=", 6>
  <Numero, "1", 8>
  <PontoVirgula, ";", 9>
  <Main, "main", 11>
  <ChaveEsq, "{", 16>
  <Se, "if", 20>
  <Identificador, "a", 23>

Posicoes exatas — um token de dois caracteres reporta a posicao do PRIMEIRO
caractere, entao `<=` fica em 18 e nao em 19:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/lex_pos.ci"
  <Main, "main", 0>
  <ChaveEsq, "{", 5>
  <Retorno, "return", 9>
  <Numero, "1", 16>
  <MenorIgual, "<=", 18>
  <Numero, "2", 21>
  <PontoVirgula, ";", 22>
  <ChaveDir, "}", 24>

Identificador que comeca com palavra-chave continua sendo identificador, e
`return`/`var`/`main` de verdade viram palavra-chave:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/lex_palavras.ci" | sed 's/, [0-9]*>$/>/' | grep -E 'Identificador|Retorno|Senao|Enquanto|Var|Main'
  <Var, "var">
  <Identificador, "ifx">
  <Var, "var">
  <Identificador, "elsey">
  <Var, "var">
  <Identificador, "whilez">
  <Var, "var">
  <Identificador, "returno">
  <Main, "main">
  <Retorno, "return">
  <Identificador, "ifx">

`!` sozinho deixou de ser erro lexico: agora e o operador de negacao. O
programa `return 1 ! 2;` continua invalido, mas o erro migrou para o
analisador sintatico — `!` e prefixo, nao infixo:

  $ python3 "$TESTDIR/../compci.py" --stdout "$TESTDIR/lex_bang.ci"
  Erro sintatico na posicao 18: esperado 'PontoVirgula', encontrado '!'
  [3]

Um caractere que nao pertence a linguagem continua sendo erro lexico:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/lex_invalido.ci" 2>&1
  Erro lexico na posicao 18: caractere invalido '@'
  [2]

`&` e `|` so existem em pares (`&&` e `||`); sozinhos sao erro lexico:

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/lex_e_solto.ci" 2>&1
  Erro lexico na posicao 18: caractere invalido '&'
  [2]

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/lex_ou_solto.ci" 2>&1
  Erro lexico na posicao 18: caractere invalido '|'
  [2]

Colchetes viram tokens proprios, usados tanto na declaracao de array
(`var a[2];`) quanto na indexacao (`a[0]`):

  $ python3 "$TESTDIR/../compci.py" --tokens "$TESTDIR/lex_colchetes.ci" | sed 's/, [0-9]*>$/>/' | grep -E 'Colchete|Var|Identificador'
  <Var, "var">
  <Identificador, "a">
  <ColcheteEsq, "[">
  <ColcheteDir, "]">
  <Identificador, "a">
  <ColcheteEsq, "[">
  <ColcheteDir, "]">
  <Identificador, "a">
  <ColcheteEsq, "[">
  <ColcheteDir, "]">
