"""Roda o servidor REAL localmente, para teste (NÃO usar em produção).
Requer um PostgreSQL de teste na porta 54329 com os scripts de banco/ aplicados
e: pip install -r ../requirements.txt fakeredis

Substitui só o que não existe nesta máquina:
  - Redis -> fakeredis (sessão em memória)
  - login Microsoft (Entra) -> usuário simulado (?como=email troca o usuário)
  - TOTVS RM -> RM falso na porta 8150 (confere usuário/senha de serviço)
Banco: PostgreSQL real (embedded), porta 54329, usuário suprimentos_app.
"""
import base64, json, os, sys, threading, uuid
V3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # pasta servidor/
os.environ.update({
    "SECRET_KEY": "teste-local-" + "x" * 40,
    "SESSION_REDIS_URL": "redis://falso:6379/0",
    "DATABASE_URL": "postgresql://suprimentos_app:teste-local@127.0.0.1:54329/automacoes",
    "DB_SCHEMA": "suprimentos",
    "AUTHORITY": "https://login.microsoftonline.com/teste", "CLIENT_ID": "teste", "CLIENT_SECRET": "teste",
    "REDIRECT_URI": "http://localhost:8143/getAToken",
    "COOKIE_SEGURO": "0",
    "DOMINIO_PERMITIDO": "grupoimpper.com.br",
    "ADMIN_EMAILS": "rafael.souza@grupoimpper.com.br",
    "PERFIL_NOVO_PERMISSOES": "sc,mesa",
    "TOTVS_BASE_URL": "http://127.0.0.1:8150",
    "rm_user": "servico.rm", "rm_senha": base64.b64encode(b"senha-servico").decode(),
    "TOTVS_VERIFICAR_SSL": "0",
})
import fakeredis, redis
_fake = fakeredis.FakeRedis()
redis.from_url = lambda *a, **k: _fake

import identity.flask as idf
from flask import request, session, redirect


def _claims_de(email):
    oid = str(uuid.uuid5(uuid.NAMESPACE_DNS, email))
    return {"oid": oid, "preferred_username": email, "name": email.split("@")[0].replace(".", " ").title(), "groups": []}


class AuthFalso:
    def __init__(self, app, **kw):
        self.app = app
        @app.route("/getAToken")
        def _retorno():
            return redirect("/")

    def get_user(self):
        como = request.args.get("como")
        if como:
            session["usuario_teste"] = como
        email = session.get("usuario_teste") or request.headers.get("X-Teste-Usuario")
        return _claims_de(email) if email else None

    def login_required(self, scopes=None):
        def deco(f):
            def interno(*a, **k):
                u = self.get_user()
                if not u:
                    return "login Microsoft simulado: abra /?como=seu.email@grupoimpper.com.br", 401
                return f(*a, context={"user": u, "access_token": "x"}, **k)
            interno.__name__ = f.__name__
            return interno
        return deco

    def logout(self, url):
        session.clear()
        return redirect(url)


idf.Auth = AuthFalso

# ── RM falso ──
from flask import Flask, jsonify
rm = Flask("rm")
RM_CHAMADAS = []


@rm.get("/api/framework/v1/consultaSQLServer/RealizaConsulta/<consulta>/<int:z>/<tipo>")
def rm_consulta(consulta, z, tipo):
    au = request.authorization
    if not au or au.username != "servico.rm" or au.password != "senha-servico":
        return "nao autorizado", 401
    RM_CHAMADAS.append((consulta, request.args.get("parameters", "")))
    if consulta == "CUBO.SUP.SC":
        p = request.args.get("parameters", "")
        return jsonify([{"CODCOLIGADA": 35, "OBRA": "OBRA TESTE", "NUMERO_SC": "000101", "PRODUTO": "CIMENTO CP II", "QUANTIDADE": 10,
                         "UNIDADE": "SC", "DATA_EMISSAO_SC": "2026-10-01", "PARAMS": p},
                        {"CODCOLIGADA": 40, "OBRA": "OUTRA OBRA", "NUMERO_SC": "000202", "PRODUTO": "ACO CA-50", "QUANTIDADE": 5,
                         "UNIDADE": "BR", "DATA_EMISSAO_SC": "2026-10-02", "PARAMS": p}])
    if consulta == "CUBO.SUP.FORN":
        return jsonify([{"CNPJ": "00.000.000/0001-00", "FORNECEDOR": "FORNECEDOR GLOBAL"}])
    if consulta == "CUBO.SUP.ORCPLAN":   # linhas sem coligada: a obra vem no parâmetro
        return jsonify([{"IDTRF": 1, "NOME": "Tarefa", "PARAMS": request.args.get("parameters", "")}])
    if consulta == "CUBO.SUP.OC":
        return jsonify([])
    return jsonify([])


@rm.get("/__chamadas")
def rm_lista():
    return jsonify(RM_CHAMADAS)


threading.Thread(target=lambda: rm.run(port=8150, use_reloader=False), daemon=True).start()

sys.path.insert(0, V3)
from app import create_app
app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8143, use_reloader=False, threaded=True)
