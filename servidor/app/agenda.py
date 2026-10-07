"""Agenda da atualização automática do TOTVS, definida pelo administrador na tela
(Configurações › Integração TOTVS) e guardada em param_totvs.agenda.

Três tipos de atualização:
  rapido   — só SC e OC, dos últimos N meses (os meses anteriores são reaproveitados);
             roda de X em X minutos, nos dias e no horário de trabalho;
  diario   — tudo (inclui Verbas e Insumos), uma vez por dia;
  completo — tudo desde a data "Buscar desde", uma vez por semana.

A tarefa agendada do servidor (python -m app.totvs_job auto) roda a cada 5 minutos
e só executa quando esta agenda diz que está na hora. Sem dependência do resto do app.
"""
from datetime import datetime, timedelta

# dias: 0 = domingo ... 6 = sábado (mesma convenção da tela)
PADRAO = {"ativo": True, "rapidaMin": 15, "rapidaMeses": 2, "horaIni": "06:00", "horaFim": "20:00",
          "dias": [1, 2, 3, 4, 5, 6], "diariaHora": "05:00", "completaDia": 0, "completaHora": "04:00"}
INTERVALOS = (0, 15, 30, 60, 120, 240)   # 0 = rápida desligada


def _hm_ok(v, padrao):
    s = str(v or "").strip()
    try:
        h, m = s.split(":")
        h, m = int(h), int(m)
        if 0 <= h <= 23 and 0 <= m <= 59:
            return "%02d:%02d" % (h, m)
    except (ValueError, TypeError):
        pass
    return padrao


def _min(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def normalizar(a):
    """Agenda salva pela tela → agenda válida (o que vier errado volta ao padrão)."""
    a = a if isinstance(a, dict) else {}
    r = dict(PADRAO)
    r["ativo"] = bool(a.get("ativo", True))
    try:
        v = int(a.get("rapidaMin", PADRAO["rapidaMin"]))
        r["rapidaMin"] = v if v in INTERVALOS else PADRAO["rapidaMin"]
    except (TypeError, ValueError):
        pass
    try:
        r["rapidaMeses"] = min(6, max(1, int(a.get("rapidaMeses", PADRAO["rapidaMeses"]))))
    except (TypeError, ValueError):
        pass
    for k in ("horaIni", "horaFim", "diariaHora", "completaHora"):
        r[k] = _hm_ok(a.get(k), PADRAO[k])
    dias = a.get("dias")
    if isinstance(dias, list):
        ds = sorted({int(d) for d in dias if str(d).strip().isdigit() and 0 <= int(d) <= 6})
        r["dias"] = ds
    try:
        d = int(a.get("completaDia", PADRAO["completaDia"]))
        r["completaDia"] = d if 0 <= d <= 6 else PADRAO["completaDia"]
    except (TypeError, ValueError):
        pass
    return r


def _ult(estado, k):
    v = (estado or {}).get(k)
    if not v:
        return None
    try:
        return datetime.fromisoformat(str(v))
    except ValueError:
        return None


def devida(agenda, estado, agora):
    """Qual atualização está na hora ("completo", "diario", "rapido") ou None.

    agora: datetime com fuso (horário local da empresa). estado: últimas execuções
    {"rapida": iso, "diaria": iso, "completa": iso}, também com fuso.
    """
    a = normalizar(agenda)
    dow = (agora.weekday() + 1) % 7          # Python: segunda = 0 → 0 = domingo
    minuto = agora.hour * 60 + agora.minute
    hoje = agora.replace(second=0, microsecond=0)

    def slot(hm):
        return hoje.replace(hour=_min(hm) // 60, minute=_min(hm) % 60)

    uc, ud, ur = _ult(estado, "completa"), _ult(estado, "diaria"), _ult(estado, "rapida")

    def no_dia(u):
        return u is not None and u.astimezone(agora.tzinfo).date() == agora.date()

    if dow == a["completaDia"] and minuto >= _min(a["completaHora"]) and not no_dia(uc):
        return "completo"
    s = slot(a["diariaHora"])
    # a completa do dia já traz tudo: não repete a diária
    if minuto >= _min(a["diariaHora"]) and (ud is None or ud < s) and not no_dia(uc):
        return "diario"
    if a["ativo"] and a["rapidaMin"] > 0 and dow in a["dias"] and _min(a["horaIni"]) <= minuto <= _min(a["horaFim"]):
        if ur is None or (agora - ur) >= timedelta(minutes=a["rapidaMin"]) - timedelta(seconds=90):
            return "rapido"
    return None


def registrar(estado, modo, agora):
    """Marca a execução: a completa também vale como diária e rápida; a diária, como rápida."""
    e = dict(estado or {})
    iso = agora.isoformat()
    if modo == "completo":
        e["completa"] = e["diaria"] = e["rapida"] = iso
    elif modo == "diario":
        e["diaria"] = e["rapida"] = iso
    elif modo == "rapido":
        e["rapida"] = iso
    return e
