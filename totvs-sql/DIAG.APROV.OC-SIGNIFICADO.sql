/* =========================================================
   DIAG.APROV.OC-SIGNIFICADO - o que significa cada CODSTATUS
   ---------------------------------------------------------
   Só leitura. Para cada código de status usado no atendimento
   de aprovação de OC (tipo 12), mostra quantas vezes aparece e
   o cadastro do status no RM (tabela HSTATUS: nome/descrição
   e se ele encerra o atendimento).

   Rode em Gestão › Consultas SQL (sem parâmetros) e me mande
   o resultado (pode ser print ou Excel).

   Se der erro de "nome de coluna inválido" ou "objeto inválido",
   rode o arquivo DIAG.APROV.OC-TABELAS.sql e me mande o resultado:
   ele mostra os nomes certos das tabelas de status nesta base.
   ========================================================= */
SELECT
    C.CODCOLIGADA,
    C.CODSTATUS,
    C.QTD_ATENDIMENTOS,
    C.ULTIMA_ABERTURA,
    S.*
FROM (
    SELECT
        H.CODCOLIGADA,
        H.CODSTATUS,
        COUNT(*)        AS QTD_ATENDIMENTOS,
        MAX(H.ABERTURA) AS ULTIMA_ABERTURA
    FROM HATENDIMENTOBASE H (NOLOCK)
    WHERE H.CODTIPOATENDIMENTO = 12
    GROUP BY H.CODCOLIGADA, H.CODSTATUS
) C
LEFT JOIN HSTATUS S (NOLOCK)
       ON S.CODCOLIGADA = C.CODCOLIGADA
      AND S.CODSTATUS   = C.CODSTATUS
ORDER BY C.CODCOLIGADA, C.QTD_ATENDIMENTOS DESC
