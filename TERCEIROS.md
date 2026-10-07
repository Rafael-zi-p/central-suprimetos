# Componentes de terceiros

Todos são de código aberto e permitem uso comercial. Ao redistribuir, mantenha os avisos de licença de cada um. A licença Apache 2.0 pede que os arquivos LICENSE e NOTICE sejam mantidos.

## Tela (navegador)

| Componente | Versão | Uso no app | Licença | Como é carregado |
|---|---|---|---|---|
| SheetJS Community Edition (`xlsx`) | 0.20.3 | Ler e gerar planilhas Excel | Apache 2.0 | arquivo local `xlsx-0.20.3.full.min.js`, com SRI |
| xlsx-js-style | 1.2.0 | Excel com formatação (exportações) | Apache 2.0 | CDN jsDelivr, sob demanda |
| qrcode-generator (Kazuhiko Arase) | 1.4.4 | QR da OC | MIT | arquivo local `qrcode-1.4.4.js` |
| PDF.js (Mozilla) | 3.11.174 | Ler PDF de propostas de cotação | Apache 2.0 | CDN cdnjs, sob demanda, com SRI |
| Tesseract.js | 5.1.1 | Leitura de texto (OCR) em PDF digitalizado | Apache 2.0 | CDN jsDelivr, sob demanda, com SRI |
| Inter / JetBrains Mono | — | Fontes da interface | SIL Open Font License 1.1 | Google Fonts |

## Servidor (Python)

| Componente | Versão | Uso | Licença |
|---|---|---|---|
| Flask / Werkzeug | 3.0.3 | servidor web | BSD-3-Clause |
| Flask-Session | 0.8.0 | sessão no Redis | BSD-3-Clause |
| redis-py | 5.0.7 | conexão com o Redis | MIT |
| SQLAlchemy | 2.0.32 | acesso ao PostgreSQL | MIT |
| psycopg2-binary | 2.9.9 | driver do PostgreSQL | LGPL-3.0 com exceções (uso como biblioteca) |
| msal | 1.30.0 | login Microsoft | MIT |
| ms-identity-python (`identity.flask`) | commit 8345836 | login Microsoft no Flask (o mesmo da Plataforma) | MIT |
| requests | 2.32.3 | chamadas ao TOTVS e à IA | Apache 2.0 |
| python-dotenv | 1.0.1 | leitura do `.env` | BSD-3-Clause |
| gunicorn | 22.0.0 | servidor de produção | MIT |

## Serviços externos

| Serviço | Uso | Observação |
|---|---|---|
| TOTVS RM (API REST `RealizaConsulta`) | dados de SC, OC, verbas, insumos, obras | da empresa; acesso com o usuário de serviço |
| Microsoft Entra ID | login | da empresa |
| BrasilAPI (`brasilapi.com.br`) | consulta pública de CNPJ | gratuito, sem garantia de disponibilidade; há alternativa manual |
| Provedor de IA (Anthropic ou OpenAI) | assistente (opcional) | **desligado** até haver contrato e política de uso |

**SRI (Subresource Integrity):** os scripts externos têm o hash `sha384` fixado na tag. Para atualizar uma biblioteca, recalcule o hash, senão o navegador bloqueia o arquivo. Os domínios externos permitidos ficam na política de segurança (CSP), em `servidor/app/__init__.py`.

**Marca:** o logotipo e o nome Grupo Impper pertencem à empresa e só aparecem na versão de uso dela.
