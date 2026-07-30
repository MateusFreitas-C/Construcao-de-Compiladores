from collections import namedtuple

# tipos de token
PAREN_ESQ = "ParenEsq"
PAREN_DIR = "ParenDir"
SOMA = "Soma"
SUB = "Sub"
MULT = "Mult"
DIV = "Div"
NUMERO = "Numero"
EOF = "EOF"
PONTO_VIRGULA = "PontoVirgula"
IGUAL = "Igual"
IDENTIFICADOR = "Identificador"
CHAVE_ESQ = "ChaveEsq"
CHAVE_DIR = "ChaveDir"
MENOR = "Menor"
MAIOR = "Maior"
MENOR_IGUAL = "MenorIgual"
MAIOR_IGUAL = "MaiorIgual"
IGUALDADE = "Igualdade"
DIFERENTE = "Diferente"
SE = "Se"
SENAO = "Senao"
ENQUANTO = "Enquanto"
RETORNO = "Retorno"
VIRGULA = "Virgula"
FUN = "Fun"
VAR = "Var"
MAIN = "Main"

# palavras-chave seguem as regras de identificador; sao separadas depois de
# reconhecer o lexema (ver tokenizar)
PALAVRAS_CHAVE = {
    "if": SE,
    "else": SENAO,
    "while": ENQUANTO,
    "return": RETORNO,
    "fun": FUN,
    "var": VAR,
    "main": MAIN,
}

OPERADORES = {
    "+": SOMA,
    "-": SUB,
    "*": MULT,
    "/": DIV,
}

ESPACOS = (" ", "\t", "\n", "\r")

Token = namedtuple("Token", ["tipo", "lexema", "pos"])


class ErroLexico(Exception):
    def __init__(self, pos, char):
        self.pos = pos
        self.char = char
        super().__init__(f"Erro lexico na posicao {pos}: caractere invalido '{char}'")


def tokenizar(texto):
    tokens = []
    i = 0
    n = len(texto)
    while i < n:
        c = texto[i]
        if c in ESPACOS:
            i += 1
            continue
        if c == "(":
            tokens.append(Token(PAREN_ESQ, c, i))
            i += 1
        elif c == ")":
            tokens.append(Token(PAREN_DIR, c, i))
            i += 1
        elif c == ";":
            tokens.append(Token(PONTO_VIRGULA, c, i))
            i += 1
        elif c == ",":
            tokens.append(Token(VIRGULA, c, i))
            i += 1
        elif c == "{":
            tokens.append(Token(CHAVE_ESQ, c, i))
            i += 1
        elif c == "}":
            tokens.append(Token(CHAVE_DIR, c, i))
            i += 1
        elif c == "=":
            if i + 1 < n and texto[i + 1] == "=":
                tokens.append(Token(IGUALDADE, "==", i))
                i += 2
            else:
                tokens.append(Token(IGUAL, c, i))
                i += 1
        elif c == "<":
            if i + 1 < n and texto[i + 1] == "=":
                tokens.append(Token(MENOR_IGUAL, "<=", i))
                i += 2
            else:
                tokens.append(Token(MENOR, c, i))
                i += 1
        elif c == ">":
            if i + 1 < n and texto[i + 1] == "=":
                tokens.append(Token(MAIOR_IGUAL, ">=", i))
                i += 2
            else:
                tokens.append(Token(MAIOR, c, i))
                i += 1
        elif c == "!":
            if i + 1 < n and texto[i + 1] == "=":
                tokens.append(Token(DIFERENTE, "!=", i))
                i += 2
            else:
                raise ErroLexico(i, c)
        elif c in OPERADORES:
            tokens.append(Token(OPERADORES[c], c, i))
            i += 1
        elif c.isalpha():
            inicio = i
            while i < n and texto[i].isalnum():
                i += 1
            lexema = texto[inicio:i]
            tipo = PALAVRAS_CHAVE.get(lexema, IDENTIFICADOR)
            tokens.append(Token(tipo, lexema, inicio))
        elif c.isdigit():
            inicio = i
            while i < n and texto[i].isdigit():
                i += 1
            if i < n and texto[i].isalpha():
                raise ErroLexico(i, texto[i])
            tokens.append(Token(NUMERO, texto[inicio:i], inicio))
        else:
            raise ErroLexico(i, c)
    tokens.append(Token(EOF, "", n))
    return tokens


def formatar(tok):
    return f'<{tok.tipo}, "{tok.lexema}", {tok.pos}>'
