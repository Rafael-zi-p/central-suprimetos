/* ======================================================
   CUBO.SUP.ORCETAPA - Orcamento da obra por etapa
   Parametros: CODCOLIGADA_N (Inteiro), IDPRJ_N (Inteiro)
   ------------------------------------------------------
   Uma linha por tarefa (MTAREFA):
   - NIVEL 1 = etapa principal (IDPAI = IDTRF)
   - NIVEL 2 = subetapa, 3+ = servicos/itens
   - ETAPA / SUBETAPA a que cada linha pertence
   - FOLHA = 1 quando a tarefa nao tem filhas
   Totais: o RM ja guarda nas etapas-mae a soma das filhas.
   Total da obra = soma de NIVEL = 1 (ou soma de FOLHA = 1).
   NUNCA somar todas as linhas (conta o mesmo valor varias vezes).
   ====================================================== */
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
    A.CODCOLIGADA,
    A.IDPRJ,
    A.NIVEL,
    A.IDETAPA,
    A.CODETAPA,
    A.ETAPA,
    A.IDSUBETAPA,
    A.CODSUBETAPA,
    A.SUBETAPA,
    T.IDTRF,
    T.IDPAI,
    T.CODTRF,
    LTRIM(RTRIM(REPLACE(REPLACE(T.NOME, CHAR(13), ''),
                        CHAR(10), ' ')))                    AS NOME,
    CASE WHEN EXISTS (SELECT 1 FROM MTAREFA C
                      WHERE C.CODCOLIGADA = T.CODCOLIGADA
                        AND C.IDPRJ       = T.IDPRJ
                        AND C.IDPAI       = T.IDTRF
                        AND C.IDTRF      <> T.IDTRF)
         THEN 0 ELSE 1 END                                  AS FOLHA,
    T.SERVICO,
    T.CODUND,
    T.QUANTIDADE,
    T.VALORUNIT,
    T.VALORTOTAL,
    T.CUSTOUNIT,
    T.CUSTOTOTAL,
    T.BDI,
    T.PERCCONCLUIDO
FROM ARVORE A
JOIN MTAREFA T
  ON T.CODCOLIGADA = A.CODCOLIGADA
 AND T.IDPRJ       = A.IDPRJ
 AND T.IDTRF       = A.IDTRF
ORDER BY T.CODTRF
