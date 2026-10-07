/* =========================================================
   CUBO.SUP.CRONO — versão OTIMIZADA (Cronograma / curva A)
   ---------------------------------------------------------
   Uma linha por NECESSIDADE DE MATERIAL do orçamento do projeto
   (MNECESSIDADEMAT): tarefa, insumo, quantidade, data de
   necessidade, preço orçado e a SC que atendeu (quando já existe).

   Por que a versão anterior estava pesada:
     1. Não tinha WHERE. A planilha manda DATAINICIO/DATAFIM mês a
        mês, mas o SQL ignorava os parâmetros: CADA mês devolvia a
        base INTEIRA (todas as coligadas e projetos). Com 21 meses,
        a mesma base vinha 21 vezes.
     2. ORDER BY sobre o resultado inteiro (ordenar não é preciso:
        o app organiza sozinho).
     3. Seis junções a mais (OC, itens da OC, relação OC→NF, NF,
        itens da NF). Cada SC com várias OCs e cada OC com várias NFs
        multiplicava as linhas. O app JÁ TEM OC e recebimento pela
        CUBO.SUP.OC e cruza pela SC: aqui basta chegar até a SC.
     4. MTAREFA sem CODCOLIGADA na junção: o mesmo IDPRJ/IDTRF de
        outra coligada podia duplicar linhas.
     5. Item da SC casado só pelo produto, e necessidade com vários
        pedidos (atendimento parcial): a linha duplicava e somava o
        orçado duas vezes. Agora sai UMA linha por necessidade, com a
        primeira SC não cancelada (TOP 1).
     Faltava também (NOLOCK) e o descarte de SC cancelada.

   Parâmetros (o app chama uma vez por projeto de cada obra):
     :CODCOLIGADA_N   coligada (obra)
     :IDPRJ_N         id do projeto (o mesmo usado na CUBO7.12)

   Como cadastrar no RM:
     1. Gestão › Consultas SQL. Pode SUBSTITUIR o texto da
        CUBO.SUP.CRONO (sistema T) ou criar outra com este SQL.
     2. Execute para um projeto e confira.
     3. Se o RM acusar "nome de coluna inválido", comente (--) a
        linha marcada com [verificar] e avise: o app funciona sem ela.
     4. No app: Configurações › Consultas TOTVS › Orçamento e
        planejamento › código, Testar, Salvar.
   ========================================================= */

SELECT
    /* ── projeto e tarefa ── */
    N.CODCOLIGADA                                       AS CODCOLIGADA,
    N.IDPRJ                                             AS IDPRJ,
    N.IDTRF                                             AS IDTRF,
    T.CODTRF                                            AS CODTRF,
    T.DESCRICAO                                         AS DESCRICAO_TAREFA,
    -- T.IDTRFPAI                                       AS IDTRFPAI,            -- [verificar] hierarquia da tarefa
    -- CONVERT(VARCHAR(10), T.DATAINICIO, 103)          AS DATA_INICIO_TAREFA,  -- [verificar] início planejado
    -- CONVERT(VARCHAR(10), T.DATAFIM, 103)             AS DATA_FIM_TAREFA,     -- [verificar] fim planejado

    /* ── insumo do orçamento e necessidade ── */
    N.IDNECESSIDADE                                     AS IDNECESSIDADE,
    M.CODISM                                            AS CODIGO_INSUMO,
    M.DESCISM                                           AS NOME_INSUMO,
    M.CODUND                                            AS UNIDADE,
    N.QTDENECESSIDADE                                   AS QUANTIDADE_NECESSIDADE,
    CONVERT(VARCHAR(10), N.DATANECESSIDADE, 103)        AS DATA_NECESSIDADE,
    N.PRECOORCADO                                       AS PRECO_ORCADO,
    CAST(ISNULL(N.QTDENECESSIDADE,0) * ISNULL(N.PRECOORCADO,0) AS DECIMAL(18,2))
                                                        AS VALOR_ORCADO,

    /* ── SC que atendeu a necessidade (o app cruza com a OC pela SC) ── */
    SC.NUMEROMOV                                        AS NUMERO_SC,
    SC.CODTMV                                           AS CODTMV_SC,
    CONVERT(VARCHAR(10), SC.DATAEMISSAO, 103)           AS DATA_SC,
    ISC.NSEQITMMOV                                      AS ITEM_SC,
    P.CODIGOPRD                                         AS CODIGO_PRODUTO_SC,
    ISC.QUANTIDADEORIGINAL                              AS QUANTIDADE_SC,

    CASE WHEN SC.IDMOV IS NOT NULL THEN 'SC CRIADA' ELSE 'SEM SC' END
                                                        AS STATUS_COMPRA

FROM MNECESSIDADEMAT N (NOLOCK)

LEFT JOIN MTAREFA T (NOLOCK)
       ON T.CODCOLIGADA = N.CODCOLIGADA
      AND T.IDPRJ       = N.IDPRJ
      AND T.IDTRF       = N.IDTRF

LEFT JOIN MISM M (NOLOCK)
       ON M.CODCOLIGADA = N.CODCOLIGADA
      AND M.IDPRJ       = N.IDPRJ
      AND M.IDISM       = N.IDISM

/* SC que atendeu: UMA por necessidade (a primeira SC não cancelada).
   Uma necessidade pode ter vários pedidos (atendimento parcial); juntar tudo
   multiplicaria a linha e o VALOR_ORCADO. */
OUTER APPLY (
    SELECT TOP 1 SC0.CODCOLIGADA, SC0.IDMOV, SC0.NUMEROMOV, SC0.CODTMV, SC0.DATAEMISSAO, IPE.IDPRD
    FROM MITEMPEDIDOMATERIAL IPE (NOLOCK)
    JOIN TMOV SC0 (NOLOCK)
      ON SC0.CODCOLIGADA = IPE.CODCOLIGADA
     AND SC0.IDMOV       = IPE.IDMOV
     AND SC0.STATUS     <> 'C'                -- SC cancelada não conta
    WHERE IPE.CODCOLIGADA   = N.CODCOLIGADA
      AND IPE.IDPRJ         = N.IDPRJ
      AND IPE.IDNECESSIDADE = N.IDNECESSIDADE
    ORDER BY SC0.DATAEMISSAO, SC0.IDMOV
) SC

OUTER APPLY (
    SELECT TOP 1 I.NSEQITMMOV, I.IDPRD, I.QUANTIDADEORIGINAL
    FROM TITMMOV I (NOLOCK)
    WHERE I.CODCOLIGADA = SC.CODCOLIGADA
      AND I.IDMOV       = SC.IDMOV
      AND I.IDPRD       = SC.IDPRD
    ORDER BY I.NSEQITMMOV
) ISC

LEFT JOIN TPRODUTO P (NOLOCK)
       ON P.IDPRD = ISC.IDPRD

WHERE N.CODCOLIGADA = :CODCOLIGADA_N
  AND N.IDPRJ       = :IDPRJ_N
