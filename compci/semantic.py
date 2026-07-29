from parser import Atribuicao, Const, Enquanto, OpBin, Se, Var


class ErroSemantico(Exception):
    pass


def verificar_semantica(arvore):
    # A tabela e um conjunto plano: a linguagem Cmd nao tem escopo aninhado, e
    # so declaracoes inserem simbolos (atribuicao nao cria variavel).
    tabela = set()
    for decl in arvore.declaracoes:
        _verificar_exp(decl.exp, tabela)
        tabela.add(decl.nome)
    for cmd in arvore.comandos:
        _verificar_cmd(cmd, tabela)
    _verificar_exp(arvore.exp_retorno, tabela)


def _verificar_cmd(no, tabela):
    if isinstance(no, Atribuicao):
        # o lado direito e verificado primeiro: em `z = z + 1;` com z nao
        # declarado, o erro aponta a leitura, que e onde o programador olha
        _verificar_exp(no.exp, tabela)
        if no.nome not in tabela:
            raise ErroSemantico(
                f"Erro semantico: atribuicao a variavel '{no.nome}' nao declarada"
            )
    elif isinstance(no, Se):
        _verificar_exp(no.cond, tabela)
        for cmd in no.entao:
            _verificar_cmd(cmd, tabela)
        for cmd in no.senao:
            _verificar_cmd(cmd, tabela)
    elif isinstance(no, Enquanto):
        _verificar_exp(no.cond, tabela)
        for cmd in no.corpo:
            _verificar_cmd(cmd, tabela)
    else:
        raise TypeError(f"comando de AST desconhecido: {no!r}")


def _verificar_exp(no, tabela):
    if isinstance(no, Const):
        pass
    elif isinstance(no, Var):
        if no.nome not in tabela:
            raise ErroSemantico(f"Erro semantico: variavel '{no.nome}' nao declarada")
    elif isinstance(no, OpBin):
        _verificar_exp(no.esq, tabela)
        _verificar_exp(no.dir, tabela)
    else:
        raise TypeError(f"no de AST desconhecido: {no!r}")
