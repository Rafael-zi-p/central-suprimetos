/* =========================================================
   DIAG.APROV.OC-CANCELADAS - OCs cuja última aprovação é "C"
   ---------------------------------------------------------
   Só leitura. Pega, para cada OC, o mesmo atendimento de
   aprovação que a CUBO.SUP.OC usa (aberto primeiro; senão o
   mais recente) e, quando ele é "C", mostra:
     - a situação da OC no RM (TMOV.STATUS);
     - se a OC já teve alguma aprovação "F" antes;
     - se ainda tem alguma aprovação "A" (pendente).
   Agrupa para mostrar quantas OCs caem em cada caso.
   ========================================================= */
SELECT
    T.STATUS                              AS STATUS_DA_OC,
    CASE WHEN F.QTD > 0 THEN 'SIM' ELSE 'NAO' END AS JA_TEVE_APROVACAO_F,
    CASE WHEN A.QTD > 0 THEN 'SIM' ELSE 'NAO' END AS TEM_PENDENTE_A,
    COUNT(*)                              AS QTD_OCS,
    MIN(T.NUMEROMOV)                      AS EXEMPLO_OC_1,
    MAX(T.NUMEROMOV)                      AS EXEMPLO_OC_2,
    MIN(T.CODCOLIGADA)                    AS COLIGADA_EXEMPLO
FROM TMOV T (NOLOCK)
CROSS APPLY (
    SELECT TOP 1 HX.CODSTATUS
    FROM TMOVATEND ATX (NOLOCK)
    INNER JOIN HATENDIMENTOBASE HX (NOLOCK)
            ON HX.CODCOLIGADA        = ATX.CODCOLIGADAATEND
           AND HX.CODATENDIMENTO     = ATX.CODATENDIMENTO
           AND HX.CODTIPOATENDIMENTO = 12
    WHERE ATX.CODCOLIGADA = T.CODCOLIGADA
      AND ATX.IDMOV       = T.IDMOV
    ORDER BY CASE WHEN HX.FECHAMENTO IS NULL THEN 0 ELSE 1 END,
             HX.ABERTURA DESC,
             ATX.CODATENDIMENTO DESC
) UL
OUTER APPLY (
    SELECT COUNT(*) AS QTD
    FROM TMOVATEND A1 (NOLOCK)
    INNER JOIN HATENDIMENTOBASE H1 (NOLOCK)
            ON H1.CODCOLIGADA = A1.CODCOLIGADAATEND AND H1.CODATENDIMENTO = A1.CODATENDIMENTO
           AND H1.CODTIPOATENDIMENTO = 12 AND H1.CODSTATUS = 'F'
    WHERE A1.CODCOLIGADA = T.CODCOLIGADA AND A1.IDMOV = T.IDMOV
) F
OUTER APPLY (
    SELECT COUNT(*) AS QTD
    FROM TMOVATEND A2 (NOLOCK)
    INNER JOIN HATENDIMENTOBASE H2 (NOLOCK)
            ON H2.CODCOLIGADA = A2.CODCOLIGADAATEND AND H2.CODATENDIMENTO = A2.CODATENDIMENTO
           AND H2.CODTIPOATENDIMENTO = 12 AND H2.CODSTATUS = 'A'
    WHERE A2.CODCOLIGADA = T.CODCOLIGADA AND A2.IDMOV = T.IDMOV
) A
WHERE UL.CODSTATUS = 'C'
GROUP BY T.STATUS,
         CASE WHEN F.QTD > 0 THEN 'SIM' ELSE 'NAO' END,
         CASE WHEN A.QTD > 0 THEN 'SIM' ELSE 'NAO' END
ORDER BY COUNT(*) DESC
