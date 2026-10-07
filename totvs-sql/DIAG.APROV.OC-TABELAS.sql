/* =========================================================
   DIAG.APROV.OC-TABELAS - onde o RM guarda a descrição do status
   ---------------------------------------------------------
   Só leitura. Use só se o DIAG.APROV.OC-SIGNIFICADO.sql der erro.
   Lista as tabelas do módulo de atendimento (começam com H) que
   têm "STATUS" no nome, com as colunas de cada uma. Com isso eu
   ajusto o SQL do significado para esta base.
   ========================================================= */
SELECT
    C.TABLE_NAME,
    C.COLUMN_NAME,
    C.DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS C
WHERE C.TABLE_NAME LIKE 'H%STATUS%'
ORDER BY C.TABLE_NAME, C.ORDINAL_POSITION
