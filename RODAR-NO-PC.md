# Testar no próprio PC (localhost)

Para ver o app funcionando antes de publicar no Coolify. Sobe tudo no PC com **Docker**: banco PostgreSQL, Redis e o app, com o mesmo Dockerfile da produção. Não mexe em nenhum banco nem servidor da empresa.

## O que precisa

1. **Docker Desktop** instalado e aberto.
2. **Internet** no PC (o build baixa as bibliotecas do Python e uma do GitHub). Se a rede usar proxy, configure o proxy no Docker Desktop.
3. **Login Microsoft:** um registro de app no Entra com a URI de retorno **`http://localhost:3000/getAToken`** (tipo Web). Pode ser:
   - o registro novo da Central, com essa URI a mais; ou
   - um registro só de teste.
   
   O Entra aceita `http` só para `localhost`. Anote o ID do locatário, o ID do aplicativo e um segredo do cliente.
4. **TOTVS RM** (opcional para abrir o app, necessário para ver dados): o endereço da API do RM precisa abrir a partir do PC, e o usuário de serviço só de leitura com as consultas `CUBO.SUP.*`.

## Passo a passo

1. Descompacte a pasta e abra um terminal na pasta **`servidor/`**.
2. Copie o modelo de configuração:
   ```
   copy .env.local.exemplo .env.local
   ```
3. Abra o `.env.local` e preencha:
   - `SECRET_KEY`: qualquer texto longo;
   - `AUTHORITY`, `CLIENT_ID`, `CLIENT_SECRET`: do registro do Entra;
   - `ADMIN_EMAILS`: o seu e-mail da empresa (entra como administradora);
   - `TOTVS_BASE_URL`, `rm_user`, `rm_senha`: do RM (a senha em Base64, como na Plataforma, ou `TOTVS_SENHA` em texto).
4. Suba tudo:
   ```
   docker compose -f docker-compose.local.yml up --build
   ```
   A primeira vez demora alguns minutos (baixa as imagens e cria as tabelas).
5. Abra **http://localhost:3000**. Deve aparecer o login da Microsoft. Entre com o e-mail que está em `ADMIN_EMAILS`.
6. Para carregar os dados do RM:
   - no botão **Atualizar** do topo, defina **Buscar desde (SC e OC)**;
   - clique em **Rodar agora · completa**;
   - em alguns minutos, use **Carregar a última atualização**.

## Comandos úteis

| Para | Comando (na pasta `servidor/`) |
|---|---|
| Parar | `Ctrl+C` no terminal, ou `docker compose -f docker-compose.local.yml down` |
| Subir de novo | `docker compose -f docker-compose.local.yml up` |
| Rodar a atualização do RM pelo terminal | `docker compose -f docker-compose.local.yml exec app python -m app.totvs_job completo` |
| Ver se está de pé | abrir `http://localhost:3000/saude` (responde `{"ok": true}`) |
| Apagar tudo e começar do zero | `docker compose -f docker-compose.local.yml down -v` (apaga o banco de teste) |

## Se der problema

| Sintoma | O que ver |
|---|---|
| Erro no login da Microsoft sobre a URI de retorno | A URI `http://localhost:3000/getAToken` não está no registro do Entra |
| "Login Microsoft não configurado" no terminal | Falta `AUTHORITY`, `CLIENT_ID` ou `CLIENT_SECRET` no `.env.local` |
| Entra, mas volta para o login | Use `http://localhost:3000` (não `127.0.0.1`), igual à URI de retorno |
| "conta sem acesso a este app" | O e-mail não é do `DOMINIO_PERMITIDO` |
| Atualização do RM com erro | O PC não alcança o `TOTVS_BASE_URL`, ou o usuário de serviço está errado. A situação aparece em **Configurações › Integração TOTVS** |
| O build falha ao baixar pacotes | Proxy ou firewall da rede bloqueando o Docker |

## Diferenças para a produção

- No PC, o banco usa o usuário `postgres` e uma senha fixa de teste, e o cookie funciona sem HTTPS. Na produção, siga o `ENTREGA-COMPLETA.md` (usuário `suprimentos_app`, HTTPS e variáveis no Coolify).
- O `.env.local` tem segredos: não envie nem coloque no Git (ele já está no `.gitignore`).
