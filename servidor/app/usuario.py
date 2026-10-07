"""Quem está usando o app: conta Microsoft (Entra) + perfil na tabela perfis."""
import uuid
from functools import wraps

from flask import current_app, g, jsonify
from sqlalchemy import func, or_, select

from . import config
from .db import engine, tabela


def _claims():
    auth = current_app.extensions.get("pz_auth")
    if auth is None:
        return None
    try:
        return auth.get_user()
    except Exception:
        return None


def _uuid(v):
    try:
        return str(uuid.UUID(str(v)))
    except Exception:
        return None


def usuario_atual():
    """Devolve o usuário da sessão (ou None). Calculado uma vez por requisição."""
    if "pz_usuario" in g:
        return g.pz_usuario
    c = _claims()
    u = None
    if c:
        email = str(c.get("preferred_username") or c.get("email") or c.get("upn") or "").lower()
        oid = _uuid(c.get("oid") or c.get("sub"))
        grupos = c.get("groups") or []
        dominio_ok = bool(email) and (not config.DOMINIO_PERMITIDO or email.endswith("@" + config.DOMINIO_PERMITIDO))
        grupo_ok = (not config.GRUPOS_ACESSO) or any(gid in grupos for gid in config.GRUPOS_ACESSO)
        u = {"id": oid, "email": email, "nome": c.get("name") or email.split("@")[0],
             "permitido": dominio_ok and grupo_ok and bool(oid), "perfil": None}
        if u["permitido"]:
            P = tabela("perfis")
            with engine.connect() as cx:
                row = cx.execute(select(P).where(or_(P.c.auth_user_id == oid, func.lower(P.c.email) == email))
                                 .order_by((P.c.auth_user_id == oid).desc()).limit(1)).mappings().first()
            u["perfil"] = dict(row) if row else None
    g.pz_usuario = u
    return u


def eh_admin(u=None):
    u = u if u is not None else usuario_atual()
    if not u or not u.get("permitido"):
        return False
    if u["email"] in config.ADMIN_EMAILS:
        return True
    p = u.get("perfil")
    return bool(p and p.get("is_admin") and p.get("ativo") is not False)


def ativo(u=None):
    u = u if u is not None else usuario_atual()
    if not u or not u.get("permitido"):
        return False
    if eh_admin(u):
        return True
    p = u.get("perfil")
    return bool(p and p.get("ativo") is not False)


def tem_perm(modulo, u=None):
    u = u if u is not None else usuario_atual()
    if eh_admin(u):
        return True
    if not ativo(u):
        return False
    perms = (u.get("perfil") or {}).get("permissoes")
    return perms is None or (isinstance(perms, list) and modulo in perms)


def perfil_id(u=None):
    u = u if u is not None else usuario_atual()
    p = (u or {}).get("perfil") or {}
    return str(p.get("id")) if p.get("id") else ""


def exige_login(f):
    """Para as rotas /api: sem sessão válida devolve 401 (a tela mostra o login)."""
    @wraps(f)
    def interno(*a, **k):
        u = usuario_atual()
        if not u:
            return jsonify(erro="login necessário"), 401
        if not u.get("permitido"):
            return jsonify(erro="conta sem acesso a este app"), 403
        return f(*a, **k)
    return interno
