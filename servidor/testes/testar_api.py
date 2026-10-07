"""Testes do servidor real (porta 8143) com dois usuários simulados."""
import json, time, requests
B = "http://127.0.0.1:8143"
import psycopg2
_c = psycopg2.connect(host="127.0.0.1", port=54329, user="postgres", dbname="automacoes"); _c.autocommit = True
_c.cursor().execute("truncate suprimentos.perfis, suprimentos.departamentos, suprimentos.dados_compartilhados, suprimentos.notificacoes, suprimentos.anotacoes, suprimentos.auditoria, suprimentos.canal_eventos, suprimentos.canal_presenca, suprimentos.totvs_arquivos, suprimentos.sync_log, suprimentos.item_anotacoes, suprimentos.sc_itens cascade")
OK, FALHA = [], []


def chk(nome, cond, extra=""):
    (OK if cond else FALHA).append(nome + ("" if cond else "  -> " + str(extra)[:300]))


def sessao(email):
    s = requests.Session()
    r = s.get(B + "/?como=" + email)
    return s, r


def db(s, **q):
    r = s.post(B + "/api/db", json=q)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text


adm, r = sessao("rafael.souza@grupoimpper.com.br")
chk("página inicial (admin) 200 + html", r.status_code == 200 and "<html" in r.text.lower(), r.status_code)
chk("cabeçalho CSP", "Content-Security-Policy" in r.headers, r.headers)
chk("página sem serviço externo", "createClient" not in r.text)
chk("saude", requests.get(B + "/saude").json().get("ok") is True)
chk("sw.js servido", requests.get(B + "/sw.js").status_code == 200)
chk("arquivo fora da lista = 404", requests.get(B + "/config.py").status_code == 404)
chk("sem login /api/db = 401", requests.post(B + "/api/db", json={"tabela": "perfis"}).status_code == 401)
j = adm.get(B + "/api/sessao").json()
chk("sessao admin", j.get("admin") is True and j["sessao"]["user"]["email"] == "rafael.souza@grupoimpper.com.br", j)

fora, _ = sessao("alguem@gmail.com")
j = fora.get(B + "/api/sessao").json()
chk("domínio de fora recusado", j.get("sessao") is None and j.get("recusado"), j)
chk("domínio de fora sem /api/db (403)", db(fora, tabela="perfis")[0] == 403)

# admin cria o próprio perfil (como o app faz)
uid_adm = adm.get(B + "/api/sessao").json()["sessao"]["user"]["id"]
st, j = db(adm, tabela="perfis", op="insert", dados={"nome": "Rafael", "email": "rafael.souza@grupoimpper.com.br", "auth_user_id": uid_adm, "ativo": True, "permissoes": []}, retornar=True)
chk("admin insere perfil", st == 200 and j["dados"][0]["id"], j)

# pessoa comum: primeiro acesso cria o próprio perfil, sem virar admin
com, _ = sessao("joao.compras@grupoimpper.com.br")
uid_com = com.get(B + "/api/sessao").json()["sessao"]["user"]["id"]
st, j = db(com, tabela="perfis", op="insert", dados={"nome": "joao", "email": "joao.compras@grupoimpper.com.br", "auth_user_id": uid_com, "is_admin": True, "ativo": True, "permissoes": None}, retornar=True)
p_com = (j.get("dados") or [{}])[0] if isinstance(j, dict) else {}
chk("comum cria próprio perfil", st == 200, j)
chk("comum NÃO vira admin", p_com.get("is_admin") is False, p_com)
chk("permissões do 1º acesso = PERFIL_NOVO_PERMISSOES", p_com.get("permissoes") == ["sc", "mesa"], p_com)
st, j = db(com, tabela="perfis", op="insert", dados={"nome": "outro", "email": "outro@grupoimpper.com.br", "auth_user_id": uid_adm}, retornar=True)
chk("comum NÃO cria perfil de outro", st == 403, (st, j))
st, j = db(com, tabela="perfis", op="update", dados={"is_admin": True}, filtros=[{"c": "id", "op": "eq", "v": p_com.get("id")}])
chk("comum NÃO se promove a admin", st == 403, (st, j))
st, j = db(com, tabela="perfis", op="update", dados={"telefone": "17 99999"}, filtros=[{"c": "id", "op": "eq", "v": p_com.get("id")}], retornar=True)
chk("comum muda o próprio telefone", st == 200 and j["dados"] and j["dados"][0]["telefone"] == "17 99999", (st, j))

# documentos compartilhados
st, j = db(adm, tabela="dados_compartilhados", op="upsert", dados={"tipo": "param_totvs", "dados": {"dataIni_sc": "2026-08", "usuario": "x", "senha": "y", "consultaSC": "CUBO.SUP.SC", "consultaOC": "CUBO.SUP.OC"}, "total": 1}, conflito="tipo")
chk("admin grava param_totvs", st == 200, (st, j))
st, j = db(adm, tabela="dados_compartilhados", colunas="dados", filtros=[{"c": "tipo", "op": "eq", "v": "param_totvs"}])
d = j["dados"][0]["dados"]
chk("senha do TOTVS removida antes de gravar", "senha" not in d and "usuario" not in d and d.get("dataIni_sc") == "2026-08", d)
st, j = db(com, tabela="dados_compartilhados", op="upsert", dados={"tipo": "param_sla", "dados": {}}, conflito="tipo")
chk("comum NÃO grava configuração (param_*)", st == 403, (st, j))
st, j = db(com, tabela="dados_compartilhados", op="upsert", dados={"tipo": "pre_teste1", "dados": {"id": "teste1"}}, conflito="tipo")
chk("comum grava documento livre (pre_)", st == 200, (st, j))
st, j = db(com, tabela="dados_compartilhados", op="upsert", dados={"tipo": "cubo_resp", "dados": {}}, conflito="tipo")
chk("comum sem módulo cubo NÃO grava cubo_", st == 403, (st, j))
st, j = db(adm, tabela="dados_compartilhados", colunas="tipo", filtros=[{"c": "tipo", "op": "like", "v": "basep%", "neg": True}, {"c": "tipo", "op": "like", "v": "pre%"}], ordem=[{"c": "tipo", "asc": True}], de=0, ate=9)
chk("filtros not/like/ordem/range", st == 200 and [x["tipo"] for x in j["dados"]] == ["pre_teste1"], j)
st, j = db(adm, tabela="perfis", colunas="id", contar="exact", cabeca=True)
chk("contagem (head)", st == 200 and j.get("contagem") == 2, j)
st, j = db(adm, tabela="perfis", colunas="is_admin", ou="auth_user_id.eq.%s,email.eq.x" % uid_adm, limite=1)
chk("filtro or", st == 200 and len(j["dados"]) == 1, j)
chk("coluna inexistente recusada", db(adm, tabela="perfis", colunas="senha")[0] == 400)
chk("tabela inexistente recusada", db(adm, tabela="pg_user")[0] == 400)
chk("delete sem filtro recusado", db(adm, tabela="sync_log", op="delete")[0] == 400)
chk("injeção no filtro não quebra", db(adm, tabela="perfis", filtros=[{"c": "email", "op": "eq", "v": "x' or '1'='1"}])[1]["dados"] == [])

# notificações
st, j = db(adm, tabela="notificacoes", op="insert", dados={"destinatario_email": "joao.compras@grupoimpper.com.br", "titulo": "Oi", "criado_por": "falsificado"}, retornar=True)
chk("notificação: autor vem do servidor", st == 200 and j["dados"][0]["criado_por"] == "Rafael", j)
st, j = db(com, tabela="notificacoes")
chk("comum vê só as dele", st == 200 and len(j["dados"]) == 1, j)
st, j = db(adm, tabela="notificacoes", op="update", dados={"lida": True}, filtros=[{"c": "titulo", "op": "eq", "v": "Oi"}], retornar=True)
chk("admin edita qualquer notificação", st == 200, j)

# anotações privadas
st, j = db(com, tabela="anotacoes", op="upsert", dados={"id": "nt1", "compartilhada": False, "dados": {"id": "nt1"}}, conflito="id", retornar=True)
chk("comum cria anotação (dono = ele)", st == 200 and j["dados"][0]["dono"] == uid_com, j)
st, j = db(adm, tabela="anotacoes")
chk("admin não vê anotação privada de outro", st == 200 and j["dados"] == [], j)
st, j = db(adm, tabela="anotacoes", op="upsert", dados={"id": "nt1", "compartilhada": True, "dados": {"id": "nt1", "x": 1}}, conflito="id")
chk("admin altera anotação privada de outro? (admin pode)", st in (200, 403), (st, j))

# auditoria
st, j = db(adm, tabela="auditoria")
chk("auditoria registrou mudanças", st == 200 and len(j["dados"]) >= 3, len(j.get("dados", [])) if isinstance(j, dict) else j)
chk("comum não lê auditoria", db(com, tabela="auditoria")[0] == 403)

# chat
st = com.get(B + "/api/canal/pz-equipe?inicio=1").json()
chk("chat: entrar", "ultimo" in st, st)
com.post(B + "/api/canal/pz-equipe/presenca", json={"meta": {"nome": "Joao", "aba": "sc"}})
p_adm_id = db(adm, tabela="perfis", colunas="id", filtros=[{"c": "email", "op": "eq", "v": "rafael.souza@grupoimpper.com.br"}])[1]["dados"][0]["id"]
marca = adm.get(B + "/api/canal/pz-equipe?inicio=1").json()["ultimo"]
com.post(B + "/api/canal/pz-equipe/evento", json={"evento": "msg", "payload": {"txt": "publica", "de": "falso"}})
com.post(B + "/api/canal/pz-equipe/evento", json={"evento": "msg", "payload": {"txt": "privada p/ admin", "para": p_adm_id}})
com.post(B + "/api/canal/pz-equipe/evento", json={"evento": "msg", "payload": {"txt": "privada p/ outro", "para": "ninguem"}})
ev = adm.get(B + "/api/canal/pz-equipe?desde=%d" % marca).json()["eventos"]
txts = [e["payload"]["txt"] for e in ev]
chk("chat: admin recebe pública e privada dele, não a de outro", "publica" in txts and "privada p/ admin" in txts and "privada p/ outro" not in txts, txts)
chk("chat: remetente vem do servidor", all(e["payload"]["de"] == p_com.get("id") for e in ev), ev)
pres = adm.get(B + "/api/canal/pz-equipe?desde=1").json()["presenca"]
chk("chat: presença", p_com.get("id") in pres, pres)
chk("chat: comum não muda o modo", com.post(B + "/api/canal/pz-equipe/evento", json={"evento": "modo", "payload": {"modo": "privado"}}).status_code == 403)

# TOTVS proxy
r = com.get(B + "/totvs/api/framework/v1/consultaSQLServer/RealizaConsulta/CUBO.SUP.SC/0/T", params={"parameters": ";A=1"}, headers={"Authorization": "Basic eDp5"})
chk("TOTVS: proxy com usuário de serviço", r.status_code == 200 and r.json()[0]["NUMERO_SC"] == "000101", (r.status_code, r.text[:200]))
r = com.get(B + "/totvs/api/framework/v1/consultaSQLServer/RealizaConsulta/OUTRA.CONSULTA/0/T")
chk("TOTVS: consulta fora de CUBO.* bloqueada", r.status_code == 403, r.status_code)
r = com.get(B + "/totvs/api/framework/v1/qualquercoisa")
chk("TOTVS: rota não permitida bloqueada", r.status_code == 403, r.status_code)

# atualização automática (job) pedida pelo admin
chk("comum NÃO pede atualização ao servidor", com.post(B + "/api/totvs/servidor", json={"acao": "iniciar"}).status_code == 403)
r = adm.post(B + "/api/totvs/servidor", json={"acao": "iniciar", "modo": "completo"})
chk("admin pede atualização", r.status_code == 200, r.text)
man = None
for _ in range(40):
    time.sleep(1)
    rr = adm.get(B + "/api/arquivo/pz-totvs/raw/latest.json")
    if rr.status_code == 200:
        man = rr.json(); break
chk("job gerou o índice raw/latest.json", man is not None and "sc" in man.get("fontes", {}), man)
if man:
    sc = man["fontes"]["sc"]
    chk("job: SC mês a mês desde 2026-08 (3 meses)", [a["chave"] for a in sc["arquivos"]] == ["2026-08", "2026-09", "2026-10"], sc)
    arq = adm.get(B + "/api/arquivo/pz-totvs/" + sc["arquivos"][0]["arquivo"]).json()
    chk("job: arquivo com as linhas do RM", isinstance(arq, list) and arq and arq[0]["NUMERO_SC"] == "000101" and "2026-08-01" in arq[0]["PARAMS"], arq)
    st, j = db(adm, tabela="dados_compartilhados", colunas="dados", filtros=[{"c": "tipo", "op": "eq", "v": "totvs_servidor_status"}])
    chk("job: situação 'concluido'", j["dados"][0]["dados"]["estado"] == "concluido", j)
ch = requests.get("http://127.0.0.1:8150/__chamadas").json()
vb = [c for c in ch if c[0] == "CUBO.SUP.VERBAS"]
chk("job: Verbas pela CUBO.SUP.VERBAS, com CODCOLIGADA_N/IDPRJ_N e a lista padrão de projetos",
    len(vb) >= 20 and any(c[1] == ";CODCOLIGADA_N=48;IDPRJ_N=2" for c in vb), vb[:3])
chk("job: Insumos pela CUBO.SUP.INS", any(c[0] == "CUBO.SUP.INS" for c in ch), [c[0] for c in ch][:10])
chk("arquivo com caminho inválido recusado", adm.get(B + "/api/arquivo/pz-totvs/../../etc/passwd").status_code in (400, 404))

# ── restrição por obra, no servidor ──
uid_r = None
restr, _ = sessao("restrito@grupoimpper.com.br")
uid_r = restr.get(B + "/api/sessao").json()["sessao"]["user"]["id"]
st, j = db(adm, tabela="perfis", op="insert", dados={"nome": "Restrito", "email": "restrito@grupoimpper.com.br", "auth_user_id": uid_r, "ativo": True, "permissoes": ["sc", "obra:35"]}, retornar=True)
chk("admin cria perfil com obra restrita", st == 200, (st, j))
RM = B + "/totvs/api/framework/v1/consultaSQLServer/RealizaConsulta/"
r = restr.get(RM + "CUBO.SUP.SC/0/T", params={"parameters": ";A=1"})
cods = sorted(x["CODCOLIGADA"] for x in r.json()) if r.status_code == 200 else r.text
chk("obra restrita: proxy do RM só devolve a obra liberada", cods == [35], cods)
r = adm.get(RM + "CUBO.SUP.SC/0/T", params={"parameters": ";A=1"})
chk("admin continua vendo todas as obras no proxy", sorted(x["CODCOLIGADA"] for x in r.json()) == [35, 40], r.text[:200])
r = com.get(RM + "CUBO.SUP.SC/0/T", params={"parameters": ";A=1"})
chk("sem restrição: vê todas as obras no proxy", sorted(x["CODCOLIGADA"] for x in r.json()) == [35, 40], r.text[:200])
r = restr.get(RM + "CUBO.SUP.ORCPLAN/0/T", params={"parameters": ";CODCOLIGADA_N=40;IDPRJ_N=4"})
chk("obra restrita: pedir outra obra pelo parâmetro é recusado", r.status_code == 403, (r.status_code, r.text[:120]))
r = restr.get(RM + "CUBO.SUP.ORCPLAN/0/T", params={"parameters": ";CODCOLIGADA_N=35;IDPRJ_N=4"})
chk("obra restrita: a obra liberada pelo parâmetro passa", r.status_code == 200 and len(r.json()) == 1, (r.status_code, r.text[:120]))
r = restr.get(RM + "CUBO.SUP.ORCPLAN/0/T")
chk("obra restrita: consulta de obra sem coligada nem parâmetro vem vazia", r.status_code == 200 and r.json() == [], (r.status_code, r.text[:120]))
r = restr.get(RM + "CUBO.SUP.FORN/0/T")
chk("obra restrita: consulta global (fornecedores) passa", r.status_code == 200 and len(r.json()) == 1, (r.status_code, r.text[:120]))
if man:
    arq_r = restr.get(B + "/api/arquivo/pz-totvs/" + sc["arquivos"][0]["arquivo"]).json()
    chk("obra restrita: arquivo da atualização só tem a obra liberada", [x["CODCOLIGADA"] for x in arq_r] == [35], arq_r)
    arq_a = adm.get(B + "/api/arquivo/pz-totvs/" + sc["arquivos"][0]["arquivo"]).json()
    chk("admin vê o arquivo completo", sorted(x["CODCOLIGADA"] for x in arq_a) == [35, 40], arq_a)
    chk("obra restrita: índice da atualização continua acessível", restr.get(B + "/api/arquivo/pz-totvs/raw/latest.json").status_code == 200)
# tabela com obra no banco
st, j = db(adm, tabela="sc_itens", op="insert", dados=[{"item_uid": "t-35", "numero_sc": "1", "coligada": 35, "obra": "A"}, {"item_uid": "t-40", "numero_sc": "2", "coligada": 40, "obra": "B"}])
chk("admin grava sc_itens de duas obras", st == 200, (st, j))
st, j = db(restr, tabela="sc_itens", colunas="item_uid")
chk("obra restrita: sc_itens só da obra liberada", st == 200 and [x["item_uid"] for x in j["dados"]] == ["t-35"], (st, j))
st, j = db(com, tabela="sc_itens", colunas="item_uid")
chk("sem restrição: sc_itens de todas as obras", st == 200 and len(j["dados"]) == 2, (st, j))
st, j = db(restr, tabela="sc_itens", op="update", dados={"obra": "X"}, filtros=[{"c": "item_uid", "op": "eq", "v": "t-40"}], retornar=True)
chk("obra restrita: não altera item de outra obra", st == 200 and not j.get("dados"), (st, j))
st, j = db(adm, tabela="dados_compartilhados", op="upsert", dados={"tipo": "totvsp_sc_0", "dados": {"linhas": []}, "total": 1}, conflito="tipo")
st, j = db(restr, tabela="dados_compartilhados", colunas="tipo", filtros=[{"c": "tipo", "op": "like", "v": "totvsp_%"}])
chk("obra restrita: cópia antiga com todas as obras fica oculta", st == 200 and j["dados"] == [], (st, j))
st, j = db(com, tabela="dados_compartilhados", colunas="tipo", filtros=[{"c": "tipo", "op": "like", "v": "totvsp_%"}])
chk("sem restrição: cópia antiga visível", st == 200 and len(j["dados"]) == 1, (st, j))

print("PASSOU %d" % len(OK))
for x in OK: print("  ok  ", x)
print("FALHOU %d" % len(FALHA))
for x in FALHA: print("  XX  ", x)
