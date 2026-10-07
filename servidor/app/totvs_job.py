"""Atualização automática do TOTVS no servidor (substitui a busca manual pela tela).

O servidor consulta o RM com o usuário de serviço, guarda as linhas brutas na
tabela totvs_arquivos e publica um índice ("raw/latest.json"). Ao abrir o app,
cada pessoa carrega esse índice e processa os dados com a mesma lógica de sempre.

Agendar no Coolify (Scheduled Tasks), dentro do container, UMA tarefa:
    python -m app.totvs_job auto       # a cada 5 minutos (*/5 * * * *)
Ela só executa quando a agenda do administrador diz que está na hora (app/agenda.py):
    rápida   — SC e OC dos últimos N meses, de X em X minutos no horário de trabalho;
    diária   — tudo, inclusive Verbas e Insumos;
    completa — tudo desde a data definida pelo administrador, uma vez por semana.
Também dá para rodar direto: python -m app.totvs_job rapido | diario | completo.
O administrador também pode pedir pela tela (Configurações › Integração TOTVS).

A data "desde" é a do administrador (param_totvs.dataIni_sc; vale para SC e OC).
"""
import json
import sys
import threading
import time
from datetime import date, datetime, timedelta, timezone

import requests
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from . import agenda as AG
from . import config
from .db import engine, tabela

MAX_TENTATIVAS = 3
MES_VAZIO_MIN = 20          # mês que tinha pelo menos isso e veio vazio: tenta de novo / mantém o anterior
TRAVA = 742001              # pg_advisory_lock: uma atualização por vez
ORDEM = ["sc", "oc", "ocitens", "verbas", "insumos"]
# projetos de orçamento (coligada, idprj) usados quando nenhum foi cadastrado em Configurações › Coligadas
# (mesma lista padrão da tela)
PROJETOS_VERBA_PADRAO = [(48, 2), (36, 10), (40, 11), (12, 11), (35, 8), (46, 4), (39, 17), (35, 4), (35, 10), (35, 12),
                         (39, 6), (9, 6), (7, 30), (7, 36), (52, 2), (52, 1), (7, 37), (36, 37), (36, 41), (44, 8),
                         (51, 1), (2, 3), (44, 3)]


def _hoje():
    return (datetime.now(timezone.utc) - timedelta(hours=3)).date()   # America/Sao_Paulo


def _doc(cx, tipo):
    T = tabela("dados_compartilhados")
    r = cx.execute(select(T.c.dados).where(T.c.tipo == tipo)).first()
    return (r[0] if r else None) or {}


def _gravar_doc(tipo, dados):
    T = tabela("dados_compartilhados")
    with engine.begin() as cx:
        q = pg_insert(T).values(tipo=tipo, dados=dados, total=1, atualizado_por="servidor", atualizado_em=datetime.now(timezone.utc))
        cx.execute(q.on_conflict_do_update(index_elements=["tipo"], set_={"dados": dados, "atualizado_por": "servidor", "atualizado_em": datetime.now(timezone.utc)}))


def _arquivo_ler(caminho):
    A = tabela("totvs_arquivos")
    with engine.connect() as cx:
        r = cx.execute(select(A.c.dados).where(A.c.caminho == caminho)).first()
    return r[0] if r else None


def _arquivo_gravar(caminho, dados, linhas):
    A = tabela("totvs_arquivos")
    with engine.begin() as cx:
        q = pg_insert(A).values(caminho=caminho, dados=dados, linhas=linhas, criado_em=datetime.now(timezone.utc))
        cx.execute(q.on_conflict_do_update(index_elements=["caminho"], set_={"dados": dados, "linhas": linhas, "criado_em": datetime.now(timezone.utc)}))


def _param(pc, fonte, chave, padrao):
    v = str(((pc.get(fonte) or {}).get("params") or {}).get(chave) or "").strip()
    return v or padrao


def _consultar(consulta, tipo, param):
    if not (config.TOTVS_BASE_URL and config.TOTVS_USUARIO):
        raise RuntimeError("SEM_LOGIN")
    url = "%s/api/framework/v1/consultaSQLServer/RealizaConsulta/%s/0/%s" % (config.TOTVS_BASE_URL, requests.utils.quote(consulta, safe=""), tipo)
    r = requests.get(url, params={"parameters": param} if param else None, auth=(config.TOTVS_USUARIO, config.TOTVS_SENHA),
                     headers={"Accept": "application/json"}, timeout=config.TOTVS_TIMEOUT, verify=config.TOTVS_VERIFICAR_SSL)
    if r.status_code in (401, 403):
        raise RuntimeError("AUTH")
    r.raise_for_status()
    j = r.json()
    if isinstance(j, list):
        return j
    if isinstance(j, dict) and isinstance(j.get("data"), list):
        return j["data"]
    return []


def _meses(inicio, hoje):
    m = date(inicio.year, inicio.month, 1)
    while m <= date(hoje.year, hoje.month, 1):
        prox = date(m.year + (m.month // 12), m.month % 12 + 1, 1)
        yield m, min(prox - timedelta(days=1), hoje)
        m = prox


def montar_tarefas(modo="completo", meses_rapido=3):
    with engine.connect() as cx:
        pt, pc, po = _doc(cx, "param_totvs"), _doc(cx, "param_consultas"), _doc(cx, "param_obras")
    desde = next((v for v in (pt.get("dataIni_sc"), pt.get("dataIni_oc"), pt.get("dataIni")) if v and len(str(v)) == 7), None) \
        or "%d-01" % _hoje().year
    consulta = {
        "sc": str(pt.get("consultaSC") or pt.get("consulta") or "CUBO.SUP.SC").strip(),
        "oc": str(pt.get("consultaOC") or "CUBO.SUP.OC").strip(),
        "ocitens": str(pt.get("consultaOcItens") or "").strip(),
        "verbas": str(pt.get("consultaVerbas") or "CUBO.SUP.VERBAS").strip(),
        "insumos": str(pt.get("consultaInsumos") or "CUBO.SUP.INS").strip(),
    }
    oc_itens = "SUP.OC" in consulta["oc"].upper() or pt.get("ocModo") != "antigo"
    fontes = [f for f in ORDEM if consulta[f] and not (f == "ocitens" and oc_itens)]
    if modo == "rapido":            # a rápida (de minutos em minutos) traz só SC e OC
        fontes = [f for f in fontes if f in ("sc", "oc", "ocitens")]
    hoje = _hoje()
    inicio = date(int(desde[:4]), int(desde[5:7]), 1)
    corte = date(hoje.year, hoje.month, 1)
    for _ in range(max(1, meses_rapido) - 1):
        corte = (corte - timedelta(days=1)).replace(day=1)
    tarefas = []
    for f in fontes:
        if f in ("sc", "ocitens") or (f == "oc" and oc_itens and pt.get("ocParam") != "unica"):
            if f == "sc":
                p_ini, p_fim = _param(pc, "sc", "ini", "DATAEMISSAOINI"), _param(pc, "sc", "fim", "DATAEMISSAOFIM")
            elif f == "oc":
                p_ini, p_fim = _param(pc, "oc", "ini", "DATAINI_D"), _param(pc, "oc", "fim", "DATAFIM_D")
            else:
                p_ini, p_fim = _param(pc, f, "ini", "DATAEMISSAO_OC_INI"), _param(pc, f, "fim", "DATAEMISSAO_OC_FIM")
            for ini, fim in _meses(inicio, hoje):
                tarefas.append({"fonte": f, "consulta": consulta[f], "tipo": "T", "chave": ini.isoformat()[:7],
                                "param": ";%s=%s;%s=%s" % (p_ini, ini.isoformat(), p_fim, fim.isoformat()),
                                "reaproveita": modo in ("rapido", "diario") and ini < corte})
        elif f == "oc":
            tarefas.append({"fonte": "oc", "consulta": consulta["oc"], "tipo": "T", "chave": "tudo", "param": ""})
        elif f == "verbas":
            p_col, p_prj = _param(pc, "verbas", "coligada", "CODCOLIGADA_N"), _param(pc, "verbas", "projeto", "IDPRJ_N")
            sistema = _param(pc, "verbas", "sistema", "T")
            pares = []
            for k, v in (po or {}).items():
                try:
                    col = int(k)
                except ValueError:
                    continue
                for prj in (v or {}).get("projetos") or []:
                    try:
                        pares.append((col, int(prj)))
                    except (TypeError, ValueError):
                        continue
            for col, prj in (pares or PROJETOS_VERBA_PADRAO):
                tarefas.append({"fonte": "verbas", "consulta": consulta["verbas"], "tipo": sistema, "chave": "%d|%d" % (col, prj),
                                "param": ";%s=%d;%s=%d" % (p_col, col, p_prj, prj), "col": col})
        elif f == "insumos":
            tarefas.append({"fonte": "insumos", "consulta": consulta["insumos"], "tipo": "T", "chave": "tudo", "param": ""})
    return desde, fontes, tarefas


def rodar(modo="completo", meses_rapido=3, origem="agendamento"):
    """Executa uma atualização completa. Devolve um resumo. Só uma por vez (trava no banco)."""
    with engine.connect() as trava:
        if not trava.execute(text("select pg_try_advisory_lock(:k)"), {"k": TRAVA}).scalar():
            return {"estado": "rodando", "aviso": "já existe uma atualização em andamento"}
        try:
            return _rodar(modo, meses_rapido, origem)
        finally:
            trava.execute(text("select pg_advisory_unlock(:k)"), {"k": TRAVA})


def _rodar(modo, meses_rapido, origem):
    job = str(int(time.time()))
    inicio = datetime.now(timezone.utc).isoformat()
    origem = "%s · %s" % (origem, {"rapido": "rápida, SC e OC (%d meses)" % meses_rapido, "diario": "diária (%d meses de SC e OC)" % meses_rapido}.get(modo, "completa"))
    try:
        desde, fontes, tarefas = montar_tarefas(modo, meses_rapido)
    except Exception as e:
        _gravar_doc("totvs_servidor_status", {"estado": "erro", "job": job, "iniciado_em": inicio, "erro": "Não montei a atualização: %s" % e})
        return {"estado": "erro"}
    anterior = _arquivo_ler("raw/latest.json") or {"fontes": {}}
    prev = lambda f, ch: next((a for a in ((anterior.get("fontes") or {}).get(f) or {}).get("arquivos", []) if a.get("chave") == ch), None)
    arquivos, erros, total = {}, [], len(tarefas)
    fonte_fora = set()   # consulta que deu erro: não insiste nos outros projetos da mesma fonte
    for i, t in enumerate(tarefas):
        if t["fonte"] in fonte_fora:
            p = prev(t["fonte"], t["chave"])
            if p:
                arquivos.setdefault(t["fonte"], []).append(dict(p, ordem=i))
            continue
        if t.get("reaproveita") and prev(t["fonte"], t["chave"]):
            arquivos.setdefault(t["fonte"], []).append(dict(prev(t["fonte"], t["chave"]), ordem=i))
            continue
        _gravar_doc("totvs_servidor_status", {"estado": "rodando", "job": job, "iniciado_em": inicio, "origem": origem,
                                              "feitas": i, "total": total, "fonte_atual": t["fonte"], "etapa": t["chave"], "erros": erros[-5:]})
        linhas, ok = None, False
        for tentativa in range(1, MAX_TENTATIVAS + 1):
            try:
                linhas = _consultar(t["consulta"], t["tipo"], t["param"])
                p = prev(t["fonte"], t["chave"])
                if not linhas and p and p.get("linhas", 0) >= MES_VAZIO_MIN and tentativa < MAX_TENTATIVAS:
                    time.sleep(5 * tentativa)
                    continue
                ok = True
                break
            except RuntimeError as e:
                if str(e) in ("AUTH", "SEM_LOGIN"):
                    msg = ("O TOTVS recusou o usuário de serviço (rm_user / rm_senha)." if str(e) == "AUTH"
                           else "Faltam TOTVS_BASE_URL, rm_user e rm_senha nas variáveis do servidor.")
                    _gravar_doc("totvs_servidor_status", {"estado": "erro", "job": job, "iniciado_em": inicio, "erro": msg})
                    return {"estado": "erro", "erro": msg}
                erro = str(e)
            except Exception as e:
                erro = "%s: %s" % (type(e).__name__, e)
            time.sleep(5 * tentativa)
        p = prev(t["fonte"], t["chave"])
        if not ok or (not linhas and p and p.get("linhas", 0) >= MES_VAZIO_MIN):
            erros.append("%s %s: %s" % (t["fonte"], t["chave"], "veio vazio; mantidos os dados anteriores" if ok else erro))
            if not ok and t["fonte"] == "verbas":
                fonte_fora.add("verbas")
                erros.append("verbas: consulta %s indisponível no RM; demais projetos pulados nesta execução" % t["consulta"])
            if p:
                arquivos.setdefault(t["fonte"], []).append(dict(p, ordem=i))
            continue
        if t["fonte"] == "verbas":
            linhas = [dict(r, __CODCOLIGADA=t["col"]) if isinstance(r, dict) else r for r in linhas]
        caminho = "jobs/%s/%s/%s.json" % (job, t["fonte"], "".join(c if c.isalnum() or c in "-." else "_" for c in t["chave"]))
        _arquivo_gravar(caminho, linhas, len(linhas))
        arquivos.setdefault(t["fonte"], []).append({"chave": t["chave"], "arquivo": caminho, "linhas": len(linhas), "ordem": i})
    agora = datetime.now(timezone.utc).isoformat()
    manifesto = {"job": job, "em": agora, "desde": desde, "fontes": dict(anterior.get("fontes") or {})}
    for f in fontes:
        arqs = sorted(arquivos.get(f, []), key=lambda a: a.get("ordem", 0))
        if arqs:
            manifesto["fontes"][f] = {"em": agora, "linhas": sum(a["linhas"] for a in arqs), "arquivos": arqs, "desde": desde}
    _arquivo_gravar("raw/latest.json", manifesto, 0)
    # limpa arquivos que nenhum índice usa mais
    usados = {a["arquivo"] for x in manifesto["fontes"].values() for a in (x or {}).get("arquivos", [])}
    A = tabela("totvs_arquivos")
    with engine.begin() as cx:
        cx.execute(A.delete().where(A.c.caminho.like("jobs/%")).where(A.c.caminho.notin_(list(usados) or [""])))
    _gravar_doc("totvs_servidor_status", {"estado": "concluido", "job": job, "iniciado_em": inicio, "concluido_em": agora, "origem": origem,
                                          "total": total, "linhas": {f: sum(a["linhas"] for a in arquivos.get(f, [])) for f in fontes},
                                          "erros": erros[-10:]})
    return {"estado": "concluido", "em": agora, "erros": erros}


def rodar_em_segundo_plano(modo, meses_rapido, origem):
    threading.Thread(target=rodar, args=(modo, meses_rapido, origem), daemon=True).start()


def _agora_local():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(config.FUSO_HORARIO))
    except Exception:
        return datetime.now(timezone(timedelta(hours=-3)))      # sem base de fusos: horário de Brasília


def auto():
    """Chamado pela tarefa agendada a cada 5 minutos: roda só o que a agenda manda."""
    with engine.connect() as cx:
        pt, estado = _doc(cx, "param_totvs"), _doc(cx, "totvs_servidor_agenda")
    agora = _agora_local()
    modo = AG.devida(pt.get("agenda"), estado, agora)
    if not modo:
        return {"estado": "nada a fazer", "agora": agora.isoformat()}
    meses = AG.normalizar(pt.get("agenda"))["rapidaMeses"]
    # marca antes de rodar: se a execução demorar, a próxima verificação não repete a mesma
    _gravar_doc("totvs_servidor_agenda", AG.registrar(estado, modo, agora))
    r = rodar(modo, meses, "agenda")
    if r.get("estado") == "rodando":      # já havia outra em andamento: desfaz a marca para tentar de novo
        _gravar_doc("totvs_servidor_agenda", estado)
    return r


if __name__ == "__main__":
    m = (sys.argv[1] if len(sys.argv) > 1 else "auto").lower()
    if m == "auto":
        print(json.dumps(auto(), ensure_ascii=False))
        sys.exit(0)
    modo = m if m in ("rapido", "diario", "completo") else "rapido"
    with engine.connect() as _cx:
        _meses = AG.normalizar(_doc(_cx, "param_totvs").get("agenda"))["rapidaMeses"]
    print(json.dumps(rodar(modo, _meses, "agendamento"), ensure_ascii=False))
