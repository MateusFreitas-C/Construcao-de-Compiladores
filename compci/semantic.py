from parser import Const, Var, OpBin, Programa

class ErroSemantico(Exception):
    pass

def verificar_semantica(arvore):
    tabela = set()
    for decl in arvore.declaracoes:
        _verificar_exp(decl.exp, tabela)
        tabela.add(decl.nome)
    _verificar_exp(arvore.exp_final, tabela)

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
