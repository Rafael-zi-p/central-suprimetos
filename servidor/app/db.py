"""Conexão com o PostgreSQL (SQLAlchemy Core) e leitura das tabelas do schema do app."""
from sqlalchemy import MetaData, create_engine

from . import config

engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=int(__import__("os").getenv("DB_POOL", "5")),
    max_overflow=10,
    connect_args={"options": "-csearch_path=%s" % config.DB_SCHEMA},
)

# Tabelas que a tela pode consultar pela rota /api/db (qualquer outra é recusada)
TABELAS_APP = (
    "departamentos", "perfis", "dados_compartilhados", "sync_log", "item_anotacoes",
    "sc_prioridades", "pessoa_insumos", "sc_itens", "notificacoes", "anotacoes", "auditoria",
)

_meta = None


def meta():
    """Lê a estrutura das tabelas uma vez (colunas e chaves vêm do próprio banco)."""
    global _meta
    if _meta is None:
        m = MetaData(schema=config.DB_SCHEMA)
        m.reflect(bind=engine, only=list(TABELAS_APP) + ["canal_eventos", "canal_presenca", "totvs_arquivos"])
        _meta = m
    return _meta


def tabela(nome):
    if nome not in TABELAS_APP and nome not in ("canal_eventos", "canal_presenca", "totvs_arquivos"):
        return None
    return meta().tables.get("%s.%s" % (config.DB_SCHEMA, nome))
