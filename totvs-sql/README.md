# Consultas SQL do TOTVS RM

As consultas ficam **cadastradas no RM da empresa** (Gestão › Consultas SQL). O app as chama pela API REST. Catálogo completo, com parâmetros e colunas: [docs/04-integracao-totvs.md](../docs/04-integracao-totvs.md).

| Arquivo | Consulta | Para quê | Situação |
|---|---|---|---|
| `CUBO.SUP.OC-mes-a-mes.sql` | `CUBO.SUP.OC` | ordens de compra **por item**, com SC de origem, aprovações, recebimento e cancelamento; período por parâmetro (`:DATAINI_D`, `:DATAFIM_D`) | em uso |
| `CUBO.SUP.OC-otimizada.sql` | `CUBO.SUP.OC` (substitui a anterior) | mesma saída (77 colunas, mesma ordem), mais rápida: aprovação da SC buscada só para as SCs do mês, aprovação da OC uma vez por OC, sem junções repetidas | **validar e trocar**: comparar nº de linhas e soma de VALOR_TOTAL_ITEM com a versão anterior no mesmo mês |
| `SC-data-aprovacao.sql` | trecho para a `CUBO.SUP.005` | acrescenta `DATA_APROVACAO_SC` à consulta de SC | pronto; confirmar se já está no RM |
| `CUBO.SUP.FORN-fornecedores.sql` | `CUBO.SUP.FORN` | cadastro de fornecedores do RM (FCFO) para a aba Fornecedores; o app cruza com as OCs | **a cadastrar no RM** |
| `CUBO.SUP.OCDOC-pdf-da-oc.sql` | `CUBO.SUP.OCDOC` | dados de uma OC (obra, fornecedor, comprador, pagamento, itens, SC de origem) para o PDF de envio ao fornecedor | **a cadastrar no RM** |
| `CUBO.SUP.CRONO-otimizada.sql` | `CUBO.SUP.CRONO` (substitui a da planilha) | necessidades de material do orçamento por tarefa (data de necessidade, quantidade, preço orçado) e a SC que atendeu; uma chamada por projeto (`:CODCOLIGADA_N`, `:IDPRJ_N`) | **a cadastrar no RM**: base do Cronograma automático |
| `MAPA-orcamento-planejamento.sql` | `MAPA.ORC.PLAN` (sugestão) | lista as tabelas e colunas do módulo de Projetos e Obras, para escrever a consulta do Cronograma | **a executar**: é o 1º passo da pendência A1 |

**Consultas em uso que não estão nesta pasta:** `CUBO.SUP.005` (SC), `CUBO7.12` (Verbas) e `CUBO.SUP.INS` (Insumos). Estão no RM e a TI pode exportar o texto delas por lá.

**O app já está pronto para receber cada consulta:**
- Em Configurações › Consultas TOTVS, o painel **Situação das consultas** lista todas as consultas, com estes dados:
  - o código cadastrado;
  - o que cada uma alimenta;
  - o arquivo SQL correspondente;
  - a situação (aguardando código / configurada / testada).
- As fontes Fornecedores (`CUBO.SUP.FORN`), OC para PDF (`CUBO.SUP.OCDOC`) e Orçamento e planejamento (Cronograma) já têm mapa de colunas e parâmetros com os nomes sugeridos.
- Basta cadastrar o SQL no RM, informar o código, clicar em **Testar e listar colunas** e depois em **Salvar parametrização**.
- Se uma coluna vier com outro nome, aponte-a no mapa.
- A letra do sistema da consulta no RM (T, M…) também é configurável.

**Regras ao alterar uma consulta:**
- O app reconhece as colunas **pelo nome**. Renomear uma coluna exige ajustar o mapa em Configurações › Consultas TOTVS.
- Mantenha as datas como `dd/mm/aaaa` (CONVERT 103) na `CUBO.SUP.OC`, ou ajuste o mapeamento.
- Teste no RM antes de salvar, e depois use "Testar" na tela Consultas TOTVS do app, que mostra as colunas devolvidas.
