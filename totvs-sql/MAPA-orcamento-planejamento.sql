/* =========================================================
   MAPA — onde ficam o orçamento e o planejamento das obras
   ---------------------------------------------------------
   Consulta só de leitura: lista as tabelas do módulo de
   Projetos e Obras (prefixo M, a mesma família da MPRJ que a
   CUBO.SUP.OC já usa) que têm dados, com as colunas de cada uma.
   Não altera nada no banco.

   Para que serve: com este resultado o SQL definitivo do
   Cronograma (CUBO.SUP.CRONO) é escrito com os nomes certos
   das tabelas e colunas da sua base, sem chute.

   Como usar no RM:
     1. Gestão › Consultas SQL › Incluir (ex.: MAPA.ORC.PLAN),
        cole este SQL e salve. Não tem parâmetros.
     2. Execute e exporte o resultado para Excel.
     3. Mande o Excel. Junto, se puder, mande o texto do SQL da
        consulta de Verbas (CUBO.ORC.00X), que já lê o orçamento.
   ========================================================= */

SELECT
    T.name                                   AS TABELA,
    C.column_id                              AS ORDEM,
    C.name                                   AS COLUNA,
    TY.name                                  AS TIPO,
    C.max_length                             AS TAMANHO,
    R.LINHAS                                 AS LINHAS_NA_TABELA
FROM sys.tables T
INNER JOIN sys.columns C
    ON C.object_id = T.object_id
INNER JOIN sys.types TY
    ON TY.user_type_id = C.user_type_id
CROSS APPLY
(
    SELECT SUM(P.rows) AS LINHAS
    FROM sys.partitions P
    WHERE P.object_id = T.object_id
      AND P.index_id IN (0, 1)
) R
WHERE
    T.name LIKE 'M%'
    AND R.LINHAS > 0
ORDER BY
    T.name,
    C.column_id;
