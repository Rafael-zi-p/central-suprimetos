"""Restrição por obra, aplicada no servidor.

No cadastro de cada pessoa (Configurações › Usuários & Permissões), o administrador
pode limitar as obras que ela enxerga. Isso fica em `perfis.permissoes` como
entradas "obra:<código da coligada>". Sem nenhuma entrada "obra:" a pessoa vê todas.

A tela já escondia as outras obras, mas o servidor entregava tudo. Agora o servidor
tira as linhas das obras não liberadas antes de responder: no proxy do TOTVS, nos
arquivos da atualização automática e nas tabelas do banco que têm obra.
"""
import fnmatch
import json
import re

from . import config
from .usuario import eh_admin, usuario_atual

# nomes de coluna que carregam o código da coligada (obra) nas linhas do RM
COLUNAS_COLIGADA = ("__CODCOLIGADA", "CODCOLIGADA", "IDCOLIGADA", "COD_COLIGADA")
# fontes da atualização automática que não pertencem a uma obra (catálogo global)
FONTES_GLOBAIS = {"insumos"}


def permitidas(u=None):
    """Conjunto de coligadas liberadas, ou None quando a pessoa vê todas as obras."""
    u = u if u is not None else usuario_atual()
    if eh_admin(u):
        return None
    perms = ((u or {}).get("perfil") or {}).get("permissoes")
    if not isinstance(perms, list):
        return None
    cods = set()
    for k in perms:
        if isinstance(k, str) and k.startswith("obra:"):
            try:
                cods.add(int(k[5:]))
            except ValueError:
                pass
    return cods or None


def _numero(v):
    try:
        return int(float(str(v).strip().replace(",", ".")))
    except (TypeError, ValueError):
        return None


def coligada_da_linha(linha, extras=()):
    """Código da coligada de uma linha do RM, ou None se a linha não traz."""
    if not isinstance(linha, dict):
        return None
    chaves = {str(k).upper(): k for k in linha}
    for nome in tuple(COLUNAS_COLIGADA) + tuple(str(e).upper() for e in extras if e):
        if nome in chaves:
            n = _numero(linha[chaves[nome]])
            if n is not None:
                return n
    return None


def filtrar_linhas(linhas, liberadas, extras=(), manter_sem_coligada=False):
    """Deixa só as linhas das obras liberadas.

    Linha sem coligada identificável é descartada, a menos que a consulta seja global.
    """
    if liberadas is None or not isinstance(linhas, list):
        return linhas
    saida = []
    for r in linhas:
        c = coligada_da_linha(r, extras)
        if c is None:
            if manter_sem_coligada:
                saida.append(r)
        elif c in liberadas:
            saida.append(r)
    return saida


def consulta_global(nome):
    """Consultas do RM que não pertencem a uma obra (fornecedores, insumos...)."""
    padroes = [p.strip() for p in (config.TOTVS_CONSULTAS_GLOBAIS or "").split(",") if p.strip()]
    n = str(nome or "").upper()
    return any(fnmatch.fnmatch(n, p.upper()) for p in padroes)


_RX_PARAM_COL = re.compile(r"COLIGADA", re.I)


def parametros_coligadas(texto):
    """Coligadas pedidas nos parâmetros da consulta (";CODCOLIGADA_N=40;...")."""
    achadas = []
    for par in str(texto or "").split(";"):
        if "=" not in par:
            continue
        k, v = par.split("=", 1)
        if _RX_PARAM_COL.search(k) and not re.search(r"NOME|CADASTRO", k, re.I):
            n = _numero(v)
            achadas.append(n if n is not None else -1)
    return achadas


def parametros_ok(texto, liberadas):
    """False se a consulta pede uma obra que a pessoa não pode ver."""
    if liberadas is None:
        return True
    return all(c in liberadas for c in parametros_coligadas(texto) if c != 0)


def filtrar_resposta_rm(corpo_bytes, consulta, texto_params, liberadas, extras=()):
    """Filtra a resposta JSON de uma consulta do RM. Devolve (bytes, houve_filtro)."""
    if liberadas is None:
        return corpo_bytes, False
    try:
        j = json.loads(corpo_bytes.decode("utf-8-sig"))
    except Exception:
        return '{"erro":"resposta do TOTVS ilegível para filtrar por obra"}'.encode("utf-8"), True
    escopo_por_parametro = bool(parametros_coligadas(texto_params))   # a consulta já veio de uma obra liberada
    manter = consulta_global(consulta) or escopo_por_parametro
    if isinstance(j, list):
        j = filtrar_linhas(j, liberadas, extras, manter)
    elif isinstance(j, dict) and isinstance(j.get("data"), list):
        j["data"] = filtrar_linhas(j["data"], liberadas, extras, manter)
    return json.dumps(j, ensure_ascii=False).encode("utf-8"), True


def fonte_do_arquivo(caminho):
    m = re.match(r"^jobs/[0-9]+/([a-z]+)/", str(caminho or ""))
    return m.group(1) if m else ""
