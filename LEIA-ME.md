# Central de Suprimentos: entrega v3 para a TI

| | |
|---|---|
| **O quê** | App de gestão de suprimentos (SC → Mesa → Cotação → OC → recebimento, prazos SLA, avaliação de fornecedores, Curva 25, orçado × comprado) |
| **Onde roda** | No servidor da empresa: Flask + PostgreSQL + Redis + Microsoft Entra, publicado pelo Coolify (padrão da Plataforma de Automações) |
| **Dependências externas** | Só o TOTVS RM (pelo servidor, com usuário de serviço) e o login Microsoft da empresa |
| **Autoria** | Rafael Luís de Souza ([CREDITOS.md](CREDITOS.md)) |
| **Termo de uso** | Em minuta; a ser assinado pelas partes |
| **Data** | 07/10/2026 |

## Comece por aqui

1. **[ENTREGA-COMPLETA.md](ENTREGA-COMPLETA.md)**: arquitetura, instalação passo a passo, variáveis, agendamentos, segurança e homologação.
2. **[docs/01-regras-de-negocio.md](docs/01-regras-de-negocio.md)**: as regras que o app calcula.
3. **[docs/02-LGPD.md](docs/02-LGPD.md)**: inventário de dados pessoais e retenção.
4. **[docs/03-abas-o-que-cada-uma-precisa.md](docs/03-abas-o-que-cada-uma-precisa.md)**: aba por aba, de onde vêm os dados, o que configurar e como conferir.

**Quer ver funcionando antes de publicar?** Siga o [RODAR-NO-PC.md](RODAR-NO-PC.md): sobe tudo no próprio PC com Docker (localhost).

## Instalação em 6 passos (detalhes no ENTREGA-COMPLETA)

1. Banco: rodar `banco/00-usuario-do-app.sql` e depois `banco/01-estrutura.sql`.
2. Entra: registrar o app com a URL de retorno `https://<endereço>/getAToken`.
3. RM: criar o usuário de serviço só de leitura e liberar as consultas `CUBO.SUP.*`.
4. Coolify: novo recurso a partir da pasta `servidor/` (Dockerfile), com as variáveis do `servidor/.env.exemplo`.
5. Agendar `python -m app.totvs_job auto` a cada 5 minutos (`*/5 * * * *`). O ritmo (rápida de 15 em 15 minutos, diária e completa) é definido pelo administrador na tela.
6. Entrar com um e-mail de `ADMIN_EMAILS`, definir "Buscar desde" e rodar a primeira atualização completa.

**O app começa limpo:** os testes foram feitos em servidor local, com dados de teste, e não há nada a importar. A configuração inicial é feita na tela (ENTREGA-COMPLETA §4.6 e §4.8). LGPD em `docs/02-LGPD.md`.
