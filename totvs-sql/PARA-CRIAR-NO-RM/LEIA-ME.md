# Consultas para criar no RM

Para cada consulta: **Gestão › Consultas SQL › Incluir**, cole o arquivo, teste e salve com o código da tabela. Depois ligue no app em **Configurações › Consultas TOTVS** (código, **Testar e listar colunas**, **Salvar** e, nas consultas por obra, **Buscar**).

| # | Arquivo | Código | Sistema | Parâmetros | Para quê | Situação |
|---|---|---|---|---|---|---|
| 1 | `1-CUBO.SUP.OC (substituir).sql` | CUBO.SUP.OC | T | `DATAINI_D`, `DATAFIM_D` | OCs por item | criada |
| 2 | `2-CUBO.SUP.FORN (nova).sql` | CUBO.SUP.FORN | T | nenhum | cadastro de fornecedores | criada |
| 3 | `3-CUBO.SUP.OCDOC (nova).sql` | CUBO.SUP.OCDOC | T | `CODCOLIGADA_N`, `NUMEROMOV_S`, `CODTMV_S` | OC completa para o PDF | criada |
| 4 | `4-CUBO.SUP.CRONO (substituir).sql` | CUBO.SUP.CRONO | T | `CODCOLIGADA_N`, `IDPRJ_N` | necessidades de material com etapa (curva ABC) | **versão com etapas**, validada (35/4: 527 linhas) |
| 5 | `5-trecho para a CUBO.SUP.005 (alterar).sql` | (já feita na CUBO.SUP.SC) | | | data de aprovação da SC | feita |
| 6 | `6-CUBO.SUP.PROJ (nova).sql` | CUBO.SUP.PROJ | T | nenhum | lista de obras, orçado, revisões e endereço | validada |
| 7 | `7-CUBO.SUP.ORCETAPA (nova).sql` | CUBO.SUP.ORCETAPA | T | `CODCOLIGADA_N`, `IDPRJ_N` | orçamento por etapa (conferência; o app usa a ORCXCOMP) | validada (35/4: 441 linhas) |
| 8 | `8-CUBO.SUP.ORCXCOMP (nova).sql` | CUBO.SUP.ORCCOMP (nome usado no RM) | T | `CODCOLIGADA_N`, `IDPRJ_N` | orçado × solicitado × comprado × recebido por etapa | validada |
| 9 | `9-CUBO.SUP.SEMETAPA (nova).sql` | CUBO.SUP.SETAPA (nome usado no RM) | T | `CODCOLIGADA_N`, `IDPRJ_N` | compras da obra sem etapa (linha "Sem etapa") | conferida em 07/10/2026 (35/4: 13 linhas, R$ 1.887,48) |
| 10 | `10-CUBO.SUP.VERBAS (nova).sql` | CUBO.SUP.VERBAS | T | `CODCOLIGADA_N`, `IDPRJ_N` | verbas da obra: orçado, solicitado, OC a receber e realizado por tarefa (aba Verbas e saldo da verba na cotação) | **criar** |

Os parâmetros `CODCOLIGADA_N` e `IDPRJ_N` são do tipo **Inteiro**.

## Como testar

- **CUBO.SUP.PROJ.** Uma linha por projeto. Os projetos com `SUBSTITUIDO_POR_REVISAO = 1` o app ignora.
- **CUBO.SUP.ORCXCOMP.** Rode para 35/4 e compare com a tabela da seção 5 do handoff: total orçado R$ 85.125.853,18, comprado R$ 28.451.546,42.
- **CUBO.SUP.SEMETAPA.** Conferida com a `CONFERE.SEMETAPA` em 35/4: 13 linhas, R$ 1.887,48 (OC R$ 334,50 + NF R$ 1.552,98; a mesma compra aparece na OC e na NF).
- **CUBO.SUP.CRONO.** Rode para 35/4: 527 linhas, todas com `ETAPA` preenchida.

A `CUBO.SUP.ORC` antiga não é usada pelo app. **Não exclua** se a `CUBO.SUP.ORCCOMP` estiver dentro dela na árvore do RM.

## Códigos que o app usa (já vêm preenchidos)

| Campo no app | Código no RM | Sistema | Parâmetros |
|---|---|---|---|
| SC | CUBO.SUP.SC | T | `DATAEMISSAOINI`, `DATAEMISSAOFIM` |
| OC | CUBO.SUP.OC | T | `DATAINI_D`, `DATAFIM_D` (mês a mês) |
| Verbas | CUBO.SUP.VERBAS | T | `CODCOLIGADA_N`, `IDPRJ_N` |
| Insumos | CUBO.SUP.INS | T | nenhum |
| Fornecedores | CUBO.SUP.FORN | T | nenhum |
| OC para PDF | CUBO.SUP.OCDOC | T | `CODCOLIGADA_N`, `NUMEROMOV_S`, `CODTMV_S` |
| Curva ABC | CUBO.SUP.CRONO | T | `CODCOLIGADA_N`, `IDPRJ_N` |
| Obras e projetos | CUBO.SUP.PROJ | T | nenhum |
| Orçado × Comprado | CUBO.SUP.ORCCOMP | T | `CODCOLIGADA_N`, `IDPRJ_N` |
| Compras sem etapa | CUBO.SUP.SETAPA | T | `CODCOLIGADA_N`, `IDPRJ_N` |

Se algum código ou parâmetro for diferente no RM, ajuste em **Configurações › Consultas TOTVS**.

Libere todas para o **usuário de serviço** (enquanto ele não existir, para o seu usuário).
