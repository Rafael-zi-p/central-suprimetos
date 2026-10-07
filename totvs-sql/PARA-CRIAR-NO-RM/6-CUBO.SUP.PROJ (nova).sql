/* ======================================================
   CUBO.SUP.PROJ - Lista de obras / projetos (todas as coligadas)
   Sem parametros.
   - Etapa principal = tarefa com IDPAI = IDTRF (confirmado no RM)
   - Etapas-mae ja guardam o total das filhas: soma so as etapas
   - SUBSTITUIDO_POR_REVISAO = 1: existe revisao mais nova desta
     obra; nao somar nos paineis para nao duplicar orcamento
   ====================================================== */
SELECT
    PR.CODCOLIGADA,
    (SELECT G.NOMEFANTASIA FROM GCOLIGADA G
      WHERE G.CODCOLIGADA = PR.CODCOLIGADA)                 AS COLIGADA_NOME,
    PR.IDPRJ,
    PR.CODPRJ,
    LTRIM(RTRIM(REPLACE(REPLACE(PR.DESCRICAO, CHAR(13), ''),
                        CHAR(10), ' ')))                    AS OBRA,
    PR.REVISAO,
    CASE WHEN PR.IDPAI <> PR.IDPRJ THEN PR.IDPAI END        AS IDPRJ_ORIGINAL,
    CASE WHEN EXISTS (SELECT 1 FROM MPRJ R
                      WHERE R.CODCOLIGADA = PR.CODCOLIGADA
                        AND R.IDPAI       = PR.IDPRJ
                        AND R.IDPRJ      <> PR.IDPRJ)
         THEN 1 ELSE 0 END                                  AS SUBSTITUIDO_POR_REVISAO,
    PR.POSICAO,
    PR.CODFILIAL,
    PR.CODCCUSTO,
    PR.RESPONSAVEL,
    PR.RUA,
    PR.NUMERO,
    PR.COMPLEMENTO,
    PR.BAIRRO,
    PR.CIDADE,
    PR.ESTADO,
    PR.CEP,
    PR.CGC,
    PR.TELEFONE,
    E.QTD_TAREFAS,
    E.QTD_ETAPAS,
    E.VALOR_ORCADO_OBRA,
    E.CUSTO_ORCADO_OBRA,
    PR.VALORPROJETO
FROM MPRJ PR
LEFT JOIN (
    SELECT
        T.CODCOLIGADA,
        T.IDPRJ,
        COUNT(*)                                                     AS QTD_TAREFAS,
        SUM(CASE WHEN T.IDPAI = T.IDTRF THEN 1 ELSE 0 END)           AS QTD_ETAPAS,
        SUM(CASE WHEN T.IDPAI = T.IDTRF THEN T.VALORTOTAL ELSE 0 END) AS VALOR_ORCADO_OBRA,
        SUM(CASE WHEN T.IDPAI = T.IDTRF THEN T.CUSTOTOTAL ELSE 0 END) AS CUSTO_ORCADO_OBRA
    FROM MTAREFA T
    GROUP BY T.CODCOLIGADA, T.IDPRJ
) E
       ON E.CODCOLIGADA = PR.CODCOLIGADA
      AND E.IDPRJ       = PR.IDPRJ
ORDER BY PR.CODCOLIGADA, PR.CODPRJ, PR.IDPRJ
