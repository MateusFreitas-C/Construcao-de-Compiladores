from parser import Atribuicao, Chamada, Const, Enquanto, FuncDecl, OpBin, Se, Var


class ErroSemantico(Exception):
    pass


def verificar_semantica(arvore):
    # Tabela global: nome -> ("var", None) para variavel global, ou
    # ("func", aridade) para funcao. As declaracoes sao processadas na ordem
    # em que aparecem no programa, entao uma variavel ou funcao so pode
    # referenciar o que foi declarado antes dela — exceto a propria funcao,
    # que e inserida na tabela global ANTES de seu corpo ser verificado, o que
    # permite recursao direta (mas nao mutua: uma funcao declarada depois
    # ainda nao existe na tabela quando o corpo desta e verificado).
    tabela_global = {}
    for decl in arvore.declaracoes:
        if isinstance(decl, FuncDecl):
            _verificar_fundecl(decl, tabela_global)
        else:
            _verificar_exp(decl.exp, tabela_global, None)
            tabela_global[decl.nome] = ("var", None)
    for cmd in arvore.comandos:
        _verificar_cmd(cmd, tabela_global, None)
    _verificar_exp(arvore.exp_retorno, tabela_global, None)


def _verificar_fundecl(func, tabela_global):
    if func.nome in tabela_global and tabela_global[func.nome][0] != "func":
        raise ErroSemantico(
            f"Erro semantico: '{func.nome}' ja foi declarada como variavel"
        )
    tabela_global[func.nome] = ("func", len(func.params))

    # tabela local: parametros primeiro (visiveis desde o inicio do corpo),
    # depois cada variavel local e inserida assim que sua propria declaracao e
    # verificada (o lado direito pode referenciar locais/parametros ja vistos)
    tabela_local = set(func.params)
    for vardecl in func.vardecls:
        _verificar_exp(vardecl.exp, tabela_global, tabela_local)
        tabela_local.add(vardecl.nome)
    for cmd in func.comandos:
        _verificar_cmd(cmd, tabela_global, tabela_local)
    _verificar_exp(func.exp_retorno, tabela_global, tabela_local)


def _verificar_cmd(no, tabela_global, tabela_local):
    if isinstance(no, Atribuicao):
        # o lado direito e verificado primeiro: em `z = z + 1;` com z nao
        # declarado, o erro aponta a leitura, que e onde o programador olha
        _verificar_exp(no.exp, tabela_global, tabela_local)
        local = tabela_local is not None and no.nome in tabela_local
        if not local:
            entrada = tabela_global.get(no.nome)
            if entrada is None or entrada[0] != "var":
                raise ErroSemantico(
                    f"Erro semantico: atribuicao a variavel '{no.nome}' nao declarada"
                )
    elif isinstance(no, Se):
        _verificar_exp(no.cond, tabela_global, tabela_local)
        for cmd in no.entao:
            _verificar_cmd(cmd, tabela_global, tabela_local)
        for cmd in no.senao:
            _verificar_cmd(cmd, tabela_global, tabela_local)
    elif isinstance(no, Enquanto):
        _verificar_exp(no.cond, tabela_global, tabela_local)
        for cmd in no.corpo:
            _verificar_cmd(cmd, tabela_global, tabela_local)
    else:
        raise TypeError(f"comando de AST desconhecido: {no!r}")


def _verificar_exp(no, tabela_global, tabela_local):
    if isinstance(no, Const):
        pass
    elif isinstance(no, Var):
        # variavel local (ou parametro) esconde uma global de mesmo nome; um
        # nome de funcao nao e uma referencia de variavel valida (precisa de
        # parenteses para ser uma chamada)
        local = tabela_local is not None and no.nome in tabela_local
        if not local:
            entrada = tabela_global.get(no.nome)
            if entrada is None or entrada[0] != "var":
                raise ErroSemantico(
                    f"Erro semantico: variavel '{no.nome}' nao declarada"
                )
    elif isinstance(no, OpBin):
        _verificar_exp(no.esq, tabela_global, tabela_local)
        _verificar_exp(no.dir, tabela_global, tabela_local)
    elif isinstance(no, Chamada):
        entrada = tabela_global.get(no.nome)
        if entrada is None:
            raise ErroSemantico(f"Erro semantico: funcao '{no.nome}' nao declarada")
        if entrada[0] != "func":
            raise ErroSemantico(f"Erro semantico: '{no.nome}' nao e uma funcao")
        aridade = entrada[1]
        if len(no.args) != aridade:
            raise ErroSemantico(
                f"Erro semantico: funcao '{no.nome}' espera {aridade} parametro(s), "
                f"recebeu {len(no.args)}"
            )
        for arg in no.args:
            _verificar_exp(arg, tabela_global, tabela_local)
    else:
        raise TypeError(f"no de AST desconhecido: {no!r}")
