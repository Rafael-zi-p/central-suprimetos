"""POST /api/db — a tela faz as mesmas consultas de sempre; o servidor confere e executa.

Corpo (JSON), montado pelo adaptador da tela (pz-servidor.js):
  { tabela, op: select|insert|upsert|update|delete, colunas, filtros:[{c, op, v, neg}],
    ou, ordem:[{c, asc}], limite, de, ate, dados, conflito, ignorarDuplicados,
    retornar, contar, cabeca }
Só tabelas e colunas que existem no schema do app são aceitas; os valores vão
sempre como parâmetro (sem SQL montado com texto do usuário).
"""
import json
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import and_, delete, func, insert, not_, or_, select, true, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from . import permissoes as P
from .db import engine, tabela
from .usuario import eh_admin, exige_login, usuario_atual

bp = Blueprint("db", __name__)

OPS = {"eq", "neq", "gt", "gte", "lt", "lte", "like", "ilike", "in", "is"}


class Recusado(Exception):
    pass


def _col(T, nome):
    nome = str(nome or "").strip()
    if nome not in T.c:
        raise Recusado("coluna desconhecida: %s" % nome)
    return T.c[nome]


def _cond(T, f):
    c = _col(T, f.get("c"))
    op = f.get("op")
    v = f.get("v")
    if op not in OPS:
        raise Recusado("operação de filtro não suportada: %s" % op)
    if op == "eq":
        e = c == v
    elif op == "neq":
        e = c != v
    elif op == "gt":
        e = c > v
    elif op == "gte":
        e = c >= v
    elif op == "lt":
        e = c < v
    elif op == "lte":
        e = c <= v
    elif op == "like":
        e = c.like(v)
    elif op == "ilike":
        e = c.ilike(v)
    elif op == "in":
        e = c.in_(list(v or []))
    else:  # is
        e = c.is_(None) if v in (None, "null") else c.is_(bool(v))
    return not_(e) if f.get("neg") else e


def _ou(T, texto):
    """Formato do .or(): "auth_user_id.eq.X,email.eq.Y" (só eq/neq/is)."""
    partes = []
    for item in str(texto or "").split(","):
        bits = item.split(".", 2)
        if len(bits) != 3:
            raise Recusado("filtro 'or' inválido")
        c, op, v = bits
        if op not in ("eq", "neq", "is"):
            raise Recusado("filtro 'or' só aceita eq/neq/is")
        partes.append(_cond(T, {"c": c, "op": op, "v": None if v == "null" else v}))
    return or_(*partes) if partes else true()


def _where(T, corpo):
    conds = [_cond(T, f) for f in (corpo.get("filtros") or [])]
    if corpo.get("ou"):
        conds.append(_ou(T, corpo["ou"]))
    return and_(*conds) if conds else true()


def _colunas(T, txt):
    txt = str(txt or "*").strip()
    if txt in ("", "*"):
        return list(T.c)
    return [_col(T, x) for x in txt.split(",")]


def _limpar_linha(T, linha):
    return {k: v for k, v in (linha or {}).items() if k in T.c}


def _json(v):
    if isinstance(v, datetime):
        return v.astimezone(timezone.utc).isoformat()
    if hasattr(v, "isoformat"):
        return v.isoformat()
    if hasattr(v, "hex") and not isinstance(v, (bytes, str)):
        return str(v)
    if isinstance(v, (int, float, str, bool)) or v is None or isinstance(v, (list, dict)):
        return v
    return str(v)


def _linhas(res):
    return [{k: _json(v) for k, v in dict(r).items()} for r in res.mappings().all()]


def _auditar(cx, u, nome, acao, registro, resumo, antes=None, depois=None):
    if nome not in ("perfis", "departamentos", "dados_compartilhados", "pessoa_insumos"):
        return
    A = tabela("auditoria")
    cx.execute(insert(A).values(quem_id=u.get("id"), quem_email=u.get("email"), tabela=nome, acao=acao,
                                registro=str(registro or "")[:200], resumo=(resumo or "")[:300],
                                antes=antes, depois=depois))


@bp.post("/api/db")
@exige_login
def api_db():
    u = usuario_atual()
    corpo = request.get_json(silent=True) or {}
    nome = str(corpo.get("tabela") or "")
    T = tabela(nome)
    if T is None:
        return jsonify(erro="tabela não permitida"), 400
    op = corpo.get("op") or "select"
    try:
        with engine.begin() as cx:
            if op == "select":
                return _select(cx, T, nome, corpo, u)
            if op in ("insert", "upsert"):
                return _inserir(cx, T, nome, corpo, u, op)
            if op in ("update", "delete"):
                return _alterar(cx, T, nome, corpo, u, op)
            return jsonify(erro="operação desconhecida"), 400
    except Recusado as e:
        return jsonify(erro=str(e)), 400
    except PermissionError as e:
        return jsonify(erro=str(e), codigo="42501"), 403


def _select(cx, T, nome, corpo, u):
    extra = P.filtro_leitura(nome, T, u)
    if extra is None:
        return jsonify(erro="sem permissão de leitura", codigo="42501"), 403
    cond = and_(_where(T, corpo), extra)
    contagem = None
    if corpo.get("contar"):
        contagem = cx.execute(select(func.count()).select_from(T).where(cond)).scalar()
        if corpo.get("cabeca"):
            return jsonify(dados=None, contagem=contagem)
    q = select(*_colunas(T, corpo.get("colunas"))).where(cond)
    for o in corpo.get("ordem") or []:
        c = _col(T, o.get("c"))
        q = q.order_by(c.asc() if o.get("asc", True) else c.desc())
    if corpo.get("de") is not None and corpo.get("ate") is not None:
        de = max(0, int(corpo["de"]))
        q = q.offset(de).limit(max(0, int(corpo["ate"]) - de + 1))
    elif corpo.get("limite"):
        q = q.limit(min(int(corpo["limite"]), 100000))
    return jsonify(dados=_linhas(cx.execute(q)), contagem=contagem)


def _inserir(cx, T, nome, corpo, u, op):
    dados = corpo.get("dados")
    lista = dados if isinstance(dados, list) else [dados]
    conflito = [c.strip() for c in str(corpo.get("conflito") or "").split(",") if c.strip()]
    if op == "upsert" and not conflito:
        conflito = [c.name for c in T.primary_key.columns]
    saida = []
    for bruta in lista:
        linha = _limpar_linha(T, bruta)
        if nome == "dados_compartilhados":
            linha.setdefault("atualizado_em", datetime.now(timezone.utc))
        existente = None
        if op == "upsert" and conflito and all(k in linha for k in conflito):
            chave = and_(*[T.c[k] == linha[k] for k in conflito])
            existente = cx.execute(select(T).where(chave)).mappings().first()
            if existente is not None:
                if corpo.get("ignorarDuplicados"):
                    continue
                extra = P.filtro_escrita(nome, T, u, "update")
                if extra is None or not cx.execute(select(func.count()).select_from(T).where(and_(chave, extra))).scalar():
                    raise PermissionError("sem permissão para alterar este registro")
                linha = P.preparar_linha(nome, linha, u, "upsert")
                novos = {k: v for k, v in linha.items() if k not in conflito and not (nome == "anotacoes" and k == "dono")}
                if novos:
                    r = cx.execute(update(T).where(chave).values(**novos).returning(*T.c))
                    saida.extend(_linhas(r))
                _auditar(cx, u, nome, "UPDATE", "/".join(str(linha.get(k)) for k in conflito), nome == "dados_compartilhados" and linha.get("tipo") or "")
                continue
        linha = P.preparar_linha(nome, linha, u, "insert")
        q = pg_insert(T).values(**linha)
        if conflito and corpo.get("ignorarDuplicados"):
            q = q.on_conflict_do_nothing(index_elements=conflito)
        r = cx.execute(q.returning(*T.c))
        saida.extend(_linhas(r))
        _auditar(cx, u, nome, "INSERT", linha.get("tipo") or linha.get("id") or linha.get("email"), linha.get("nome") or linha.get("tipo") or "")
    return jsonify(dados=saida if corpo.get("retornar") else None)


def _alterar(cx, T, nome, corpo, u, op):
    if not corpo.get("filtros") and not corpo.get("ou"):
        raise Recusado("update/delete sem filtro não é permitido")
    extra = P.filtro_escrita(nome, T, u, op)
    if extra is None:
        raise PermissionError("sem permissão")
    cond = and_(_where(T, corpo), extra)
    if nome == "dados_compartilhados" and not eh_admin(u):
        tipos = [r[0] for r in cx.execute(select(T.c.tipo).where(cond)).all()]
        if any(not P.pode_gravar_doc(t, u) for t in tipos):
            raise PermissionError("sem permissão para este documento")
    if op == "delete":
        antes = _linhas(cx.execute(select(T).where(cond))) if nome in ("perfis", "departamentos") else None
        r = cx.execute(delete(T).where(cond).returning(*T.c))
        res = _linhas(r)
        for x in res:
            _auditar(cx, u, nome, "DELETE", x.get("tipo") or x.get("id"), x.get("nome") or x.get("tipo") or "", antes=(antes or [None])[0])
        return jsonify(dados=res if corpo.get("retornar") else None)
    linha = P.preparar_linha(nome, _limpar_linha(T, corpo.get("dados") or {}), u, "update")
    if nome == "anotacoes":
        linha.pop("dono", None)
    if not linha:
        return jsonify(dados=[])
    r = cx.execute(update(T).where(cond).values(**linha).returning(*T.c))
    res = _linhas(r)
    for x in res:
        _auditar(cx, u, nome, "UPDATE", x.get("tipo") or x.get("id"), ", ".join(sorted(linha.keys())), depois=json.loads(json.dumps({k: _json(v) for k, v in linha.items()})) if nome == "perfis" else None)
    return jsonify(dados=res if corpo.get("retornar") else None)
