# Central de Suprimentos: entrega para a TI (v3, servidor da empresa)

**Para:** TI do Grupo Impper  
**Data:** 07/10/2026  
**Criação e desenvolvimento:** Rafael Luís de Souza (Suprimentos)

Esta pasta tem tudo para rodar a Central de Suprimentos **no servidor e no banco da empresa**, no mesmo padrão da Plataforma de Automações (`projeto-himpper`): Flask, PostgreSQL, Redis, login Microsoft Entra e publicação pelo Coolify.

O app não depende de nenhum serviço externo além do TOTVS RM e do login Microsoft da empresa.

---

## 1. O que muda em relação à versão de testes

| Versão de testes (servidor local) | Agora (esta entrega) |
|---|---|
| Banco de testes local | PostgreSQL da empresa, schema `suprimentos` |
| Login de teste, com e-mail e senha | Login **só** com a conta Microsoft da empresa (Entra), sessão no Redis |
| Servidor local de testes | Flask no Coolify, mesmo servidor da Plataforma |
| Cada pessoa digitava usuário e senha do RM | **Usuário de serviço** do RM, só no servidor; a senha nunca chega ao navegador |
| Atualização do TOTVS pela tela de cada pessoa | O **servidor atualiza sozinho** (agendado); a tela só carrega o resultado |
| Regras de acesso no banco de testes | As mesmas regras, conferidas **no servidor** a cada consulta |
| Chat do ambiente de testes | Chat pelo próprio servidor; mensagem privada só chega a quem deve |

As regras de negócio não mudaram: a tela é a mesma, com os mesmos números.

---

## 2. Como as peças se conversam

```
Navegador (tela do app, mesma de sempre)
   │  só fala com o próprio servidor (mesmo domínio, HTTPS)
   ▼
Flask "suprimentos" (Coolify)  ── login ──►  Microsoft Entra (OIDC, identity.flask)
   │  /api/db        consultas e gravações, com permissão conferida
   │  /api/sessao    quem está logado
   │  /api/canal     chat da equipe
   │  /totvs/...     consultas do RM pedidas pela tela (ex.: PDF da OC)
   │  /api/arquivo   resultado da atualização automática do TOTVS
   ├──► PostgreSQL "automacoes", schema "suprimentos"
   ├──► Redis (sessão, prefixo "suprimentos:")
   └──► TOTVS RM (REST RealizaConsulta) com o usuário de serviço
Tarefa agendada (Coolify): python -m app.totvs_job auto, a cada 5 minutos (segue a agenda do administrador)
```

Serviços de fora usados pela tela, só quando a função é usada:
- **BrasilAPI**: consulta pública de CNPJ.
- **cdnjs / jsdelivr**: leitor de PDF, leitura de texto em imagem (OCR) e Excel com formatação.
- **IA**: desligada até haver decisão (seção 9).

---

## 3. O que a TI precisa ter antes

1. **PostgreSQL 13 ou mais novo**: o mesmo da Plataforma, com um schema novo.
2. **Redis**: o mesmo da Plataforma, com prefixo próprio.
3. **Coolify**: um recurso novo a partir da pasta `servidor/`, que já tem Dockerfile.
4. **Registro de aplicativo no Microsoft Entra**: um novo, ou o da Plataforma com mais uma URL de retorno.
5. **Usuário de serviço no TOTVS RM**: só leitura, com acesso às consultas da seção 6.
6. **Endereço** com HTTPS, por exemplo `suprimentos.grupoimpper.com.br`.

---

## 4. Instalação passo a passo

> Para testar antes no próprio PC (localhost, com Docker), veja `RODAR-NO-PC.md`.

### 4.1 Banco

1. Rode `banco/00-usuario-do-app.sql` como administrador do PostgreSQL. Troque a senha do usuário `suprimentos_app`.
2. Rode `banco/01-estrutura.sql`. Ele cria as tabelas no schema `suprimentos` e pode ser repetido sem estragar nada.
3. Rode os comandos `grant` que estão no fim do `00-usuario-do-app.sql`, para as tabelas que acabaram de ser criadas.

O app usa só o schema `suprimentos`. Ele não lê nem grava nada da Plataforma.

### 4.2 Login Microsoft (Entra)

No portal do Azure, em **Microsoft Entra ID › Registros de aplicativo**:

1. Crie um novo registro ("Central de Suprimentos") ou use o da Plataforma.
2. Em **URI de redirecionamento (Web)**, informe `https://<endereço>/getAToken`.
3. Em **URL de logout de front-channel**, informe `https://<endereço>/logout`.
4. Crie um **segredo do cliente** e anote o valor. Ele vai para `CLIENT_SECRET`.
5. Em **Permissões de API**, adicione Microsoft Graph › `User.Read` (delegada).
6. Opcional, para limitar quem entra por grupo:
   - em **Configuração de token**, adicione a declaração **groups**;
   - informe os IDs dos grupos em `GRUPOS_ACESSO`.

A verificação em duas etapas fica a cargo do **Acesso Condicional** da empresa. O app não tem senha própria.

### 4.3 Usuário de serviço do TOTVS RM

- Crie um usuário **só de leitura**, com permissão de executar as consultas `CUBO.SUP.*` (lista na seção 6).
- Informe o usuário em `rm_user` e a senha em `rm_senha`, em Base64, como na Plataforma. Também é possível usar `TOTVS_SENHA` em texto.
- O servidor só aceita repassar ao RM as consultas que casam com `TOTVS_CONSULTAS_PERMITIDAS` (padrão: `CUBO.*`).

### 4.4 Coolify

1. Crie um novo recurso a partir do repositório da empresa, apontando para a pasta `servidor/`. O build usa o **Dockerfile**.
2. Cadastre as variáveis de ambiente. O modelo comentado está em `servidor/.env.exemplo`, e a lista vem na seção 5.
3. Use a **porta** 3000 e a **verificação de saúde** em `GET /saude` (testa o banco).
4. Configure o **domínio** com HTTPS. O servidor já confia no proxy do Coolify, para enxergar o endereço e o HTTPS corretos.
5. Faça o deploy e abra o endereço. Deve aparecer o login da Microsoft.

### 4.5 Atualização automática do TOTVS (tarefa agendada)

No Coolify, em **Scheduled Tasks** do recurso, cadastre **uma** tarefa:

| Quando | Comando |
|---|---|
| A cada 5 minutos (`*/5 * * * *`) | `python -m app.totvs_job auto` |

Ela só busca no RM quando a **agenda do administrador** diz que está na hora. A agenda fica em **Configurações › Integração TOTVS**, e o padrão é:

| Tipo | O que busca | Quando (padrão) |
|---|---|---|
| **Rápida** | só SC e OC dos últimos 2 meses (os meses anteriores são reaproveitados) | a cada **15 minutos**, de segunda a sábado, das 06:00 às 20:00 |
| **Diária** | tudo, inclusive Verbas e Insumos | todo dia às 05:00 |
| **Completa** | tudo desde a data "Buscar desde" | domingo às 04:00 |

O administrador muda intervalo (15 min, 30 min, 1 h, 2 h, 4 h ou desligada), meses, dias, horários da rápida e horários da diária e da completa. Não é preciso mexer no Coolify.

Como funciona:
- Só roda uma atualização por vez: há uma trava no banco. Se uma ainda estiver rodando, a próxima verificação tenta de novo.
- A rápida não busca Verbas nem Insumos, para não pesar no TOTVS; eles vêm na diária.
- Se o RM devolver vazio um mês que antes tinha dados, o servidor tenta de novo e, se continuar vazio, mantém os dados anteriores.
- **Quem está com o app aberto recebe os dados novos sozinho**: a tela confere a cada 2 minutos e carrega em silêncio só o que mudou. Ela espera se a pessoa estiver com uma janela aberta, digitando ou no Quadro de Cotação.
- O administrador também pode pedir pela tela: botão **Atualizar › Rodar agora** (rápida ou completa).
- A data **"Buscar desde"** é uma só, definida pelo administrador, e vale para SC e OC.
- Horário: `FUSO_HORARIO` (padrão `America/Sao_Paulo`).
- Para rodar à mão no container: `python -m app.totvs_job rapido`, `diario` ou `completo`.

### 4.6 Primeira entrada

1. Entre com uma conta listada em `ADMIN_EMAILS`. Essa pessoa já entra como administradora.
2. Em **Configurações › Consultas TOTVS**, confira os códigos das consultas e use **Testar e listar colunas**.
3. No botão **Atualizar** do topo, defina **Buscar desde (SC e OC)** e clique em **Rodar agora · completa**.
4. Em alguns minutos, use **Carregar a última atualização** e confira os números com o RM.
5. Em **Configurações › Usuários & Permissões**, marque os administradores no próprio app. A partir daí, `ADMIN_EMAILS` pode ficar só com quem precisa como reserva.

### 4.7 Dados iniciais

O app começa limpo: não há dados a importar. Os dados do TOTVS vêm da atualização automática, e a configuração da equipe é feita na tela (4.6 e 4.8).

### 4.8 Liberar para a equipe

- Quem entra pela primeira vez ganha um perfil automaticamente:
  - `PERFIL_NOVO_ATIVO=1`: o perfil já entra ativo;
  - `PERFIL_NOVO_PERMISSOES`: quais abas a pessoa vê de início. Vazio = nenhuma até o administrador liberar, como hoje.
- O administrador ajusta as abas e obras de cada pessoa em **Usuários & Permissões**.

Configuração inicial na tela, feita pelo administrador (o app começa limpo):

1. **Usuários & Permissões**: cadastre a equipe, marque os administradores, libere abas e obras.
2. **Obras**: contatos (GGO, GO, assistente, almoxarife), endereço de entrega, horário de recebimento, e-mail da NF-e e regras de segurança. O PDF e o e-mail da OC usam esses dados.
3. **Parâmetros**: coligadas e obras, prazos de SLA por categoria e janela de aprovação.
4. **Pré-Compras**: categorias de ticket.
5. **Reunião do CUBO**: carteira de insumos de cada comprador.

Os dados do TOTVS (SC, OC, verbas, insumos e fornecedores) vêm sozinhos da atualização automática.

O que cada aba precisa e como conferir cada uma: `docs/03-abas-o-que-cada-uma-precisa.md`.

---

## 5. Variáveis de ambiente

| Variável | Para quê | Exemplo |
|---|---|---|
| `SECRET_KEY` | assina a sessão | texto longo e aleatório |
| `SESSION_REDIS_URL` | Redis da sessão | `redis://…:6379/2` |
| `SESSION_KEY_PREFIX` | separa da Plataforma | `suprimentos:` |
| `SESSAO_MINUTOS` | duração da sessão | `480` |
| `DATABASE_URL` | PostgreSQL (como o Coolify entrega) | `postgresql://…/automacoes` |
| `DB_NAME` / `DB_SCHEMA` | banco e schema | `automacoes` / `suprimentos` |
| `AUTHORITY` | locatário do Entra | `https://login.microsoftonline.com/<id>` |
| `CLIENT_ID` / `CLIENT_SECRET` | registro do app no Entra | … |
| `REDIRECT_URI` | retorno do login | `https://<endereço>/getAToken` |
| `DOMINIO_PERMITIDO` | só contas deste domínio | `grupoimpper.com.br` |
| `GRUPOS_ACESSO` | IDs de grupos do Entra (opcional) | vazio = todo o domínio |
| `ADMIN_EMAILS` | administradores iniciais | e-mails separados por vírgula |
| `PERFIL_NOVO_ATIVO` / `PERFIL_NOVO_PERMISSOES` | perfil do primeiro acesso (vazio = sem abas até liberar) | `1` / `sc,mesa` |
| `TOTVS_BASE_URL` | endereço da API do RM | `https://…rm.cloudtotvs.com.br:8051` |
| `rm_user` / `rm_senha` | usuário de serviço (senha em Base64) | … |
| `TOTVS_CONSULTAS_PERMITIDAS` | consultas que o servidor aceita | `CUBO.*` |
| `FUSO_HORARIO` | fuso da agenda da atualização | `America/Sao_Paulo` |
| `TOTVS_CONSULTAS_GLOBAIS` | consultas do RM sem obra, que passam sem filtro por obra | `CUBO.SUP.FORN*,CUBO.SUP.INS*` |
| `TOTVS_VERIFICAR_SSL` / `TOTVS_TIMEOUT` | segurança e tempo da chamada | `1` / `600` |
| `CHAT_RETENCAO_MIN` | por quanto tempo as mensagens do chat ficam guardadas | `240` |
| `IA_PROVEDOR` e chaves | assistente com IA (deixe vazio) | vazio |
| `WEB_WORKERS` / `WEB_THREADS` / `WEB_TIMEOUT` | gunicorn | `3` / `4` / `660` |

Nenhum valor real vai no código nem no Git. O `.gitignore` já exclui o `.env`.

---

## 6. Consultas do TOTVS RM usadas

Todas ficam em `totvs-sql/`, com instruções em `totvs-sql/PARA-CRIAR-NO-RM/LEIA-ME.md`. Libere todas para o usuário de serviço.

| Código no RM | Para quê |
|---|---|
| `CUBO.SUP.SC` | itens de SC, com data de aprovação |
| `CUBO.SUP.OC` | OCs por item (aprovação, recebimento, notas) |
| `CUBO.SUP.OCDOC` | OC completa para o PDF |
| `CUBO.SUP.FORN` | cadastro de fornecedores |
| `CUBO.SUP.INS` | base de insumos |
| `CUBO.SUP.CRONO` | necessidades com etapa (curva ABC) |
| `CUBO.SUP.PROJ` | obras, orçamentos e revisões |
| `CUBO.SUP.ORCCOMP` | orçado × comprado por etapa |
| `CUBO.SUP.SETAPA` | compras sem etapa (conferida em 07/10/2026) |
| `CUBO.SUP.VERBAS` | verbas da obra: orçado, solicitado, OC a receber e realizado por tarefa |

---

## 7. Segurança: o que o servidor garante

- **Login**:
  - só contas Microsoft do domínio da empresa (e dos grupos, se configurado);
  - sessão em cookie `HttpOnly` + `Secure` + `SameSite=Lax`, guardada no Redis;
  - a sessão expira depois de `SESSAO_MINUTOS`.
- **Permissões** conferidas no servidor a cada consulta (`servidor/app/permissoes.py`), com as mesmas regras que o app tinha no banco antigo:
  - configurações da equipe: só o administrador;
  - documentos da Reunião do CUBO: só quem tem esse módulo;
  - notificações: cada pessoa só vê as suas;
  - anotações: privadas, a não ser que sejam compartilhadas;
  - auditoria: só o administrador lê.
- **Consultas ao banco**:
  - só as tabelas e colunas do app;
  - valores sempre como parâmetro (sem SQL montado com texto);
  - `update` e `delete` sem filtro são recusados.
- **Auditoria**: quem mudou perfis, departamentos, carteiras e documentos fica gravado na tabela `auditoria`.
- **Restrição por obra**: quando o administrador limita as obras de uma pessoa (permissões `obra:<coligada>` no perfil), o servidor tira as outras obras antes de responder:
  - no proxy do RM (linhas filtradas; pedir outra obra pelo parâmetro é recusado com 403);
  - nos arquivos da atualização automática;
  - na tabela `sc_itens`, e a cópia antiga `totvsp_*` (todas as obras) fica oculta;
  - consultas globais, sem obra (fornecedores e insumos), passam sem filtro (`TOTVS_CONSULTAS_GLOBAIS`).
- **TOTVS**: a senha fica só no servidor, e só passam as consultas permitidas. Credencial que alguém tente salvar nas configurações é apagada antes de gravar.
- **Chat**: o remetente vem da sessão, não da tela, e mensagem privada só é entregue ao remetente e ao destinatário. Antes ela chegava a todos os navegadores e era só escondida.
- **Cabeçalhos de segurança**: CSP, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy` e `Permissions-Policy`.
- O app **não tem** rota de depuração, senha no código nem anexo acessível pelo número.

Decisões que ficam com a TI:
- **App separado ou módulo da Plataforma**: esta versão está pronta para app separado, no mesmo banco, com schema próprio.
- **Usuário de serviço do RM**: um exclusivo ou o mesmo da Plataforma, sempre só leitura e só com as consultas `CUBO.SUP.*`.
- **Grupos de acesso** no Entra (`GRUPOS_ACESSO`), se o acesso não for para todo o domínio.
- **Assistente com IA**: vem desligado (seção 9).

Outros pontos:
- **LGPD**: o inventário de dados pessoais, a rotina de retenção e o encerramento do ambiente de testes estão em `docs/02-LGPD.md`. Faltam só as confirmações do encarregado (bases legais e prazos).
- **QR da OC**: hoje ele não autentica a OC, porque é só um resumo sem segredo.

---

## 8. Operação

- **Logs**: saída do gunicorn no Coolify (acessos e erros). A atualização do TOTVS grava a situação em **Configurações › Integração TOTVS**.
- **Backup**: o do PostgreSQL da TI, incluindo o schema `suprimentos`. Recomendação: diário, com retenção de 30 dias.
- **Nova versão da tela**: o autor entrega a pasta `servidor/app/static` já pronta para o servidor. A TI substitui a pasta e publica de novo no Coolify.
- **Saúde**: `GET /saude` responde `{"ok": true}` quando o servidor e o banco estão de pé.
- **Limpeza automática**: mensagens do chat somem depois de `CHAT_RETENCAO_MIN`, e arquivos antigos da atualização do TOTVS são apagados a cada execução.

---

## 9. Assistente com IA

Ele vem **desligado** (`IA_PROVEDOR` vazio). Antes de ligar, é preciso:
- contrato corporativo com o provedor (Anthropic ou OpenAI);
- política de uso de IA aprovada;
- decisão sobre mandar ou não o resumo de números.

O servidor já tem a rota `/api/ia`, com login, limite de perguntas por minuto e chave só no servidor. Detalhes em `docs/assistente-ia-LEIA-ME.md`.

---

## 10. Homologação (checklist)

| # | Teste | Esperado |
|---|---|---|
| 1 | Abrir o endereço sem estar logado | vai para o login da Microsoft |
| 2 | Entrar com conta de fora do domínio | acesso recusado |
| 3 | Entrar com conta do `ADMIN_EMAILS` | entra como administrador |
| 4 | Rodar a atualização completa | situação "concluído" e SC/OC/Verbas carregadas |
| 5 | Conferir 3 SCs e 3 OCs contra o RM | mesmos números, datas e situação |
| 6 | Pessoa sem o módulo CUBO tentando gravar a reunião | recusado pelo servidor |
| 7 | Chat: mensagem privada entre A e B | C não recebe |
| 8 | Ver a OC aprovada e gerar o PDF | PDF com QR e dados do RM |
| 9 | OC rejeitada no RM | aparece como REJEITADA, e o criador recebe aviso |
| 10 | Sair (menu › Sair) | volta ao login da Microsoft |
| 11 | Testes de aceite das regras | `testes-de-aceite/` (rodar no console do app) |

---

## 11. O que foi testado (07/10/2026)

O **servidor Flask desta pasta** foi executado de verdade, com o **PostgreSQL 18** e os scripts `banco/00` e `banco/01` aplicados como no passo 4.1 (o `01` rodou duas vezes sem erro). Só três partes foram simuladas, porque dependem do ambiente da empresa:
- o login Microsoft (escolha do usuário de teste);
- o Redis (sessão em memória);
- o RM (um RM falso, que confere o usuário de serviço).

| Teste | Resultado |
|---|---|
| Rotas e permissões: `servidor/testes/testar_api.py` | **71 de 71** |
| Restrição por obra: pessoa com uma obra liberada só recebe essa obra no proxy do RM, nos arquivos da atualização e em `sc_itens`; pedir outra obra é recusado; administrador e pessoa sem restrição veem tudo | OK |
| Login: domínio de fora recusado, administrador por `ADMIN_EMAILS`, primeiro acesso sem virar administrador | OK |
| Uma pessoa comum tentando se promover, gravar configuração ou gravar a Reunião do CUBO | recusado pelo servidor |
| Senha do TOTVS enviada nas configurações | removida antes de gravar |
| Filtros, contagem, ordem e paginação; tentativa de injeção no filtro | OK |
| Notificações e anotações (privadas e compartilhadas); auditoria gravada | OK |
| Chat: mensagem privada só para o destinatário; remetente vindo do servidor; presença | OK (corrigida a perda das primeiras mensagens de um chat vazio) |
| TOTVS pelo servidor: consulta permitida passa; fora de `CUBO.*` e rota estranha bloqueadas | OK |
| Atualização automática: SC e OC mês a mês desde a data do administrador, índice, arquivos e situação "concluído" | OK |
| Tela inteira servida pelo Flask: login, perfil, abas, chat e carga da atualização do servidor (7 arquivos baixados e processados) | OK, sem erros |

Ajuste feito durante o teste: o endereço do banco passa a indicar o driver `psycopg2`, porque o SQLAlchemy 2.1 mudou o padrão.

**O que só a homologação da TI testa:**
- o login real no Entra (registro do app, grupos, Acesso Condicional);
- o Redis real;
- o RM real com o usuário de serviço;
- o build da imagem no Coolify (não havia Docker nesta máquina).

Use a seção 10.

## 12. Conteúdo da pasta

```
ENTREGA-COMPLETA.md            este documento
LEIA-ME.md                     resumo de uma página
RODAR-NO-PC.md                 teste no próprio PC (Docker, localhost)
servidor/                      app Flask (Dockerfile, requirements, .env.exemplo, docker-compose.local.yml)
  app/static/                  a tela (index.html e arquivos), já no modo servidor
banco/                         00 usuário do app, 01 estrutura
totvs-sql/                     consultas do RM e diagnósticos
docs/                          regras de negócio, LGPD, guia das abas, integração TOTVS, assistente IA
testes-de-aceite/              casos das regras de negócio
servidor/testes/               testes do servidor usados antes da entrega
CREDITOS.md, TERCEIROS.md      autoria e componentes de terceiros
```
