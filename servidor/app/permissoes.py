"""Regras de quem pode ler e gravar cada tabela.

São as mesmas regras que o app tinha no banco anterior (arquivos 01, 09, 10 e 11
das regras), agora aplicadas no servidor. A tela nunca decide sozinha.
"""
from sqlalchemy import and_, false, func, not_, or_, true

from . import config
from . import obras as OBR
from .usuario import ativo, eh_admin, perfil_id, tem_perm


def pode_gravar_doc(tipo, u):
    """dados_compartilhados: quem pode gravar cada tipo de documento."""
    t = str(tipo or "")
    if not ativo(u):
        return False
    if eh_admin(u):
        return True
    if t in ("totvs_servidor_status", "totvs_servidor_agenda"):
        return False                                   # escritos só pelo servidor
    if t in ("param_obras", "param_coligadas_oc"):
        return tem_perm("import", u)
    if t.startswith("param_") or t in ("ia_cfg", "precfg", "orc_cfg"):
        return False                                   # configurações da equipe: só administrador
    if t.startswith("perfil_extra_"):
        return t == "perfil_extra_" + perfil_id(u)
    if t.startswith(("basem_", "basep_", "totvs_", "totvsp_")) or t == "cronograma":
        return tem_perm("import", u)
    if t.startswith("cubo_"):
        return tem_perm("cubo", u)
    if t in ("preco_ignorar", "oc_envios"):
        return tem_perm("oc", u)
    if t.startswith("forn_aval_"):
        return any(tem_perm(m, u) for m in ("forn", "forn_aval", "sc", "oc", "obras"))
    if t == "obras_painel":
        return tem_perm("obras_editar", u)
    return True


def limpar_doc(tipo, dados):
    """Nunca guardar credencial do TOTVS no banco (o servidor usa o usuário de serviço)."""
    if tipo == "param_totvs" and isinstance(dados, dict):
        for k in ("usuario", "senha", "token", "password"):
            dados.pop(k, None)
    return dados


def filtro_leitura(nome, T, u):
    """Condição extra de leitura por tabela (ou None = recusar)."""
    me_email = (u or {}).get("email", "")
    me_id = (u or {}).get("id")
    if nome == "auditoria":
        return true() if eh_admin(u) else None
    if nome == "perfis":
        if ativo(u):
            return true()
        return or_(T.c.auth_user_id == me_id, func.lower(T.c.email) == me_email)
    if not ativo(u):
        return None
    if nome == "notificacoes":
        return true() if eh_admin(u) else func.lower(T.c.destinatario_email) == me_email
    if nome == "anotacoes":
        return or_(T.c.dono == me_id, T.c.compartilhada.is_(True))
    lib = OBR.permitidas(u)
    if lib is not None:
        if nome == "sc_itens":
            return T.c.coligada.in_(list(lib))
        if nome == "dados_compartilhados":
            # cópia antiga com todas as obras: fica fora do alcance de quem tem obras restritas
            return not_(T.c.tipo.like(r"totvsp\_%", escape="\\"))
    return true()


def filtro_escrita(nome, T, u, op):
    """Condição extra para update/delete (ou None = recusar)."""
    me_email = (u or {}).get("email", "")
    me_id = (u or {}).get("id")
    if nome == "auditoria":
        return None
    if eh_admin(u):
        return true()
    if not ativo(u) and nome != "perfis":
        return None
    if nome == "perfis":
        if op == "delete":
            return None
        return or_(T.c.auth_user_id == me_id, and_(T.c.auth_user_id.is_(None), func.lower(T.c.email) == me_email))
    if nome == "departamentos":
        return None
    if nome == "pessoa_insumos":
        return true() if tem_perm("cubo", u) else None
    if nome == "notificacoes":
        return func.lower(T.c.destinatario_email) == me_email
    if nome == "anotacoes":
        return T.c.dono == me_id if op == "delete" else or_(T.c.dono == me_id, T.c.compartilhada.is_(True))
    if nome == "sync_log" and op == "delete":
        return None
    lib = OBR.permitidas(u)
    if lib is not None and nome == "sc_itens":
        return T.c.coligada.in_(list(lib))
    return true()


# colunas que uma pessoa (não administradora) pode mudar no próprio perfil
PERFIL_CAMPOS_PROPRIOS = {"nome", "telefone", "auth_user_id"}


def preparar_linha(nome, linha, u, op):
    """Ajusta/recusa uma linha antes de gravar. Devolve a linha ou levanta PermissionError."""
    me_id = (u or {}).get("id")
    if nome == "auditoria":
        raise PermissionError("auditoria é gravada só pelo servidor")
    if nome == "dados_compartilhados":
        if op in ("insert", "upsert") and not pode_gravar_doc(linha.get("tipo"), u):
            raise PermissionError("sem permissão para gravar " + str(linha.get("tipo")))
        if "dados" in linha:
            linha["dados"] = limpar_doc(linha.get("tipo"), linha["dados"])
        return linha
    if nome == "perfis":
        if eh_admin(u):
            return linha
        if op == "insert":
            if str(linha.get("auth_user_id") or "") != str(me_id) or str(linha.get("email") or "").lower() != u.get("email"):
                raise PermissionError("só é possível criar o próprio perfil")
            linha["is_admin"] = False
            linha["ativo"] = config.PERFIL_NOVO_ATIVO
            perms = [x.strip() for x in config.PERFIL_NOVO_PERMISSOES.split(",") if x.strip()]
            linha["permissoes"] = perms   # vazio = nenhuma aba até o administrador liberar (como no app atual)
            linha.pop("departamento_id", None)
            return linha
        extra = set(linha) - PERFIL_CAMPOS_PROPRIOS
        if extra:
            raise PermissionError("só o administrador muda " + ", ".join(sorted(extra)))
        if "auth_user_id" in linha and str(linha["auth_user_id"]) != str(me_id):
            raise PermissionError("vínculo de login inválido")
        return linha
    if nome == "departamentos" and not eh_admin(u):
        raise PermissionError("só o administrador muda departamentos")
    if nome == "pessoa_insumos" and not (eh_admin(u) or tem_perm("cubo", u)):
        raise PermissionError("sem permissão para mudar carteiras")
    if not ativo(u):
        raise PermissionError("perfil inativo")
    if nome == "anotacoes" and op == "insert":
        linha["dono"] = me_id
    if nome == "notificacoes" and op == "insert":
        p = (u or {}).get("perfil") or {}
        linha["criado_por"] = p.get("nome") or u.get("email")
    return linha
