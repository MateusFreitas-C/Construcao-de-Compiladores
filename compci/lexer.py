# Analisador lexico da linguagem EC1.
# Modulo separado para crescer junto com a linguagem nas proximas atividades.

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
        elif c in OPERADORES:
            tokens.append(Token(OPERADORES[c], c, i))
            i += 1
        elif c.isdigit():
            inicio = i
            while i < n and texto[i].isdigit():
                i += 1
            tokens.append(Token(NUMERO, texto[inicio:i], inicio))
        else:
            raise ErroLexico(i, c)
    tokens.append(Token(EOF, "", n))
    return tokens


def formatar(tok):
    return f'<{tok.tipo}, "{tok.lexema}", {tok.pos}>'
