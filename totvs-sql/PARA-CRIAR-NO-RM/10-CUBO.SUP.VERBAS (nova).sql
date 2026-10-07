/* ======================================================
   CUBO.SUP.VERBAS - Verbas do orcamento da obra (aba Verbas e
                     saldo da verba no Quadro de Cotacao)
   Parametros: CODCOLIGADA_N (Inteiro), IDPRJ_N (Inteiro)
   Sistema: T (o mesmo das outras consultas CUBO.SUP)
   ------------------------------------------------------
   Uma linha por tarefa do orcamento (MTAREFA), com a mesma
   arvore e a mesma ligacao compra -> tarefa da CUBO.SUP.ORCXCOMP
   (rateio TITMMOVRATCCU; sem rateio, a tarefa do proprio item).
   Valores ACUMULADOS na linha (a tarefa-mae ja soma as filhas).

   Colunas com os nomes que o app le:
     VALOR ORÇADO        = valor total orcado da tarefa
     SOLICITAÇÃO_VALOR   = solicitado em SC
     PEDIDO_VALOR        = OC ainda a receber (vira "Saldo OC")
     REALIZADO_VALOR     = recebido em NF, menos devolucoes
   O app calcula:
     Comprometido = Saldo OC (+ saldo de contrato, se existir)
     Saldo        = Orcado - Realizado - Comprometido

   Mesma classificacao de tipos da CUBO.SUP.ORCXCOMP:
     SC  : 1.1.01, 1.1.02, 1.1.03, 1.1.04, 1.1.06
     OC  : 1.1.10, 1.1.11, 1.1.12, 1.1.13, 1.1.14, 1.1.18, 1.1.19,
           1.1.33, 1.1.34
     NF  : 1.2.xx, exceto adiantamentos, lucros, aporte, mutuo,
           impostos a compensar, investimento, reembolso e remessa futura
     DEV : 2.2.01 (abate do recebido)
   Movimentos cancelados (STATUS = 'C') ficam fora.

   Como testar: rode para 35/4. O total de VALOR ORÇADO nas
   linhas NIVEL = 1 deve bater com o total orcado da ORCXCOMP
   (R$ 85.125.853,18 em 07/10/2026).
   ====================================================== */
WITH ARVORE AS (
    SELECT T.CODCOLIGADA, T.IDPRJ, T.IDTRF, 1 AS NIVEL
    FROM MTAREFA T
    WHERE T.CODCOLIGADA = :CODCOLIGADA_N
      AND T.IDPRJ       = :IDPRJ_N
      AND T.IDPAI       = T.IDTRF

    UNION ALL

    SELECT F.CODCOLIGADA, F.IDPRJ, F.IDTRF, A.NIVEL + 1
    FROM MTAREFA F
    JOIN ARVORE A
      ON A.CODCOLIGADA = F.CODCOLIGADA
     AND A.IDPRJ       = F.IDPRJ
     AND A.IDTRF       = F.IDPAI
    WHERE F.IDTRF <> F.IDPAI
),
/* cada tarefa ligada a si mesma e a todas as tarefas abaixo dela */
FECHO AS (
    SELECT T.IDTRF AS IDANC, T.IDTRF AS IDDESC
    FROM MTAREFA T
    WHERE T.CODCOLIGADA = :CODCOLIGADA_N
      AND T.IDPRJ       = :IDPRJ_N

    UNION ALL

    SELECT C.IDANC, F.IDTRF
    FROM FECHO C
    JOIN MTAREFA F
      ON F.CODCOLIGADA = :CODCOLIGADA_N
     AND F.IDPRJ       = :IDPRJ_N
     AND F.IDPAI       = C.IDDESC
    WHERE F.IDTRF <> F.IDPAI
),
/* valores de compra por tarefa (sem acumular) */
MOVS AS (
    SELECT
        X.IDTRF,
        SUM(CASE WHEN X.GRUPO = 'SC'  THEN X.VALOR ELSE 0 END)                AS SOLICITADO,
        SUM(CASE WHEN X.GRUPO = 'OC'  THEN X.VALOR * X.FATOR_PEND ELSE 0 END) AS OC_A_RECEBER,
        SUM(CASE WHEN X.GRUPO = 'NF'  THEN X.VALOR
                 WHEN X.GRUPO = 'DEV' THEN -X.VALOR
                 ELSE 0 END)                                                 AS RECEBIDO
    FROM (
        SELECT
            B.IDTRF,
            B.VALOR,
            /* parte ainda pendente do item (status A = aberto, G = parcial) */
            CASE WHEN B.STATUS IN ('A','G') AND B.QTDORIG > 0
                 THEN CASE WHEN ISNULL(B.QTDARECEBER,0) >= B.QTDORIG THEN 1.0
                           ELSE ISNULL(B.QTDARECEBER,0) / B.QTDORIG END
                 ELSE 0 END                                              AS FATOR_PEND,
            CASE
                WHEN B.CODTMV IN ('1.1.01','1.1.02','1.1.03','1.1.04','1.1.06')
                    THEN 'SC'
                WHEN B.CODTMV IN ('1.1.10','1.1.11','1.1.12','1.1.13','1.1.14',
                                  '1.1.18','1.1.19','1.1.33','1.1.34')
                    THEN 'OC'
                WHEN B.CODTMV LIKE '1.2.%'
                 AND B.CODTMV NOT IN ('1.2.05','1.2.15','1.2.21','1.2.61','1.2.62',
                                      '1.2.63','1.2.65','1.2.67','1.2.68','1.2.69',
                                      '1.2.76','1.2.77','1.2.93')
                    THEN 'NF'
                WHEN B.CODTMV = '2.2.01'
                    THEN 'DEV'
            END                                                          AS GRUPO
        FROM (
            /* 1) rateio do item por tarefa */
            SELECT
                R.IDTRF,
                M.CODTMV,
                M.STATUS,
                ISNULL(R.VALOR, I.VALORTOTALITEM * R.PERCENTUAL / 100.0) AS VALOR,
                I.QUANTIDADEORIGINAL                                     AS QTDORIG,
                I.QUANTIDADEARECEBER                                     AS QTDARECEBER
            FROM TITMMOVRATCCU R
            JOIN TITMMOV I
              ON I.CODCOLIGADA = R.CODCOLIGADA
             AND I.IDMOV       = R.IDMOV
             AND I.NSEQITMMOV  = R.NSEQITMMOV
            JOIN TMOV M
              ON M.CODCOLIGADA = R.CODCOLIGADA
             AND M.IDMOV       = R.IDMOV
            WHERE R.CODCOLIGADA = :CODCOLIGADA_N
              AND R.IDPRJ       = :IDPRJ_N
              AND R.IDTRF IS NOT NULL
              AND M.STATUS     <> 'C'

            UNION ALL

            /* 2) item sem rateio por tarefa: usa a tarefa do proprio item */
            SELECT
                I.IDTRF,
                M.CODTMV,
                M.STATUS,
                I.VALORTOTALITEM,
                I.QUANTIDADEORIGINAL,
                I.QUANTIDADEARECEBER
            FROM TITMMOV I
            JOIN TMOV M
              ON M.CODCOLIGADA = I.CODCOLIGADA
             AND M.IDMOV       = I.IDMOV
            WHERE I.CODCOLIGADA = :CODCOLIGADA_N
              AND I.IDPRJ       = :IDPRJ_N
              AND I.IDTRF IS NOT NULL
              AND M.STATUS     <> 'C'
              AND NOT EXISTS (SELECT 1 FROM TITMMOVRATCCU R
                              WHERE R.CODCOLIGADA = I.CODCOLIGADA
                                AND R.IDMOV       = I.IDMOV
                                AND R.NSEQITMMOV  = I.NSEQITMMOV
                                AND R.IDTRF IS NOT NULL)
        ) B
    ) X
    WHERE X.GRUPO IS NOT NULL
    GROUP BY X.IDTRF
),
/* acumula na tarefa tudo o que foi lancado nela e abaixo dela */
ACUM AS (
    SELECT
        C.IDANC               AS IDTRF,
        SUM(MV.SOLICITADO)    AS SOLICITADO,
        SUM(MV.OC_A_RECEBER)  AS OC_A_RECEBER,
        SUM(MV.RECEBIDO)      AS RECEBIDO
    FROM FECHO C
    JOIN MOVS MV
      ON MV.IDTRF = C.IDDESC
    GROUP BY C.IDANC
)
SELECT
    T.CODCOLIGADA,
    T.IDPRJ,
    T.IDTRF,
    CASE WHEN T.IDPAI = T.IDTRF THEN NULL ELSE T.IDPAI END   AS IDPAI,
    A.NIVEL,
    T.CODTRF,
    LTRIM(RTRIM(REPLACE(REPLACE(T.NOME, CHAR(13), ''),
                        CHAR(10), ' ')))                    AS [DESCRIÇÃO TAREFA],
    T.CODUND,
    ISNULL(T.QUANTIDADE, 0)                                 AS [QUANTIDADE ORÇADA],
    ISNULL(T.VALORTOTAL, 0)                                 AS [VALOR ORÇADO],
    CAST(ISNULL(AC.SOLICITADO, 0)   AS DECIMAL(18,2))       AS [SOLICITAÇÃO_VALOR],
    CAST(ISNULL(AC.OC_A_RECEBER, 0) AS DECIMAL(18,2))       AS PEDIDO_VALOR,
    CAST(ISNULL(AC.RECEBIDO, 0)     AS DECIMAL(18,2))       AS REALIZADO_VALOR
FROM ARVORE A
JOIN MTAREFA T
  ON T.CODCOLIGADA = A.CODCOLIGADA
 AND T.IDPRJ       = A.IDPRJ
 AND T.IDTRF       = A.IDTRF
LEFT JOIN ACUM AC
  ON AC.IDTRF = T.IDTRF
ORDER BY T.CODTRF

