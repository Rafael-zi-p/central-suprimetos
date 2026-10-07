/* =========================================================
   CUBO.SUP.CRONO - Cronograma / curva A (versao com etapas)
   ---------------------------------------------------------
   Uma linha por NECESSIDADE DE MATERIAL do orcamento
   (MNECESSIDADEMAT): tarefa, ETAPA/SUBETAPA, insumo,
   quantidade, data de necessidade, preco orcado e a SC que
   atendeu (quando ja existe).

   Ajustes desta versao:
     - Linhas [verificar] resolvidas com as colunas reais da
       MTAREFA: hierarquia = IDPAI; datas = DATAINICIOPLAN /
       DATAFIMPLAN (com reserva na linha de base e no calculado).
     - Nome da tarefa vem de MTAREFA.NOME (DESCRICAO costuma
       vir vazia).
     - Etapa principal (IDPAI = IDTRF) e subetapa em cada linha:
       o app soma por etapa sem recalcular a arvore.
   Parametros: :CODCOLIGADA_N, :IDPRJ_N (Inteiros)
   ========================================================= */
WITH ARVORE AS (
    SELECT
        T.CODCOLIGADA, T.IDPRJ, T.IDTRF,
        1                                                   AS NIVEL,
        T.IDTRF                                             AS IDETAPA,
        CAST(T.CODTRF AS VARCHAR(60))                       AS CODETAPA,
        CAST(LTRIM(RTRIM(REPLACE(REPLACE(T.NOME, CHAR(13), ''),
             CHAR(10), ' '))) AS VARCHAR(255))              AS ETAPA,
        CAST(NULL AS INT)                                   AS IDSUBETAPA,
        CAST(NULL AS VARCHAR(60))                           AS CODSUBETAPA,
        CAST(NULL AS VARCHAR(255))                          AS SUBETAPA
    FROM MTAREFA T
    WHERE T.CODCOLIGADA = :CODCOLIGADA_N
      AND T.IDPRJ       = :IDPRJ_N
      AND T.IDPAI       = T.IDTRF

    UNION ALL

    SELECT
        F.CODCOLIGADA, F.IDPRJ, F.IDTRF,
        A.NIVEL + 1,
        A.IDETAPA,
        A.CODETAPA,
        A.ETAPA,
        CASE WHEN A.NIVEL = 1 THEN F.IDTRF ELSE A.IDSUBETAPA END,
        CASE WHEN A.NIVEL = 1 THEN CAST(F.CODTRF AS VARCHAR(60))
             ELSE A.CODSUBETAPA END,
        CASE WHEN A.NIVEL = 1
             THEN CAST(LTRIM(RTRIM(REPLACE(REPLACE(F.NOME, CHAR(13), ''),
                  CHAR(10), ' '))) AS VARCHAR(255))
             ELSE A.SUBETAPA END
    FROM MTAREFA F
    JOIN ARVORE A
      ON A.CODCOLIGADA = F.CODCOLIGADA
     AND A.IDPRJ       = F.IDPRJ
     AND A.IDTRF       = F.IDPAI
    WHERE F.IDTRF <> F.IDPAI
)
SELECT
    /* -- projeto, etapa e tarefa -- */
    N.CODCOLIGADA                                       AS CODCOLIGADA,
    N.IDPRJ                                             AS IDPRJ,
    AR.NIVEL                                            AS NIVEL_TAREFA,
    AR.IDETAPA                                          AS IDETAPA,
    AR.CODETAPA                                         AS CODETAPA,
    AR.ETAPA                                            AS ETAPA,
    AR.IDSUBETAPA                                       AS IDSUBETAPA,
    AR.CODSUBETAPA                                      AS CODSUBETAPA,
    AR.SUBETAPA                                         AS SUBETAPA,
    N.IDTRF                                             AS IDTRF,
    T.CODTRF                                            AS CODTRF,
    LTRIM(RTRIM(REPLACE(REPLACE(
        ISNULL(NULLIF(T.NOME, ''), T.DESCRICAO),
        CHAR(13), ''), CHAR(10), ' ')))                 AS DESCRICAO_TAREFA,
    T.IDPAI                                             AS IDTRFPAI,
    CONVERT(VARCHAR(10), COALESCE(T.DATAINICIOPLAN, T.DATAINICIOBASE,
                                  T.DATAINICIOCALC), 103) AS DATA_INICIO_TAREFA,
    CONVERT(VARCHAR(10), COALESCE(T.DATAFIMPLAN, T.DATAFIMBASE,
                                  T.DATAFIMCALC), 103)    AS DATA_FIM_TAREFA,

    /* -- insumo do orcamento e necessidade -- */
    N.IDNECESSIDADE                                     AS IDNECESSIDADE,
    M.CODISM                                            AS CODIGO_INSUMO,
    M.DESCISM                                           AS NOME_INSUMO,
    M.CODUND                                            AS UNIDADE,
    N.QTDENECESSIDADE                                   AS QUANTIDADE_NECESSIDADE,
    CONVERT(VARCHAR(10), N.DATANECESSIDADE, 103)        AS DATA_NECESSIDADE,
    N.PRECOORCADO                                       AS PRECO_ORCADO,
    CAST(ISNULL(N.QTDENECESSIDADE,0) * ISNULL(N.PRECOORCADO,0) AS DECIMAL(18,2))
                                                        AS VALOR_ORCADO,

    /* -- SC que atendeu a necessidade (o app cruza com a OC pela SC) -- */
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

LEFT JOIN ARVORE AR
       ON AR.CODCOLIGADA = N.CODCOLIGADA
      AND AR.IDPRJ       = N.IDPRJ
      AND AR.IDTRF       = N.IDTRF

LEFT JOIN MISM M (NOLOCK)
       ON M.CODCOLIGADA = N.CODCOLIGADA
      AND M.IDPRJ       = N.IDPRJ
      AND M.IDISM       = N.IDISM

/* SC que atendeu: UMA por necessidade (a primeira SC nao cancelada) */
OUTER APPLY (
    SELECT TOP 1 SC0.CODCOLIGADA, SC0.IDMOV, SC0.NUMEROMOV, SC0.CODTMV,
                 SC0.DATAEMISSAO, IPE.IDPRD
    FROM MITEMPEDIDOMATERIAL IPE (NOLOCK)
    JOIN TMOV SC0 (NOLOCK)
      ON SC0.CODCOLIGADA = IPE.CODCOLIGADA
     AND SC0.IDMOV       = IPE.IDMOV
     AND SC0.STATUS     <> 'C'
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
