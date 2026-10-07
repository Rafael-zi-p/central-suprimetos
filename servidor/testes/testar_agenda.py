"""Testes da agenda da atualização automática (app/agenda.py). Não precisa de banco.

Rodar na pasta servidor/:  python testes/testar_agenda.py
"""
import os
import sys
from datetime import datetime, timedelta, timezone

# carrega só o módulo da agenda (sem subir o app nem pedir variáveis de ambiente)
import importlib.util  # noqa: E402
_esp = importlib.util.spec_from_file_location("agenda", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "agenda.py"))
AG = importlib.util.module_from_spec(_esp)
_esp.loader.exec_module(AG)

BR = timezone(timedelta(hours=-3))
OK, FALHA = [], []


def chk(nome, cond, extra=""):
    (OK if cond else FALHA).append(nome + ("" if cond else "  -> " + str(extra)))


def em(y, m, d, h, mi):
    return datetime(y, m, d, h, mi, tzinfo=BR)


A = {}                                  # agenda padrão: rápida 15 min, 06:00–20:00, seg–sáb; diária 05:00; completa domingo 04:00
SEG = (2026, 10, 5)                     # 05/10/2026 é segunda-feira
DOM = (2026, 10, 4)
E_HOJE = {"completa": em(*DOM, 4, 1).isoformat(), "diaria": em(*SEG, 5, 0).isoformat()}

chk("padrão: 15 min, 2 meses", AG.normalizar(A)["rapidaMin"] == 15 and AG.normalizar(A)["rapidaMeses"] == 2)
chk("segunda 05:02 sem diária hoje → diária", AG.devida(A, {"completa": E_HOJE["completa"]}, em(*SEG, 5, 2)) == "diario")
chk("segunda 05:40, diária feita, fora do horário → nada", AG.devida(A, E_HOJE, em(*SEG, 5, 40)) is None)
chk("segunda 06:00, nunca rodou rápida → rápida", AG.devida(A, E_HOJE, em(*SEG, 6, 0)) == "rapido")
e = AG.registrar(E_HOJE, "rapido", em(*SEG, 6, 0))
chk("06:10 (10 min depois) → nada", AG.devida(A, e, em(*SEG, 6, 10)) is None)
chk("06:15 (15 min depois) → rápida", AG.devida(A, e, em(*SEG, 6, 15)) == "rapido")
chk("06:14 (folga de 90 s do agendador) → rápida", AG.devida(A, e, em(*SEG, 6, 14)) == "rapido")
chk("20:30, depois do horário → nada", AG.devida(A, e, em(*SEG, 20, 30)) is None)
chk("domingo 04:05, sem completa → completa", AG.devida(A, {}, em(*DOM, 4, 5)) == "completo")
e = AG.registrar({}, "completo", em(*DOM, 4, 5))
chk("domingo 05:10, completa já feita → não repete a diária", AG.devida(A, e, em(*DOM, 5, 10)) is None)
chk("domingo 10:00 (fora dos dias da rápida) → nada", AG.devida(A, e, em(*DOM, 10, 0)) is None)
A2 = {"rapidaMin": 60, "rapidaMeses": 4, "horaIni": "07:30", "horaFim": "18:00", "dias": [1, 2, 3, 4, 5]}
e = AG.registrar(E_HOJE, "rapido", em(*SEG, 7, 30))
chk("agenda de 1 h: 08:00 → nada", AG.devida(A2, e, em(*SEG, 8, 0)) is None)
chk("agenda de 1 h: 08:30 → rápida", AG.devida(A2, e, em(*SEG, 8, 30)) == "rapido")
chk("sábado fora dos dias → nada", AG.devida(A2, {"diaria": em(2026, 10, 10, 5, 0).isoformat(), "completa": E_HOJE["completa"]}, em(2026, 10, 10, 9, 0)) is None)
chk("rápida desligada (0) → nada", AG.devida({"rapidaMin": 0}, E_HOJE, em(*SEG, 9, 0)) is None)
chk("valores errados voltam ao padrão", AG.normalizar({"rapidaMin": 7, "rapidaMeses": 99, "horaIni": "25:99", "completaDia": 9})
    == dict(AG.PADRAO, rapidaMeses=6))
r = AG.registrar({}, "diario", em(*SEG, 5, 0))
chk("a diária também conta como rápida", r.get("diaria") and r.get("rapida") == r.get("diaria") and not r.get("completa"))

print("PASSOU %d" % len(OK))
for x in OK:
    print("  ok  ", x)
print("FALHOU %d" % len(FALHA))
for x in FALHA:
    print("  XX  ", x)
sys.exit(1 if FALHA else 0)
