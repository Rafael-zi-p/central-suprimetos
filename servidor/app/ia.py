"""
Endpoint da IA do assistente da Central de Suprimentos.

O app manda POST /api/ia com JSON:
    { "pergunta": "...", "historico": [{"papel": "usuario"|"assistente", "texto": "..."}],
      "contexto": {...opcional, só números} }
e recebe:
    { "resposta": "..." }

A chave da IA fica SÓ aqui (variável de ambiente). O navegador nunca a vê.

Variáveis de ambiente:
    IA_PROVEDOR        anthropic | openai            (padrão: anthropic)
    ANTHROPIC_API_KEY  chave da Anthropic (Claude)
    ANTHROPIC_MODELO   padrão: claude-sonnet-5-5
    OPENAI_API_KEY     chave da OpenAI (ChatGPT)
    OPENAI_MODELO      padrão: gpt-4o-mini
    IA_LIMITE_MIN      perguntas por usuário por minuto (padrão: 10)

Registrado em app/__init__.py. Desligado enquanto IA_PROVEDOR estiver vazio.
"""
import os
import time
from collections import defaultdict, deque

import requests
from flask import Blueprint, jsonify, request

from .usuario import ativo, usuario_atual

bp_ia = Blueprint("ia", __name__)

SISTEMA = (
    "Você é o assistente da Central de Suprimentos de uma construtora. "
    "Responda em português do Brasil, de forma curta e direta, para compradores e equipes de obra. "
    "Use apenas os números enviados no contexto; se não tiver o dado, diga que não sabe e indique "
    "em qual aba do app procurar (SCs, Mesa de Compras, OCs, Cotação, Fornecedores, Curva 25, Orçado x Comprado). "
    "Nunca invente valores, prazos, fornecedores ou pessoas. Não informe atraso de entrega de fornecedor."
)

_janela = defaultdict(deque)


def _usuario():
    """Quem pergunta: a sessão Microsoft deste servidor (perfil ativo)."""
    u = usuario_atual()
    if not u or not u.get("permitido") or not ativo(u):
        return None
    return u["email"]


def _limite_ok(user):
    lim = int(os.environ.get("IA_LIMITE_MIN", "10"))
    q, agora = _janela[user], time.time()
    while q and agora - q[0] > 60:
        q.popleft()
    if len(q) >= lim:
        return False
    q.append(agora)
    return True


def _mensagens(corpo):
    msgs = []
    for h in (corpo.get("historico") or [])[-8:]:
        txt = str(h.get("texto") or "")[:600].strip()
        if txt:
            msgs.append({"role": "user" if h.get("papel") == "usuario" else "assistant", "content": txt})
    pergunta = str(corpo.get("pergunta") or "")[:1000].strip()
    ctx = corpo.get("contexto")
    if isinstance(ctx, dict) and ctx:
        pergunta = "Contexto (números do app): " + str(ctx)[:3000] + "\n\nPergunta: " + pergunta
    msgs.append({"role": "user", "content": pergunta})
    # a API da Anthropic exige começar pelo usuário e alternar papéis
    while msgs and msgs[0]["role"] != "user":
        msgs.pop(0)
    limpo = []
    for m in msgs:
        if limpo and limpo[-1]["role"] == m["role"]:
            limpo[-1]["content"] += "\n" + m["content"]
        else:
            limpo.append(m)
    return limpo


def _anthropic(msgs):
    r = requests.post("https://api.anthropic.com/v1/messages", timeout=40, headers={
        "x-api-key": os.environ["ANTHROPIC_API_KEY"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }, json={
        "model": os.environ.get("ANTHROPIC_MODELO", "claude-sonnet-5-5"),
        "max_tokens": 800,
        "system": SISTEMA,
        "messages": msgs,
    })
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text")


def _openai(msgs):
    r = requests.post("https://api.openai.com/v1/chat/completions", timeout=40, headers={
        "Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
        "Content-Type": "application/json",
    }, json={
        "model": os.environ.get("OPENAI_MODELO", "gpt-4o-mini"),
        "max_tokens": 800,
        "messages": [{"role": "system", "content": SISTEMA}] + msgs,
    })
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


@bp_ia.post("/api/ia")
def ia():
    if not os.environ.get("IA_PROVEDOR"):
        return jsonify(erro="IA não configurada neste servidor"), 503
    user = _usuario()
    if not user:
        return jsonify(erro="login necessário"), 401
    if not _limite_ok(user):
        return jsonify(erro="muitas perguntas seguidas"), 429
    corpo = request.get_json(silent=True) or {}
    if not str(corpo.get("pergunta") or "").strip():
        return jsonify(erro="pergunta vazia"), 400
    try:
        msgs = _mensagens(corpo)
        prov = os.environ.get("IA_PROVEDOR", "anthropic").lower()
        texto = _openai(msgs) if prov == "openai" else _anthropic(msgs)
    except KeyError:
        return jsonify(erro="chave da IA não configurada no servidor"), 500
    except requests.RequestException as e:
        return jsonify(erro="provedor indisponível: " + type(e).__name__), 502
    return jsonify(resposta=texto.strip())
