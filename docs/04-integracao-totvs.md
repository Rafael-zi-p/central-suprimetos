> **Na v3 (servidor da empresa)** a conexão com o RM é feita só pelo servidor, com o usuário de serviço (`rm_user`/`rm_senha`), e a atualização é agendada no próprio servidor. Ninguém informa login do RM na tela, e o endereço `/totvs` é atendido pelo próprio servidor. Veja `ENTREGA-COMPLETA.md`, seções 4.3 e 4.5. O restante deste documento (consultas, colunas e parâmetros) continua valendo.

# 04 — Integração com o TOTVS RM

O app **não usa código do TOTVS**. Ele chama **consultas SQL cadastradas no próprio RM da empresa**, pela API REST do framework, e organiza o resultado.

## Chamada

```
GET {base}/api/framework/v1/consultaSQLServer/RealizaConsulta/{CODIGO}/0/{T|M}?parameters=;P1=valor;P2=valor
Authorization: Basic base64(usuario:senha)
Accept: application/json
```

- `{base}` é a URL do RM. No site publicado, use **`/totvs`**, o proxy do `_redirects`.
- `T` é usado nas consultas de SC, OC e insumos; `M`, na de verbas.
- **Login:** cada usuário usa o **próprio** usuário do RM. O login fica só no navegador dele, preso à conta do app, e **nunca** é gravado no banco. A função do servidor usa uma conta técnica, guardada em Secrets.
- **Tempo limite:** as buscas grandes são feitas **mês a mês**, para nenhuma chamada ao RM passar do tempo limite.

## Consultas usadas

Os códigos e os nomes dos parâmetros são configuráveis em **Configurações › Integração TOTVS** e **› Consultas TOTVS** (doc `param_consultas`). A tabela mostra os valores do ambiente atual.

| Fonte | Código no RM | Parâmetros | Uma linha por | SQL nesta entrega |
|---|---|---|---|---|
| SC | `CUBO.SUP.005` | `DATAEMISSAOINI`, `DATAEMISSAOFIM` (mês a mês) | item de SC | não (está no RM); trecho de aprovação em `totvs-sql/SC-data-aprovacao.sql` |
| OC | `CUBO.SUP.OC` | `DATAINI_D`, `DATAFIM_D` (mês a mês) | **item** de OC | **sim**: `totvs-sql/CUBO.SUP.OC-mes-a-mes.sql` |
| Verbas | `CUBO7.12` | `IDCOLIGADA`, `IDPROJETO` (uma chamada por projeto) | tarefa × recurso | não (está no RM) |
| Insumos | `CUBO.SUP.INS` | — | insumo | não (está no RM) |
| Mapa de tabelas | `MAPA.ORC.PLAN` (sugestão) | — | coluna de tabela | **sim**: `totvs-sql/MAPA-orcamento-planejamento.sql`. **Ainda não executada**: serve para escrever a consulta do Cronograma (pendência) |

> As consultas que estão só no RM (SC, Verbas, Insumos) podem ser exportadas pela própria TI no RM (Gestão › Consultas SQL). Esta entrega documenta as **colunas que o app espera** de cada uma.

**Verbas por projeto:** uma obra pode ter mais de um projeto no RM (construção, infraestrutura…). A lista de pares coligada × projeto fica em `TOTVS_PROJETOS_VERBA` / `TOTVS_PROJETOS_DEF`, extraída do TOTVS em 02/10/2026. Os valores são somados por (coligada, `CODTRF`).

## Colunas esperadas

- O app reconhece pelo **nome da coluna**. O padrão está entre parênteses.
- Qualquer coluna pode ser remapeada na tela Consultas TOTVS, sem mudar código (`PC_CAMPOS`).

**SC:**
- coligada (`CODCOLIGADA`), nº (`N° MOVIMENTO`), criação (`DATACRIACAO`), entrega (`DATAENTREGA`), status (`STATUS`);
- produto (`PRODUTO`), histórico (`HISTORICO`), comentário do item (`HISTORICOITEM`);
- quantidade (`QUANTIDADE`), unidade (`CODUND`), anexo (`ARQUIVOANEXO`);
- natureza orçamentária (`ORCAMENTO`), tarefa do orçamento (`TAREFA`), aprovação (`DATA_APROVACAO_SC`).
- **Filtros aplicados pelo app:** aprovação "Concluído confirmado", coligadas liberadas e tipos de movimento de SC.

**OC (`CUBO.SUP.OC`):**
- **Identificação:** `COD_OBRA`, `NUMERO_OC`, `ITEM_OC`, `CODTMV_OC`, `CODIGO_INSUMO`, `NOME_INSUMO`, `UNIDADE`.
- **Valores:** `QUANTIDADE_COMPRADA`, `PRECO_UNITARIO`, `VALOR_TOTAL_ITEM`.
- **SC de origem:** `NUMERO_SC`, `DATA_CRIACAO_SC`, `DATA_APROVACAO_SC`, `DATA_NECESSIDADE_SC`.
- **OC:** `DATA_CRIACAO_OC`, `DATA_EMISSAO_OC`, `DATA_APROVACAO_OC`, `SITUACAO_APROVACAO_OC`, `PRAZO_APROVACAO_SC_OC`, `OC_DENTRO_PRAZO`.
- **Entrega e recebimento:** `DATA_ENTREGA_ITEM`, `DATA_PRIMEIRO_RECEBIMENTO`, `QUANTIDADE_RECEBIDA`, `SALDO_A_RECEBER`, `SITUACAO_RECEBIMENTO`, `VALOR_RECEBIDO`.
- **Fornecedor e pagamento:** `FORNECEDOR`, `CNPJ_FORNECEDOR`, `CONDICAO_PAGAMENTO`, `FORMA_PAGAMENTO`.
- **Outros:** `GERADO_POR_OC`, `COD_CCUSTO`, `CENTRO_CUSTO`, `SITUACAO_CANCELAMENTO_OC`, `HISTORICO_OC`.
- **Datas** chegam como `dd/mm/aaaa`.

**Verbas (`CUBO7.12`):**
- coligada (`CODCOLIGADA`), código da tarefa (`CODTRF`), descrição (`DESCRIÇÃO TAREFA`), orçado (`VALOR ORÇADO`);
- hierarquia (`IDTRF`, `IDPAI`, `NIVEL`), grupo de custo (`DESCGRUPOCUSTO`), recurso (`RECURSO`);
- e os **campos brutos** usados no cálculo do saldo (ver [01-regras-de-negocio.md](01-regras-de-negocio.md), item 9).

**Insumos (`CUBO.SUP.INS`):**
- `CODIGO_INSUMO`, `NOME_INSUMO`, `UNIDADE`, `COD_NATUREZA_ORCAMENTARIA`, `NATUREZA_ORCAMENTARIA`;
- opcionais: `TIPO`, `INATIVO`.

## Cadeia de movimentos

- **SC:** tipos 1.1.01 a 1.1.06. O 1.1.06 é a SC de material/serviço AT, que conta como regularização.
- **OC:** só os tipos em que a SC é recebida (lista editável em Configurações › Tipos de movimento).
- **Vínculo SC → OC:** feito **por item**, pelas tabelas de relacionamento do RM (`TITMMOVRELAC`), dentro do `CUBO.SUP.OC`.

## Consultas que ainda faltam (pendências)

| Para quê | Situação |
|---|---|
| **Cronograma:** orçamento por item e data planejada da atividade | **Aguardando** o resultado do `MAPA-orcamento-planejamento.sql`, para identificar as tabelas do módulo de Projetos e Obras |
| Ficha completa do fornecedor | Aguardando o SQL de fornecedores |
| Data de aprovação na consulta de SC | Trecho pronto (`SC-data-aprovacao.sql`). Confirmar no RM se já foi incorporado à `CUBO.SUP.005`; sem ele o app usa a data da OC ou a estimativa pelo ciclo |
