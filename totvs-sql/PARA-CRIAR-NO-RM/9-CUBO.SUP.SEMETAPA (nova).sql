/* ======================================================
   CUBO.SUP.SEMETAPA - Compras da obra sem etapa no orcamento
   Parametros: CODCOLIGADA_N (Inteiro), IDPRJ_N (Inteiro)
   ------------------------------------------------------
   Versao parametrizada da CONFERE.SEMETAPA (que era fixa
   em 35/4). Uma linha por grupo de movimento (SC, OC, NF,
   DEV) com o total que NAO tem tarefa nem no rateio
   (TITMMOVRATCCU) nem no proprio item (TITMMOV).
   O app mostra esse total como a linha "Sem etapa" da tela
   Orcado x Comprado.
   Mesma classificacao de tipos da CUBO.SUP.ORCXCOMP.
   Movimentos cancelados (STATUS = 'C') ficam fora.
   [conferir] Ainda nao rodada no RM: compare com a
   CONFERE.SEMETAPA em 35/4 (cerca de R$ 1,9 mil).
   ====================================================== */
SELECT
    X.GRUPO,
    COUNT(*)                                   AS ITENS,
    CAST(SUM(X.VALOR) AS DECIMAL(18,2))        AS VALOR
FROM (
    SELECT
        CASE
            WHEN M.CODTMV IN ('1.1.01','1.1.02','1.1.03','1.1.04','1.1.06')
                THEN 'SC'
            WHEN M.CODTMV IN ('1.1.10','1.1.11','1.1.12','1.1.13','1.1.14',
                              '1.1.18','1.1.19','1.1.33','1.1.34')
                THEN 'OC'
            WHEN M.CODTMV LIKE '1.2.%'
             AND M.CODTMV NOT IN ('1.2.05','1.2.15','1.2.21','1.2.61','1.2.62',
                                  '1.2.63','1.2.65','1.2.67','1.2.68','1.2.69',
                                  '1.2.76','1.2.77','1.2.93')
                THEN 'NF'
            WHEN M.CODTMV = '2.2.01'
                THEN 'DEV'
        END                                    AS GRUPO,
        CASE WHEN R.IDMOV IS NULL THEN I.VALORTOTALITEM
             ELSE ISNULL(R.VALOR, I.VALORTOTALITEM * ISNULL(R.PERCENTUAL, 100) / 100.0)
        END                                    AS VALOR
    FROM TITMMOV I (NOLOCK)
    JOIN TMOV M (NOLOCK)
      ON M.CODCOLIGADA = I.CODCOLIGADA
     AND M.IDMOV       = I.IDMOV
    LEFT JOIN TITMMOVRATCCU R (NOLOCK)
      ON R.CODCOLIGADA = I.CODCOLIGADA
     AND R.IDMOV       = I.IDMOV
     AND R.NSEQITMMOV  = I.NSEQITMMOV
    WHERE I.CODCOLIGADA = :CODCOLIGADA_N
      AND (I.IDPRJ = :IDPRJ_N OR R.IDPRJ = :IDPRJ_N)
      AND M.STATUS <> 'C'
      AND ISNULL(R.IDTRF, I.IDTRF) IS NULL
) X
WHERE X.GRUPO IS NOT NULL
GROUP BY X.GRUPO
