"""Página do app, sessão, TOTVS (usuário de serviço), chat da equipe."""
import os
import re
from datetime import datetime, timedelta, timezone

import requests
from flask import Blueprint, Response, current_app, jsonify, redirect, request, send_from_directory, stream_with_context
from sqlalchemy import and_, delete, func, insert, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from . import config
from . import obras as OBR
from .db import engine, tabela
from .usuario import ativo, eh_admin, exige_login, perfil_id, tem_perm, usuario_atual

bp = Blueprint("app", __name__)
PASTA_APP = os.path.join(os.path.dirname(__file__), "static")


# ── Sessão (o adaptador da tela pergunta quem está logado) ──────────
@bp.get("/api/sessao")
def api_sessao():
    u = usuario_atual()
    if not u:
        return jsonify(sessao=None)
    if not u.get("permitido"):
        return jsonify(sessao=None, recusado=True, email=u.get("email"),
                       motivo="Esta conta não tem acesso (domínio ou grupo do Entra).")
    _religar_legado(u)
    return jsonify(sessao={
        "access_token": "sessao-servidor",
        "user": {"id": u["id"], "email": u["email"],
                 "app_metadata": {"provider": "azure"},
                 "user_metadata": {"name": u["nome"], "full_name": u["nome"]}},
    }, admin=eh_admin(u), ativo=ativo(u), admins_iniciais=config.ADMIN_EMAILS)


def _religar_legado(u):
    """Notas ligadas a um login anterior passam para a conta Microsoft no primeiro acesso."""
    p = u.get("perfil") or {}
    if not p.get("auth_legado"):
        return
    P, N = tabela("perfis"), tabela("anotacoes")
    with engine.begin() as cx:
        cx.execute(update(N).where(N.c.dono == p["auth_legado"]).values(dono=u["id"]))
        cx.execute(update(P).where(P.c.id == p["id"]).values(auth_legado=None, auth_user_id=u["id"]))
    p["auth_legado"] = None
    p["auth_user_id"] = u["id"]


@bp.get("/auth/v1/settings")
def auth_settings():
    # a tela consulta isto para saber quais formas de login existem
    return jsonify(external={"azure": True, "email": False}, disable_signup=True)


# ── TOTVS RM: o navegador chama /totvs/... e o servidor repassa com o usuário de serviço ──
_ROTA_TOTVS = re.compile(r"^api/framework/v1/(consultaSQLServer/RealizaConsulta/[A-Za-z0-9._\-]+/\d+/[A-Za-z]+|users)$")


def _consulta_permitida(rota):
    m = re.match(r"^api/framework/v1/consultaSQLServer/RealizaConsulta/([A-Za-z0-9._\-]+)/", rota)
    if not m:
        return rota == "api/framework/v1/users"
    padroes = [p.strip() for p in (os.getenv("TOTVS_CONSULTAS_PERMITIDAS", "CUBO.*") or "").split(",") if p.strip()]
    nome = m.group(1).upper()
    for p in padroes:
        rx = "^" + re.escape(p.upper()).replace(r"\*", ".*") + "$"
        if re.match(rx, nome):
            return True
    return False


def _colunas_coligada_configuradas():
    """Nomes de coluna de coligada que o administrador configurou em Consultas TOTVS."""
    try:
        T = tabela("dados_compartilhados")
        with engine.connect() as cx:
            r = cx.execute(select(T.c.dados).where(T.c.tipo == "param_consultas")).first()
        pc = (r[0] if r else None) or {}
        return tuple(str(((v or {}).get("colunas") or {}).get("COD") or "") for v in pc.values() if isinstance(v, dict))
    except Exception:
        return ()


@bp.get("/totvs/<path:rota>")
@exige_login
def totvs_proxy(rota):
    if not ativo():
        return jsonify(erro="perfil inativo"), 403
    if not config.TOTVS_BASE_URL or not config.TOTVS_USUARIO:
        return jsonify(erro="TOTVS não configurado no servidor (TOTVS_BASE_URL / rm_user / rm_senha)"), 503
    if not _ROTA_TOTVS.match(rota) or not _consulta_permitida(rota):
        return jsonify(erro="consulta do TOTVS não permitida"), 403
    liberadas = OBR.permitidas()
    params_txt = request.args.get("parameters", "")
    if not OBR.parametros_ok(params_txt, liberadas):
        return jsonify(erro="esta obra não está liberada para o seu perfil"), 403
    try:
        r = requests.get(config.TOTVS_BASE_URL + "/" + rota, params=request.args,
                         auth=(config.TOTVS_USUARIO, config.TOTVS_SENHA),
                         headers={"Accept": "application/json"}, timeout=config.TOTVS_TIMEOUT,
                         verify=config.TOTVS_VERIFICAR_SSL, stream=True)
    except requests.RequestException as e:
        return jsonify(erro="TOTVS indisponível: " + type(e).__name__), 502
    if r.status_code in (401, 403):
        # não repassa 401: a tela entenderia como "sua senha", mas a senha é a do usuário de serviço
        return jsonify(erro="o TOTVS recusou o usuário de serviço (rm_user)"), 502
    if liberadas is not None and r.status_code == 200:
        # pessoa com obras restritas: o servidor tira as linhas das outras obras antes de responder
        partes = rota.split("/")
        nome = partes[5] if len(partes) > 5 else ""
        corpo, _ = OBR.filtrar_resposta_rm(r.content, nome, params_txt, liberadas, _colunas_coligada_configuradas())
        return Response(corpo, status=200, content_type="application/json")
    return Response(stream_with_context(r.iter_content(64 * 1024)), status=r.status_code,
                    content_type=r.headers.get("Content-Type", "application/json"))


# ── Atualização automática do TOTVS (feita pelo servidor; a tela só carrega o resultado) ──
@bp.get("/api/arquivo/pz-totvs/<path:caminho>")
@exige_login
def totvs_arquivo(caminho):
    if not ativo():
        return jsonify(erro="perfil inativo"), 403
    if not re.match(r"^(raw/latest\.json|jobs/[0-9]+/[a-z]+/[A-Za-z0-9._\-]+\.json)$", caminho):
        return jsonify(erro="arquivo inválido"), 400
    A = tabela("totvs_arquivos")
    with engine.connect() as cx:
        r = cx.execute(select(A.c.dados).where(A.c.caminho == caminho)).first()
    if not r:
        return jsonify(erro="não encontrado"), 404
    liberadas = OBR.permitidas()
    if liberadas is not None and OBR.fonte_do_arquivo(caminho) not in OBR.FONTES_GLOBAIS and isinstance(r[0], list):
        return jsonify(OBR.filtrar_linhas(r[0], liberadas, _colunas_coligada_configuradas()))
    return jsonify(r[0])


@bp.post("/api/totvs/servidor")
@exige_login
def totvs_servidor():
    if not eh_admin():
        return jsonify(erro="só o administrador pede atualização ao servidor"), 403
    corpo = request.get_json(silent=True) or {}
    from .totvs_job import rodar_em_segundo_plano
    modo = corpo.get("modo") if corpo.get("modo") in ("rapido", "diario", "completo") else "completo"
    try:
        meses = min(6, max(1, int(corpo.get("meses") or 0)))
    except (TypeError, ValueError):
        meses = 0
    if not meses:
        from .agenda import normalizar
        T = tabela("dados_compartilhados")
        with engine.connect() as cx:
            r = cx.execute(select(T.c.dados).where(T.c.tipo == "param_totvs")).first()
        meses = normalizar(((r[0] if r else None) or {}).get("agenda"))["rapidaMeses"]
    rodar_em_segundo_plano(modo, meses, "pedido de " + (usuario_atual() or {}).get("email", "admin"))
    return jsonify(estado="iniciado")


# ── Chat da equipe (troca o canal em tempo real do serviço antigo) ──
def _canal_ok(nome):
    return bool(re.match(r"^[a-z0-9\-]{1,40}$", nome or ""))


@bp.get("/api/canal/<nome>")
@exige_login
def canal_ler(nome):
    if not _canal_ok(nome) or not ativo():
        return jsonify(erro="canal inválido"), 400
    u = usuario_atual()
    eu = perfil_id(u) or u["id"]
    E, Pz = tabela("canal_eventos"), tabela("canal_presenca")
    try:
        desde = max(0, int(request.args.get("desde") or 0))
    except ValueError:
        desde = 0
    limite = datetime.now(timezone.utc) - timedelta(minutes=config.CHAT_RETENCAO_MIN)
    with engine.begin() as cx:
        if request.args.get("inicio"):
            # primeira leitura: só devolve o último id (mensagens antigas não reaparecem)
            ultimo = cx.execute(select(func.coalesce(func.max(E.c.id), 0)).where(E.c.canal == nome)).scalar()
            eventos = []
        else:
            rows = cx.execute(select(E).where(and_(E.c.canal == nome, E.c.id > desde, E.c.criado_em > limite,
                                                    or_(E.c.para.is_(None), E.c.para == "", E.c.para == eu, E.c.de == eu)))
                              .order_by(E.c.id).limit(500)).mappings().all()
            eventos = [{"id": r["id"], "evento": r["evento"], "payload": r["payload"]} for r in rows]
            ultimo = max([desde] + [e["id"] for e in eventos])
        vivos = cx.execute(select(Pz).where(and_(Pz.c.canal == nome, Pz.c.visto_em > datetime.now(timezone.utc) - timedelta(seconds=90)))).mappings().all()
        cx.execute(delete(E).where(E.c.criado_em < limite))
    return jsonify(ultimo=ultimo, eventos=eventos, presenca={r["chave"]: [r["meta"]] for r in vivos})


@bp.post("/api/canal/<nome>/evento")
@exige_login
def canal_enviar(nome):
    if not _canal_ok(nome) or not ativo():
        return jsonify(erro="canal inválido"), 400
    u = usuario_atual()
    corpo = request.get_json(silent=True) or {}
    payload = corpo.get("payload") or {}
    if not isinstance(payload, dict) or len(str(payload)) > 4000:
        return jsonify(erro="mensagem inválida"), 400
    evento = str(corpo.get("evento") or "msg")[:30]
    if evento == "modo" and not eh_admin(u):
        return jsonify(erro="só o administrador muda o modo do chat"), 403
    eu = perfil_id(u) or u["id"]
    payload["de"] = eu                      # remetente vem da sessão, não da tela
    with engine.begin() as cx:
        cx.execute(insert(tabela("canal_eventos")).values(canal=nome, evento=evento, de=eu,
                                                          para=str(payload.get("para") or "")[:64], payload=payload))
    return jsonify(ok=True)


@bp.post("/api/canal/<nome>/presenca")
@exige_login
def canal_presenca(nome):
    if not _canal_ok(nome) or not ativo():
        return jsonify(erro="canal inválido"), 400
    u = usuario_atual()
    eu = perfil_id(u) or u["id"]
    meta = (request.get_json(silent=True) or {}).get("meta") or {}
    meta = {"nome": str(meta.get("nome") or "")[:60], "aba": str(meta.get("aba") or "")[:20], "em": meta.get("em")}
    Pz = tabela("canal_presenca")
    with engine.begin() as cx:
        if (request.get_json(silent=True) or {}).get("sair"):
            cx.execute(delete(Pz).where(and_(Pz.c.canal == nome, Pz.c.chave == eu)))
        else:
            q = pg_insert(Pz).values(canal=nome, chave=eu, meta=meta, visto_em=datetime.now(timezone.utc))
            cx.execute(q.on_conflict_do_update(index_elements=["canal", "chave"], set_={"meta": meta, "visto_em": datetime.now(timezone.utc)}))
    return jsonify(ok=True)


# ── Arquivos estáticos do app ───────────────────────────────────────
@bp.get("/<path:arquivo>")
def estatico(arquivo):
    permitidos = {"sw.js", "manifest.webmanifest", "icon-192.png", "icon-512.png", "icon-maskable-512.png",
                  "apple-touch-icon.png", "xlsx-0.20.3.full.min.js", "qrcode-1.4.4.js"}
    if arquivo not in permitidos:
        return jsonify(erro="não encontrado"), 404
    resp = send_from_directory(PASTA_APP, arquivo)
    if arquivo == "sw.js":
        resp.headers["Cache-Control"] = "no-cache"
    return resp


def pagina_inicial():
    resp = send_from_directory(PASTA_APP, "index.html")
    resp.headers["Cache-Control"] = "no-cache"
    return resp
