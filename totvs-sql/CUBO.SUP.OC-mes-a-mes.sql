/* =========================================================
   CUBO.SUP.OC — OC por item, com PERÍODO POR PARÂMETRO
   ---------------------------------------------------------
   Mesmo SQL de antes, com 2 mudanças (marcadas "PERÍODO"):
   o período deixou de ser fixo e passou a vir de 2 parâmetros
   de data, que o app envia mês a mês:

     :DATAINI_D  → primeiro dia do mês (aaaa-mm-dd)
     :DATAFIM_D  → último dia do mês   (aaaa-mm-dd)

   Por quê: o site chama o RM por um proxy que corta qualquer
   chamada com mais de 26 segundos. O ano inteiro numa chamada
   só passa disso; um mês por vez, não.

   No RM: cole este SQL na consulta CUBO.SUP.OC e salve. Os dois
   parâmetros aparecem para preencher (tipo data). No app:
   Configurações › Integração TOTVS › "Busca da OC" = Mês a mês.
   No Power Query, para testar um mês:
     .../RealizaConsulta/CUBO.SUP.OC/0/T?parameters=DATAINI_D=2026-09-01;DATAFIM_D=2026-09-30
   ========================================================= */

WITH OC_IDENTIFICADAS AS
(
    SELECT DISTINCT
        AT.CODCOLIGADA,
        AT.IDMOV AS IDMOV_OC
    FROM TMOVATEND AT (NOLOCK)

    INNER JOIN HATENDIMENTOBASE H (NOLOCK)
        ON H.CODCOLIGADA = AT.CODCOLIGADAATEND
        AND H.CODATENDIMENTO = AT.CODATENDIMENTO
        AND H.CODTIPOATENDIMENTO = 12

    /* PERÍODO (parâmetros do app): só as OCs criadas na janela pedida.
       Filtrar aqui deixa todas as CTEs abaixo pequenas — cada chamada fica rápida. */
    INNER JOIN TMOV OCP (NOLOCK)
        ON OCP.CODCOLIGADA = AT.CODCOLIGADA
        AND OCP.IDMOV = AT.IDMOV
        AND OCP.DATACRIACAO >= :DATAINI_D
        AND OCP.DATACRIACAO <  DATEADD(DAY, 1, :DATAFIM_D)

    WHERE
        AT.CODCOLIGADA IN
        (
            2, 7, 35, 36, 39, 40,
            44, 46, 48, 51, 52, 63
        )
),

/* =========================================================
   RELAÇÃO OC -> SC
   ========================================================= */

OC_SC_REL AS
(
    SELECT DISTINCT

        R.CODCOLDESTINO AS CODCOLIGADA,
        R.IDMOVDESTINO AS IDMOV_OC,

        R.CODCOLORIGEM AS CODCOLIGADA_SC,
        R.IDMOVORIGEM AS IDMOV_SC,

        SC.NUMEROMOV AS NUMERO_SC,
        SC.CODTMV AS CODTMV_SC,

        SC.DATAEMISSAO AS DATA_EMISSAO_SC,
        SC.DATACRIACAO AS DATA_CRIACAO_SC,

        SC.USUARIOCRIACAO AS GERADO_POR_SC

    FROM TMOVRELAC R (NOLOCK)

    INNER JOIN OC_IDENTIFICADAS OX
        ON OX.CODCOLIGADA = R.CODCOLDESTINO
        AND OX.IDMOV_OC = R.IDMOVDESTINO

    INNER JOIN TMOV SC (NOLOCK)
        ON SC.CODCOLIGADA = R.CODCOLORIGEM
        AND SC.IDMOV = R.IDMOVORIGEM
),

/* =========================================================
   APROVAÇÃO DA SC

   FLUXOS VALIDADOS:
   5
   16

   STATUS F = aprovação
   DATA = HSTATUSATEND.DATA
   ========================================================= */

SC_APROVACAO AS
(
    SELECT

        X.CODCOLIGADA_SC,
        X.IDMOV_SC,
        X.CODATENDIMENTO_APROVACAO_SC,
        X.CODTIPOATENDIMENTO_APROVACAO_SC,
        X.DATA_APROVACAO_SC

    FROM
    (
        SELECT

            SAT.CODCOLIGADA AS CODCOLIGADA_SC,

            SAT.IDMOV AS IDMOV_SC,

            SAT.CODATENDIMENTO
                AS CODATENDIMENTO_APROVACAO_SC,

            SH.CODTIPOATENDIMENTO
                AS CODTIPOATENDIMENTO_APROVACAO_SC,

            HS.DATA AS DATA_APROVACAO_SC,

            ROW_NUMBER() OVER
            (
                PARTITION BY
                    SAT.CODCOLIGADA,
                    SAT.IDMOV

                ORDER BY
                    HS.DATA DESC,
                    SAT.CODATENDIMENTO DESC
            ) AS RN

        FROM TMOVATEND SAT (NOLOCK)

        INNER JOIN HATENDIMENTOBASE SH (NOLOCK)
            ON SH.CODCOLIGADA = SAT.CODCOLIGADAATEND
            AND SH.CODATENDIMENTO = SAT.CODATENDIMENTO
            AND SH.CODTIPOATENDIMENTO IN
            (
                5,
                16
            )

        INNER JOIN HSTATUSATEND HS (NOLOCK)
            ON HS.CODCOLIGADA = SH.CODCOLIGADA
            AND HS.CODLOCAL = SH.CODLOCAL
            AND HS.CODATENDIMENTO = SH.CODATENDIMENTO
            AND HS.CODSTATUS = 'F'
            AND HS.DATA IS NOT NULL

    ) X

    WHERE
        X.RN = 1
),

/* =========================================================
   SC COM APROVAÇÃO
   ========================================================= */

SC_BASE AS
(
    SELECT DISTINCT

        S.CODCOLIGADA,
        S.IDMOV_OC,

        S.CODCOLIGADA_SC,
        S.IDMOV_SC,

        S.NUMERO_SC,
        S.CODTMV_SC,

        S.DATA_EMISSAO_SC,
        S.DATA_CRIACAO_SC,

        S.GERADO_POR_SC,

        A.DATA_APROVACAO_SC,

        A.CODATENDIMENTO_APROVACAO_SC,

        A.CODTIPOATENDIMENTO_APROVACAO_SC

    FROM OC_SC_REL S

    LEFT JOIN SC_APROVACAO A
        ON A.CODCOLIGADA_SC = S.CODCOLIGADA_SC
        AND A.IDMOV_SC = S.IDMOV_SC
),

/* =========================================================
   SCs VINCULADAS À OC
   ========================================================= */

SC_VINCULADAS AS
(
    SELECT

        CODCOLIGADA,
        IDMOV_OC,

        COUNT(DISTINCT IDMOV_SC)
            AS QTD_SC_VINCULADAS,

        STRING_AGG(
            CAST(NUMERO_SC AS VARCHAR(MAX)),
            ', '
        ) AS NUMERO_SC,

        STRING_AGG(
            CAST(CODTMV_SC AS VARCHAR(MAX)),
            ', '
        ) AS CODTMV_SC,

        MIN(DATA_CRIACAO_SC)
            AS DATA_CRIACAO_SC,

        MIN(DATA_EMISSAO_SC)
            AS DATA_EMISSAO_SC,

        MAX(DATA_APROVACAO_SC)
            AS DATA_APROVACAO_SC,

        STRING_AGG(
            CAST(GERADO_POR_SC AS VARCHAR(MAX)),
            ', '
        ) AS GERADO_POR_SC

    FROM SC_BASE

    GROUP BY
        CODCOLIGADA,
        IDMOV_OC
),

/* =========================================================
   RELAÇÃO ITEM SC -> ITEM OC
   ========================================================= */

SC_ITEM_BASE AS
(
    SELECT DISTINCT

        R.CODCOLDESTINO AS CODCOLIGADA,

        R.IDMOVDESTINO AS IDMOV_OC,

        R.NSEQITMMOVDESTINO AS ITEM_OC,

        R.CODCOLORIGEM AS CODCOLIGADA_SC,

        R.IDMOVORIGEM AS IDMOV_SC,

        R.NSEQITMMOVORIGEM AS ITEM_SC,

        S.NUMERO_SC,
        S.CODTMV_SC,

        S.DATA_CRIACAO_SC,
        S.DATA_EMISSAO_SC,

        S.GERADO_POR_SC,

        S.DATA_APROVACAO_SC,

        S.CODATENDIMENTO_APROVACAO_SC,

        S.CODTIPOATENDIMENTO_APROVACAO_SC,

        SI.DATAENTREGA AS DATA_NECESSIDADE_SC

    FROM TITMMOVRELAC R (NOLOCK)

    INNER JOIN OC_IDENTIFICADAS OX
        ON OX.CODCOLIGADA = R.CODCOLDESTINO
        AND OX.IDMOV_OC = R.IDMOVDESTINO

    INNER JOIN SC_BASE S
        ON S.CODCOLIGADA = R.CODCOLDESTINO
        AND S.IDMOV_OC = R.IDMOVDESTINO
        AND S.CODCOLIGADA_SC = R.CODCOLORIGEM
        AND S.IDMOV_SC = R.IDMOVORIGEM

    INNER JOIN TITMMOV SI (NOLOCK)
        ON SI.CODCOLIGADA = R.CODCOLORIGEM
        AND SI.IDMOV = R.IDMOVORIGEM
        AND SI.NSEQITMMOV = R.NSEQITMMOVORIGEM
),

/* =========================================================
   CONSOLIDAÇÃO SC POR ITEM
   ========================================================= */

SC_ITEM_VINCULADAS AS
(
    SELECT

        CODCOLIGADA,
        IDMOV_OC,
        ITEM_OC,

        COUNT(DISTINCT IDMOV_SC)
            AS QTD_SC_ITEM,

        STRING_AGG(
            CAST(NUMERO_SC AS VARCHAR(MAX)),
            ', '
        ) AS NUMERO_SC_ITEM,

        STRING_AGG(
            CAST(CODTMV_SC AS VARCHAR(MAX)),
            ', '
        ) AS CODTMV_SC_ITEM,

        MIN(DATA_CRIACAO_SC)
            AS DATA_CRIACAO_SC_ITEM,

        MIN(DATA_EMISSAO_SC)
            AS DATA_EMISSAO_SC_ITEM,

        MAX(DATA_APROVACAO_SC)
            AS DATA_APROVACAO_SC_ITEM,

        MIN(DATA_NECESSIDADE_SC)
            AS DATA_NECESSIDADE_SC,

        MAX(DATA_NECESSIDADE_SC)
            AS DATA_NECESSIDADE_SC_ULTIMA,

        STRING_AGG(
            CAST(GERADO_POR_SC AS VARCHAR(MAX)),
            ', '
        ) AS GERADO_POR_SC_ITEM,

        MAX(
            CODATENDIMENTO_APROVACAO_SC
        ) AS CODATENDIMENTO_APROVACAO_SC,

        MAX(
            CODTIPOATENDIMENTO_APROVACAO_SC
        ) AS CODTIPOATENDIMENTO_APROVACAO_SC

    FROM SC_ITEM_BASE

    GROUP BY
        CODCOLIGADA,
        IDMOV_OC,
        ITEM_OC
),

/* =========================================================
   RECEBIMENTO BASE

   VALORRECEBIDO pode estar NULL.
   Trazemos o preço unitário da OC para cálculo analítico.
   ========================================================= */

RECEBIMENTO_BASE AS
(
    SELECT

        R.CODCOLORIGEM AS CODCOLIGADA,

        R.IDMOVORIGEM AS IDMOV_OC,

        R.NSEQITMMOVORIGEM AS ITEM_OC,

        R.IDMOVDESTINO,

        R.QUANTIDADE,

        R.VALORRECEBIDO,

        I.PRECOUNITARIO,

        NF.NUMEROMOV AS NUMERO_DOCUMENTO_ENTRADA,

        NF.DATACRIACAO AS DATA_DOCUMENTO_ENTRADA

    FROM TITMMOVRELAC R (NOLOCK)

    INNER JOIN OC_IDENTIFICADAS OX
        ON OX.CODCOLIGADA = R.CODCOLORIGEM
        AND OX.IDMOV_OC = R.IDMOVORIGEM

    INNER JOIN TITMMOV I (NOLOCK)
        ON I.CODCOLIGADA = R.CODCOLORIGEM
        AND I.IDMOV = R.IDMOVORIGEM
        AND I.NSEQITMMOV = R.NSEQITMMOVORIGEM

    LEFT JOIN TMOV NF (NOLOCK)
        ON NF.CODCOLIGADA = R.CODCOLDESTINO
        AND NF.IDMOV = R.IDMOVDESTINO
),

/* =========================================================
   CONSOLIDAÇÃO DO RECEBIMENTO
   ========================================================= */

RECEBIMENTO AS
(
    SELECT

        CODCOLIGADA,
        IDMOV_OC,
        ITEM_OC,

        SUM(
            COALESCE(
                QUANTIDADE,
                0
            )
        ) AS QUANTIDADE_RECEBIDA,

        /* Valor original informado pelo RM */
        SUM(
            COALESCE(
                VALORRECEBIDO,
                0
            )
        ) AS VALOR_RECEBIDO_RM,

        /* Valor analítico */
        SUM(
            CASE

                WHEN COALESCE(
                    VALORRECEBIDO,
                    0
                ) <> 0

                THEN VALORRECEBIDO

                WHEN COALESCE(
                    QUANTIDADE,
                    0
                ) <> 0

                AND COALESCE(
                    PRECOUNITARIO,
                    0
                ) <> 0

                THEN
                    QUANTIDADE
                    *
                    PRECOUNITARIO

                ELSE 0

            END
        ) AS VALOR_RECEBIDO,

        COUNT(
            DISTINCT IDMOVDESTINO
        ) AS QTD_DOCUMENTOS_ENTRADA,

        STRING_AGG(
            CAST(
                NUMERO_DOCUMENTO_ENTRADA
                AS VARCHAR(MAX)
            ),
            ', '
        ) AS NUMEROS_DOCUMENTOS_ENTRADA,

        MIN(
            CASE

                WHEN COALESCE(
                    QUANTIDADE,
                    0
                ) > 0

                THEN DATA_DOCUMENTO_ENTRADA

            END
        ) AS DATA_PRIMEIRO_RECEBIMENTO,

        MAX(
            CASE

                WHEN COALESCE(
                    QUANTIDADE,
                    0
                ) > 0

                THEN DATA_DOCUMENTO_ENTRADA

            END
        ) AS DATA_ULTIMO_RECEBIMENTO

    FROM RECEBIMENTO_BASE

    GROUP BY
        CODCOLIGADA,
        IDMOV_OC,
        ITEM_OC
)

/* =========================================================
   SELECT FINAL
   ========================================================= */

SELECT

    /* =====================================================
       IDENTIFICAÇÃO
       ===================================================== */

    OC.CODCOLIGADA AS COD_OBRA,

    CASE
        WHEN OC.CODCOLIGADA = 2
            THEN 'IMPPER LOUNGE'
        ELSE COL.NOMEFANTASIA
    END AS OBRA,

    OC.NUMEROMOV AS NUMERO_OC,

    OC.CODTMV AS CODTMV_OC,

    I.NSEQITMMOV AS ITEM_OC,

    PROD.CODIGOPRD AS CODIGO_INSUMO,

    PROD.NOMEFANTASIA AS NOME_INSUMO,

    I.CODUND AS UNIDADE,


    /* =====================================================
       QUANTIDADE / PREÇO
       ===================================================== */

    I.QUANTIDADEORIGINAL AS QUANTIDADE_COMPRADA,

    I.PRECOUNITARIO AS PRECO_UNITARIO,


    /* Valor original RM */

    I.VALORBRUTOITEM AS VALOR_BRUTO_ITEM_RM,

    I.VALORTOTALITEM AS VALOR_TOTAL_ITEM_RM,


    /* Valor para análise */

    CASE

        WHEN COALESCE(
            I.VALORTOTALITEM,
            0
        ) <> 0

        THEN I.VALORTOTALITEM

        WHEN

            COALESCE(
                I.QUANTIDADEORIGINAL,
                0
            ) <> 0

            AND COALESCE(
                I.PRECOUNITARIO,
                0
            ) <> 0

        THEN

            I.QUANTIDADEORIGINAL
            *
            I.PRECOUNITARIO

        ELSE 0

    END AS VALOR_TOTAL_ITEM,


    CASE

        WHEN

            COALESCE(
                I.VALORTOTALITEM,
                0
            ) = 0

            AND COALESCE(
                I.QUANTIDADEORIGINAL,
                0
            ) <> 0

            AND COALESCE(
                I.PRECOUNITARIO,
                0
            ) <> 0

        THEN 'CALCULADO - RM SEM VALOR'

        ELSE 'VALOR RM'

    END AS ORIGEM_VALOR_TOTAL_ITEM,


    /* =====================================================
       SC
       ===================================================== */

    COALESCE(
        SCIV.NUMERO_SC_ITEM,
        SCV.NUMERO_SC
    ) AS NUMERO_SC,

    COALESCE(
        SCIV.CODTMV_SC_ITEM,
        SCV.CODTMV_SC
    ) AS CODTMV_SC,

    COALESCE(
        SCIV.QTD_SC_ITEM,
        SCV.QTD_SC_VINCULADAS,
        0
    ) AS QTD_SC_VINCULADAS,


    CONVERT(
        VARCHAR(10),

        COALESCE(
            SCIV.DATA_CRIACAO_SC_ITEM,
            SCV.DATA_CRIACAO_SC
        ),

        103

    ) AS DATA_CRIACAO_SC,


    CONVERT(
        VARCHAR(10),

        COALESCE(
            SCIV.DATA_EMISSAO_SC_ITEM,
            SCV.DATA_EMISSAO_SC
        ),

        103

    ) AS DATA_EMISSAO_SC,


    COALESCE(

        CONVERT(
            VARCHAR(10),

            COALESCE(
                SCIV.DATA_APROVACAO_SC_ITEM,
                SCV.DATA_APROVACAO_SC
            ),

            103

        ),

        ''

    ) AS DATA_APROVACAO_SC,


    CONVERT(
        VARCHAR(10),
        SCIV.DATA_NECESSIDADE_SC,
        103
    ) AS DATA_NECESSIDADE_SC,


    CONVERT(
        VARCHAR(10),
        SCIV.DATA_NECESSIDADE_SC_ULTIMA,
        103
    ) AS DATA_NECESSIDADE_SC_ULTIMA,


    CASE

        WHEN COALESCE(
            SCIV.DATA_APROVACAO_SC_ITEM,
            SCV.DATA_APROVACAO_SC
        ) IS NOT NULL

        THEN 'APROVADA'

        ELSE 'SEM APROVAÇÃO'

    END AS SITUACAO_APROVACAO_SC,


    /* =====================================================
       PRAZO SC
       ===================================================== */

    CASE

        WHEN

            COALESCE(
                SCIV.DATA_APROVACAO_SC_ITEM,
                SCV.DATA_APROVACAO_SC
            ) IS NULL

            OR SCIV.DATA_NECESSIDADE_SC IS NULL

        THEN NULL

        ELSE DATEDIFF(

            DAY,

            COALESCE(
                SCIV.DATA_APROVACAO_SC_ITEM,
                SCV.DATA_APROVACAO_SC
            ),

            SCIV.DATA_NECESSIDADE_SC

        )

    END AS PRAZO_APROVACAO_SC_NECESSIDADE,


    /* =====================================================
       OC
       ===================================================== */

    CONVERT(
        VARCHAR(10),
        OC.DATACRIACAO,
        103
    ) AS DATA_CRIACAO_OC,


    CONVERT(
        VARCHAR(10),
        OC.DATAEMISSAO,
        103
    ) AS DATA_EMISSAO_OC,


    CONVERT(
        VARCHAR(10),
        APO.DATA_APROVACAO_OC,
        103
    ) AS DATA_APROVACAO_OC,


    CASE

        WHEN

            COALESCE(
                SCIV.DATA_APROVACAO_SC_ITEM,
                SCV.DATA_APROVACAO_SC
            ) IS NULL

        THEN NULL

        ELSE DATEDIFF(

            DAY,

            COALESCE(
                SCIV.DATA_APROVACAO_SC_ITEM,
                SCV.DATA_APROVACAO_SC
            ),

            OC.DATACRIACAO

        )

    END AS PRAZO_APROVACAO_SC_OC,


    CASE

        WHEN APO.DATA_APROVACAO_OC IS NULL

        THEN NULL

        ELSE DATEDIFF(

            DAY,

            OC.DATACRIACAO,

            APO.DATA_APROVACAO_OC

        )

    END AS PRAZO_CRIACAO_OC_APROVACAO_OC,


    CASE

        WHEN SCIV.DATA_NECESSIDADE_SC IS NULL

        THEN NULL

        ELSE DATEDIFF(

            DAY,

            OC.DATACRIACAO,

            SCIV.DATA_NECESSIDADE_SC

        )

    END AS DIAS_ANTECEDENCIA_OC_NECESSIDADE,


    CASE

        WHEN SCIV.DATA_NECESSIDADE_SC IS NULL

        THEN 'SEM DATA DE NECESSIDADE'

        WHEN OC.DATACRIACAO <=
             SCIV.DATA_NECESSIDADE_SC

        THEN 'DENTRO DO PRAZO'

        ELSE 'FORA DO PRAZO'

    END AS OC_DENTRO_PRAZO,


    /* =====================================================
       ENTREGA / RECEBIMENTO
       ===================================================== */

    CONVERT(
        VARCHAR(10),
        I.DATAENTREGA,
        103
    ) AS DATA_ENTREGA_ITEM,


    CONVERT(
        VARCHAR(10),
        RC.DATA_PRIMEIRO_RECEBIMENTO,
        103
    ) AS DATA_PRIMEIRO_RECEBIMENTO,


    CONVERT(
        VARCHAR(10),
        RC.DATA_ULTIMO_RECEBIMENTO,
        103
    ) AS DATA_ULTIMO_RECEBIMENTO,


    COALESCE(
        RC.QUANTIDADE_RECEBIDA,
        0
    ) AS QUANTIDADE_RECEBIDA,


    COALESCE(
        I.QUANTIDADEARECEBER,
        0
    ) AS SALDO_A_RECEBER,


    CASE

        WHEN

            I.QUANTIDADEORIGINAL IS NULL

            OR I.QUANTIDADEORIGINAL = 0

        THEN NULL

        ELSE ROUND(

            (
                COALESCE(
                    RC.QUANTIDADE_RECEBIDA,
                    0
                )
                /
                I.QUANTIDADEORIGINAL
            ) * 100,

            2

        )

    END AS PERCENTUAL_RECEBIDO,


    CASE

        WHEN

            I.QUANTIDADEORIGINAL IS NULL

            OR I.QUANTIDADEORIGINAL = 0

        THEN 'SEM QUANTIDADE'

        WHEN

            COALESCE(
                I.QUANTIDADEARECEBER,
                0
            ) <= 0.0001

        THEN 'RECEBIDA / CONCLUÍDA NO RM'

        WHEN

            COALESCE(
                I.QUANTIDADEARECEBER,
                0
            )
            >=
            I.QUANTIDADEORIGINAL - 0.0001

        THEN 'NÃO RECEBIDA'

        ELSE 'PARCIALMENTE RECEBIDA'

    END AS SITUACAO_RECEBIMENTO,


    /* Valor recebido analítico */

    COALESCE(
        RC.VALOR_RECEBIDO,
        0
    ) AS VALOR_RECEBIDO,


    /* Valor originalmente registrado */

    COALESCE(
        RC.VALOR_RECEBIDO_RM,
        0
    ) AS VALOR_RECEBIDO_RM,


    CASE

        WHEN

            COALESCE(
                RC.VALOR_RECEBIDO_RM,
                0
            ) <> 0

        THEN 'VALOR RM'

        WHEN

            COALESCE(
                RC.QUANTIDADE_RECEBIDA,
                0
            ) <> 0

        THEN 'CALCULADO - RM SEM VALOR'

        ELSE 'SEM RECEBIMENTO'

    END AS ORIGEM_VALOR_RECEBIDO,


    COALESCE(
        RC.QTD_DOCUMENTOS_ENTRADA,
        0
    ) AS QTD_DOCUMENTOS_ENTRADA,


    RC.NUMEROS_DOCUMENTOS_ENTRADA,


    /* =====================================================
       VALIDAÇÃO RECEBIMENTO
       ===================================================== */

    CASE

        WHEN I.QUANTIDADEORIGINAL IS NULL

        THEN NULL

        ELSE

            I.QUANTIDADEORIGINAL
            -
            COALESCE(
                RC.QUANTIDADE_RECEBIDA,
                0
            )

    END AS SALDO_A_RECEBER_CALCULADO,


    CASE

        WHEN I.QUANTIDADEORIGINAL IS NULL

        THEN NULL

        ELSE

            COALESCE(
                RC.QUANTIDADE_RECEBIDA,
                0
            )
            -
            (
                I.QUANTIDADEORIGINAL
                -
                COALESCE(
                    I.QUANTIDADEARECEBER,
                    0
                )
            )

    END AS DIVERGENCIA_QUANTIDADE_RECEBIMENTO,


    CASE

        WHEN I.QUANTIDADEORIGINAL IS NULL

        THEN 'SEM INFORMAÇÃO'

        WHEN ABS(

            COALESCE(
                RC.QUANTIDADE_RECEBIDA,
                0
            )
            -
            (
                I.QUANTIDADEORIGINAL
                -
                COALESCE(
                    I.QUANTIDADEARECEBER,
                    0
                )
            )

        ) <= 0.001

        THEN 'OK'

        ELSE 'VERIFICAR'

    END AS VALIDACAO_RECEBIMENTO,


    /* =====================================================
       FORNECEDOR / PAGAMENTO
       ===================================================== */

    COALESCE(

        NULLIF(

            LTRIM(
                RTRIM(
                    FORN.NOMEFANTASIA
                )
            ),

            ''

        ),

        FORN.NOME

    ) AS FORNECEDOR,


    CPG.NOME AS CONDICAO_PAGAMENTO,


    CASE

        WHEN NULLIF(

            LTRIM(
                RTRIM(
                    CAST(
                        FORN.FORMAPAGAMENTO
                        AS VARCHAR(100)
                    )
                )
            ),

            ''

        ) IS NULL

        THEN 'NÃO INFORMADO'

        ELSE CAST(
            FORN.FORMAPAGAMENTO
            AS VARCHAR(100)
        )

    END AS FORMA_PAGAMENTO,


    /* =====================================================
       CANCELAMENTO
       ===================================================== */

    CONVERT(
        VARCHAR(10),
        OC.DATACANCELAMENTOMOV,
        103
    ) AS DATA_CANCELAMENTO_OC,


    CASE

        WHEN OC.DATACANCELAMENTOMOV IS NOT NULL

        THEN 'CANCELADA'

        ELSE 'NÃO CANCELADA'

    END AS SITUACAO_CANCELAMENTO_OC,


    /* =====================================================
       APROVAÇÃO OC
       ===================================================== */

    AP.CODSTATUS AS COD_STATUS_APROVACAO_OC,


    CASE

        WHEN AP.CODSTATUS = 'F'

        THEN 'APROVADA'

        WHEN AP.CODSTATUS = 'A'

        THEN 'PENDENTE'

        WHEN APO.DATA_APROVACAO_OC IS NOT NULL

        THEN 'APROVADA'

        ELSE 'SEM INFORMAÇÃO'

    END AS SITUACAO_APROVACAO_OC,


    CONVERT(
        VARCHAR(10),
        AP.ABERTURA,
        103
    ) AS DATA_ABERTURA_APROVACAO_OC,


    CONVERT(
        VARCHAR(10),
        AP.FECHAMENTO,
        103
    ) AS DATA_FECHAMENTO_APROVACAO_OC,


    /* =====================================================
       PROJETO
       ===================================================== */

    COALESCE(
        I.IDPRJ,
        OC.IDPRJ
    ) AS ID_PROJETO,


    PROJ.CODPRJ AS CODIGO_PROJETO,


    COALESCE(
        PROJ.DESCRICAO,
        'SEM PROJETO'
    ) AS PROJETO,


    /* =====================================================
       CENTRO DE CUSTO
       ===================================================== */

    COALESCE(
        I.CODCCUSTO,
        OC.CODCCUSTO
    ) AS COD_CCUSTO,


    CC.NOME AS CENTRO_CUSTO,


    /* =====================================================
       DADOS DE APOIO
       ===================================================== */

    OC.USUARIOCRIACAO AS GERADO_POR_OC,


    COALESCE(
        SCIV.GERADO_POR_SC_ITEM,
        SCV.GERADO_POR_SC
    ) AS GERADO_POR_SC,


    OC.STATUS AS STATUS_OC,


    I.QUANTIDADE AS QUANTIDADE_RM,


    I.QUANTIDADETOTAL AS QUANTIDADE_TOTAL_RM,


    I.QUANTIDADECONCLUIDA AS QUANTIDADE_CONCLUIDA,


    I.QUANTIDADESEPARADA AS QUANTIDADE_SEPARADA,


    I.IDPRD AS ID_PRODUTO,


    OC.CODCFO AS COD_FORNECEDOR,


    OC.CODCPG AS COD_CONDICAO_PAGAMENTO,


    /* Atendimento aprovação OC */

    AP.CODATENDIMENTO
        AS COD_ATENDIMENTO_APROVACAO_OC,


    AP.CODATENDENTE
        AS COD_ATENDENTE_APROVACAO_OC,


    AP.CODATENDENTERESP
        AS COD_RESPONSAVEL_APROVACAO_OC,


    /* Atendimento aprovação SC */

    SCIV.CODATENDIMENTO_APROVACAO_SC
        AS COD_ATENDIMENTO_APROVACAO_SC,


    SCIV.CODTIPOATENDIMENTO_APROVACAO_SC
        AS COD_TIPO_ATENDIMENTO_APROVACAO_SC,


    FORN.CGCCFO AS CNPJ_FORNECEDOR,


    CASE

        WHEN COALESCE(
            SCIV.NUMERO_SC_ITEM,
            SCV.NUMERO_SC
        ) IS NULL

        THEN 'SEM SC VINCULADA'

        ELSE 'COM SC VINCULADA'

    END AS SITUACAO_SC,


    COALESCE(
        SCIV.QTD_SC_ITEM,
        SCV.QTD_SC_VINCULADAS,
        0
    ) AS QTD_SC_ITEM


FROM TMOV OC (NOLOCK)


INNER JOIN OC_IDENTIFICADAS OX

    ON OX.CODCOLIGADA =
        OC.CODCOLIGADA

    AND OX.IDMOV_OC =
        OC.IDMOV


INNER JOIN TITMMOV I (NOLOCK)

    ON I.CODCOLIGADA =
        OC.CODCOLIGADA

    AND I.IDMOV =
        OC.IDMOV


LEFT JOIN GCOLIGADA COL (NOLOCK)

    ON COL.CODCOLIGADA =
        OC.CODCOLIGADA


LEFT JOIN SC_VINCULADAS SCV

    ON SCV.CODCOLIGADA =
        OC.CODCOLIGADA

    AND SCV.IDMOV_OC =
        OC.IDMOV


LEFT JOIN SC_ITEM_VINCULADAS SCIV

    ON SCIV.CODCOLIGADA =
        OC.CODCOLIGADA

    AND SCIV.IDMOV_OC =
        OC.IDMOV

    AND SCIV.ITEM_OC =
        I.NSEQITMMOV


LEFT JOIN RECEBIMENTO RC

    ON RC.CODCOLIGADA =
        OC.CODCOLIGADA

    AND RC.IDMOV_OC =
        OC.IDMOV

    AND RC.ITEM_OC =
        I.NSEQITMMOV


LEFT JOIN TPRODUTO PROD (NOLOCK)

    ON PROD.IDPRD =
        I.IDPRD


LEFT JOIN FCFO FORN (NOLOCK)

    ON FORN.CODCFO =
        OC.CODCFO

    AND FORN.CODCOLIGADA = 0


LEFT JOIN TCPG CPG (NOLOCK)

    ON CPG.CODCOLIGADA =
        OC.CODCOLIGADA

    AND CPG.CODCPG =
        OC.CODCPG


LEFT JOIN MPRJ PROJ (NOLOCK)

    ON PROJ.CODCOLIGADA =
        OC.CODCOLIGADA

    AND PROJ.IDPRJ =
        COALESCE(
            I.IDPRJ,
            OC.IDPRJ
        )


LEFT JOIN GCCUSTO CC (NOLOCK)

    ON CC.CODCOLIGADA =
        OC.CODCOLIGADA

    AND CC.CODCCUSTO =
        COALESCE(
            I.CODCCUSTO,
            OC.CODCCUSTO
        )


/* =========================================================
   APROVAÇÃO DA OC
   ========================================================= */

OUTER APPLY
(
    SELECT TOP 1

        ATX.CODATENDIMENTO,

        ATX.CODCOLIGADAATEND,

        HX.CODLOCAL,

        HX.CODSTATUS,

        HX.ABERTURA,

        HX.FECHAMENTO,

        HX.CODATENDENTE,

        HX.CODATENDENTERESP

    FROM TMOVATEND ATX (NOLOCK)

    INNER JOIN HATENDIMENTOBASE HX (NOLOCK)

        ON HX.CODCOLIGADA =
            ATX.CODCOLIGADAATEND

        AND HX.CODATENDIMENTO =
            ATX.CODATENDIMENTO

        AND HX.CODTIPOATENDIMENTO = 12

    WHERE

        ATX.CODCOLIGADA =
            OC.CODCOLIGADA

        AND ATX.IDMOV =
            OC.IDMOV

    ORDER BY

        CASE

            WHEN HX.FECHAMENTO IS NULL

            THEN 0

            ELSE 1

        END,

        HX.ABERTURA DESC,

        ATX.CODATENDIMENTO DESC

) AP


/* =========================================================
   DATA DE APROVAÇÃO DA OC
   ========================================================= */

OUTER APPLY
(
    SELECT

        MAX(
            HSX.DATA
        ) AS DATA_APROVACAO_OC

    FROM HSTATUSATEND HSX (NOLOCK)

    WHERE

        HSX.CODCOLIGADA =
            AP.CODCOLIGADAATEND

        AND HSX.CODLOCAL =
            AP.CODLOCAL

        AND HSX.CODATENDIMENTO =
            AP.CODATENDIMENTO

        AND HSX.CODSTATUS = 'F'

        AND HSX.DATA IS NOT NULL

) APO


WHERE

    OC.CODCOLIGADA IN
    (
        2, 7, 35, 36, 39, 40,
        44, 46, 48, 51, 52, 63
    )

    /* PERÍODO (parâmetros do app) — antes: >= '2026-01-01' e < amanhã */
    AND OC.DATACRIACAO >= :DATAINI_D

    AND OC.DATACRIACAO <  DATEADD(DAY, 1, :DATAFIM_D)


ORDER BY

    OC.CODCOLIGADA,

    OC.DATACRIACAO,

    OC.NUMEROMOV,

    I.NSEQITMMOV;
