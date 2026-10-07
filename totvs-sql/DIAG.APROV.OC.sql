/* =========================================================
   DIAG.APROV.OC - status do atendimento de aprovação da OC
   ---------------------------------------------------------
   Só leitura. Mostra os códigos de status (CODSTATUS) que o
   atendimento de aprovação de OC (tipo 12) usa no RM e quantas
   vezes cada um aparece. A CUBO.SUP.OC só traduz F (aprovada)
   e A (pendente); os demais aparecem no app como
   "SEM INFORMAÇÃO".

   Rode em Gestão › Consultas SQL (sem parâmetros) e mande o
   resultado, de preferência com a descrição de cada status.
   ========================================================= */
SELECT
    H.CODSTATUS,
    COUNT(*)                 AS QTD_ATENDIMENTOS,
    MIN(H.ABERTURA)          AS PRIMEIRA_ABERTURA,
    MAX(H.ABERTURA)          AS ULTIMA_ABERTURA
FROM HATENDIMENTOBASE H (NOLOCK)
WHERE H.CODTIPOATENDIMENTO = 12
GROUP BY H.CODSTATUS
ORDER BY COUNT(*) DESC
