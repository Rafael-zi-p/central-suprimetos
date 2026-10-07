"""Configuração da Central de Suprimentos — tudo vem de variáveis de ambiente (Coolify / .env).

Nada de senha ou chave neste arquivo. Os nomes seguem o padrão da Plataforma de
Automações (AUTHORITY, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, DATABASE_URL,
SESSION_REDIS_URL), para a TI reaproveitar o que já tem.
"""
import base64
import os
from datetime import timedelta
from urllib.parse import quote_plus, urlsplit, urlunsplit

import redis
from dotenv import load_dotenv

load_dotenv(encoding="utf-8")


def _env(nome, padrao=None):
    v = os.getenv(nome)
    return v if v not in (None, "") else padrao


def _bool(nome, padrao=False):
    v = _env(nome)
    return padrao if v is None else str(v).strip().lower() in ("1", "true", "sim", "yes", "on")


def _b64_ou_texto(nome_b64, nome_txt):
    """Aceita a senha em Base64 (padrão da TI: rm_senha) ou em texto."""
    v = _env(nome_b64)
    if v:
        try:
            return base64.b64decode(v).decode("utf-8")
        except Exception:
            return v
    return _env(nome_txt, "")


# ── Flask / sessão ────────────────────────────────────────────────
SECRET_KEY = _env("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Defina SECRET_KEY no ambiente (texto longo e aleatório).")

_redis_url = _env("SESSION_REDIS_URL") or _env("REDIS_URL")
if not _redis_url:
    raise RuntimeError("Defina SESSION_REDIS_URL (ou REDIS_URL) no ambiente.")
SESSION_TYPE = "redis"
SESSION_REDIS = redis.from_url(_redis_url)
SESSION_USE_SIGNER = True
SESSION_PERMANENT = True
SESSION_KEY_PREFIX = _env("SESSION_KEY_PREFIX", "suprimentos:")
PERMANENT_SESSION_LIFETIME = timedelta(minutes=int(_env("SESSAO_MINUTOS", "480")))
SESSION_COOKIE_SECURE = _bool("COOKIE_SEGURO", True)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_NAME = _env("SESSION_COOKIE_NAME", "suprimentos_sessao")
PREFERRED_URL_SCHEME = "https"
MAX_CONTENT_LENGTH = int(_env("MAX_UPLOAD_MB", "60")) * 1024 * 1024

# ── Microsoft Entra (login) ───────────────────────────────────────
AUTHORITY = _env("AUTHORITY")          # https://login.microsoftonline.com/<tenant-id>
CLIENT_ID = _env("CLIENT_ID")
CLIENT_SECRET = _env("CLIENT_SECRET")
REDIRECT_URI = _env("REDIRECT_URI")    # https://suprimentos.grupoimpper.com.br/getAToken
DOMINIO_PERMITIDO = (_env("DOMINIO_PERMITIDO", "grupoimpper.com.br") or "").lower().lstrip("@")
# IDs de grupos do Entra que podem entrar (vazio = qualquer pessoa do domínio)
GRUPOS_ACESSO = [g.strip() for g in (_env("GRUPOS_ACESSO", "") or "").split(",") if g.strip()]
# e-mails que são administradores mesmo sem perfil marcado (arranque)
ADMIN_EMAILS = [e.strip().lower() for e in (_env("ADMIN_EMAILS", "") or "").split(",") if e.strip()]
# perfil criado no primeiro acesso: ativo? quais módulos? (vazio = todos, como hoje)
PERFIL_NOVO_ATIVO = _bool("PERFIL_NOVO_ATIVO", True)
PERFIL_NOVO_PERMISSOES = _env("PERFIL_NOVO_PERMISSOES", "")  # ex.: sc,mesa,oc · vazio = nenhuma aba até o admin liberar

# ── Banco (PostgreSQL) ────────────────────────────────────────────
DB_NAME = _env("DB_NAME", "automacoes")
DB_SCHEMA = _env("DB_SCHEMA", "suprimentos")


def _database_url():
    url = _env("DATABASE_URL")
    if url:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        p = urlsplit(url)
        return urlunsplit((p.scheme, p.netloc, "/" + DB_NAME, p.query, p.fragment))
    usuario = _env("us_banco") or _env("DB_USER")
    senha = _env("senha_banco") or _env("DB_PASSWORD")
    host = _env("DB_HOST")
    if not (usuario and senha and host):
        raise RuntimeError("Defina DATABASE_URL ou DB_HOST/DB_USER/DB_PASSWORD no ambiente.")
    return "postgresql://%s:%s@%s:%s/%s" % (quote_plus(usuario), quote_plus(senha), host, _env("DB_PORT", "5432"), DB_NAME)


DATABASE_URL = _database_url()
# driver fixo (psycopg2): o SQLAlchemy 2.1 mudou o padrão de "postgresql://" para outra biblioteca
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# ── TOTVS RM (usuário de serviço; o navegador nunca vê a senha) ───
TOTVS_BASE_URL = (_env("TOTVS_BASE_URL", "") or "").rstrip("/")   # ex.: https://servidor:8051
TOTVS_USUARIO = _env("rm_user") or _env("TOTVS_USUARIO", "")
TOTVS_SENHA = _b64_ou_texto("rm_senha", "TOTVS_SENHA")
TOTVS_VERIFICAR_SSL = _bool("TOTVS_VERIFICAR_SSL", True)
TOTVS_TIMEOUT = int(_env("TOTVS_TIMEOUT", "600"))
# fuso da agenda da atualização automática (horário de trabalho da empresa)
FUSO_HORARIO = _env("FUSO_HORARIO", "America/Sao_Paulo")
# consultas do RM que não pertencem a uma obra (fornecedores, insumos): passam sem filtro por obra
TOTVS_CONSULTAS_GLOBAIS = _env("TOTVS_CONSULTAS_GLOBAIS", "CUBO.SUP.FORN*,CUBO.SUP.INS*")

# ── Chat da equipe (sem serviço externo: mensagens pelo próprio banco) ──
CHAT_RETENCAO_MIN = int(_env("CHAT_RETENCAO_MIN", "240"))

# ── IA do assistente (opcional) ───────────────────────────────────
IA_PROVEDOR = (_env("IA_PROVEDOR", "") or "").lower()   # anthropic | openai | vazio = desligado
IA_LIMITE_MIN = int(_env("IA_LIMITE_MIN", "10"))
