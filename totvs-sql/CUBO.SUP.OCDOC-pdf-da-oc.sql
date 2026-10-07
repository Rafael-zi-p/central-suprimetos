/* =========================================================
   CUBO.SUP.OCDOC — dados de UMA OC para o PDF de envio ao fornecedor
   ---------------------------------------------------------
   Uma linha por item da OC; os dados do cabeçalho (obra,
   fornecedor, comprador, pagamento, totais, observação) se
   repetem em cada linha. O app monta o PDF e deixa editar
   observações, endereço/horário de entrega e contato antes de
   gerar — o que é editado fica no app, o TOTVS não é alterado.

   Parâmetros (o app envia):
     :CODCOLIGADA_N   coligada (obra) da OC
     :NUMEROMOV_S     número da OC, como vem na CUBO.SUP.OC (NUMERO_OC)
     :CODTMV_S        tipo de movimento da OC (CODTMV_OC); em branco = qualquer
                      (o mesmo número pode existir em tipos diferentes)

   Como cadastrar no RM:
     1. Gestão › Consultas SQL › Incluir. Código sugerido:
        CUBO.SUP.OCDOC  (sistema: o mesmo da CUBO.SUP.OC)
     2. Cole, salve e teste com uma OC conhecida.
     3. Se o RM acusar "nome de coluna inválido", comente (--)
        a linha indicada: os campos [opcional] variam conforme a
        versão/customização do RM.
     4. Libere para os mesmos usuários da CUBO.SUP.OC e informe o
        código no app (Configurações › Consultas TOTVS).

   Teste no navegador (substitua os valores):
     .../RealizaConsulta/CUBO.SUP.OCDOC/0/T?parameters=CODCOLIGADA_N=48;NUMEROMOV_S=000123;CODTMV_S=1.1.12
   ========================================================= */

SELECT

    /* ── obra (coligada) ── */
    OC.CODCOLIGADA                                  AS COD_OBRA,
    COL.NOME                                        AS OBRA_RAZAO_SOCIAL,
    CASE WHEN OC.CODCOLIGADA = 2 THEN 'IMPPER LOUNGE' ELSE COL.NOMEFANTASIA END
                                                    AS OBRA,
    COL.CGC                                         AS OBRA_CNPJ,
    COL.RUA                                         AS OBRA_RUA,               -- [opcional]
    COL.NUMERO                                      AS OBRA_NUMERO,            -- [opcional]
    COL.COMPLEMENTO                                 AS OBRA_COMPLEMENTO,       -- [opcional]
    COL.BAIRRO                                      AS OBRA_BAIRRO,            -- [opcional]
    COL.CIDADE                                      AS OBRA_CIDADE,            -- [opcional]
    COL.ESTADO                                      AS OBRA_UF,                -- [opcional]
    COL.CEP                                         AS OBRA_CEP,               -- [opcional]
    COL.TELEFONE                                    AS OBRA_TELEFONE,          -- [opcional]

    /* ── OC ── */
    OC.IDMOV                                        AS IDMOV_OC,
    OC.NUMEROMOV                                    AS NUMERO_OC,
    OC.CODTMV                                       AS CODTMV_OC,
    CONVERT(VARCHAR(10), OC.DATAEMISSAO, 103)       AS DATA_EMISSAO_OC,
    CONVERT(VARCHAR(10), OC.DATACRIACAO, 103)       AS DATA_CRIACAO_OC,
    CONVERT(VARCHAR(10), APO.DATA_APROVACAO_OC, 103) AS DATA_APROVACAO_OC,
    CASE WHEN APO.DATA_APROVACAO_OC IS NOT NULL THEN 'APROVADA' ELSE 'PENDENTE' END
                                                    AS SITUACAO_APROVACAO_OC,
    CASE WHEN OC.DATACANCELAMENTOMOV IS NOT NULL THEN 'CANCELADA' ELSE 'NÃO CANCELADA' END
                                                    AS SITUACAO_CANCELAMENTO_OC,

    /* ── comprador (quem criou a OC) ── */
    OC.USUARIOCRIACAO                               AS COMPRADOR_LOGIN,
    USU.NOME                                        AS COMPRADOR_NOME,
    USU.EMAIL                                       AS COMPRADOR_EMAIL,        -- [opcional]

    /* ── fornecedor ── */
    OC.CODCFO                                       AS COD_FORNECEDOR,
    FORN.NOME                                       AS FORNECEDOR_RAZAO_SOCIAL,
    COALESCE(NULLIF(LTRIM(RTRIM(FORN.NOMEFANTASIA)),''), FORN.NOME)
                                                    AS FORNECEDOR,
    FORN.CGCCFO                                     AS FORNECEDOR_CNPJ,
    FORN.INSCRESTADUAL                              AS FORNECEDOR_IE,          -- [opcional]
    FORN.RUA                                        AS FORNECEDOR_RUA,
    FORN.NUMERO                                     AS FORNECEDOR_NUMERO,
    FORN.BAIRRO                                     AS FORNECEDOR_BAIRRO,
    FORN.CIDADE                                     AS FORNECEDOR_CIDADE,
    FORN.CODETD                                     AS FORNECEDOR_UF,
    FORN.CEP                                        AS FORNECEDOR_CEP,
    FORN.TELEFONE                                   AS FORNECEDOR_TELEFONE,
    FORN.EMAIL                                      AS FORNECEDOR_EMAIL,
    FORN.CONTATO                                    AS FORNECEDOR_CONTATO,     -- [opcional]

    /* ── pagamento, frete e totais ── */
    OC.CODCPG                                       AS COD_CONDICAO_PAGAMENTO,
    CPG.NOME                                        AS CONDICAO_PAGAMENTO,
    CAST(FORN.FORMAPAGAMENTO AS VARCHAR(100))       AS FORMA_PAGAMENTO,
    CASE OC.FRETECIFOUFOB                                                      -- [opcional]
        WHEN 1 THEN 'CIF'
        WHEN 2 THEN 'FOB'
        ELSE NULL
    END                                             AS TIPO_FRETE,
    OC.VALORBRUTO                                   AS VALOR_BRUTO_OC,
    OC.VALORDESC                                    AS VALOR_DESCONTO_OC,
    OC.VALORFRETE                                   AS VALOR_FRETE_OC,         -- [opcional]
    OC.VALOROUTROS                                  AS VALOR_OUTROS_OC,        -- [opcional]
    OC.VALORLIQUIDO                                 AS VALOR_TOTAL_OC,

    /* ── observações ── */
    CAST(HIS.HISTORICOCURTO AS VARCHAR(1000))       AS OBSERVACAO_OC,
    CAST(HIS.HISTORICOLONGO AS VARCHAR(4000))       AS OBSERVACAO_OC_LONGA,    -- [opcional]

    /* ── projeto e centro de custo ── */
    PROJ.CODPRJ                                     AS CODIGO_PROJETO,
    PROJ.DESCRICAO                                  AS PROJETO,
    CC.NOME                                         AS CENTRO_CUSTO,

    /* ── item ── */
    I.NSEQITMMOV                                    AS ITEM_OC,
    PROD.CODIGOPRD                                  AS CODIGO_INSUMO,
    PROD.NOMEFANTASIA                               AS NOME_INSUMO,
    CASE WHEN PROD.TIPO = 'S' THEN 'SERVIÇO' ELSE 'PRODUTO' END AS TIPO_INSUMO,   -- TPRODUTO.TIPO: P = produto, S = serviço
    I.CODUND                                        AS UNIDADE,
    I.QUANTIDADEORIGINAL                            AS QUANTIDADE,
    I.PRECOUNITARIO                                 AS PRECO_UNITARIO,
    CASE
        WHEN COALESCE(I.VALORTOTALITEM,0) <> 0 THEN I.VALORTOTALITEM
        ELSE COALESCE(I.QUANTIDADEORIGINAL,0) * COALESCE(I.PRECOUNITARIO,0)
    END                                             AS VALOR_TOTAL_ITEM,
    CONVERT(VARCHAR(10), I.DATAENTREGA, 103)        AS DATA_ENTREGA_ITEM,
    CAST(HIT.HISTORICOLONGO AS VARCHAR(2000))       AS OBSERVACAO_ITEM,        -- [opcional]

    /* ── SC de origem do item ── */
    SCI.NUMERO_SC                                   AS NUMERO_SC

FROM TMOV OC (NOLOCK)

INNER JOIN TITMMOV I (NOLOCK)
    ON  I.CODCOLIGADA = OC.CODCOLIGADA
    AND I.IDMOV       = OC.IDMOV

LEFT JOIN GCOLIGADA COL (NOLOCK)
    ON  COL.CODCOLIGADA = OC.CODCOLIGADA

LEFT JOIN FCFO FORN (NOLOCK)
    ON  FORN.CODCFO      = OC.CODCFO
    AND FORN.CODCOLIGADA = 0                 -- igual à CUBO.SUP.OC

LEFT JOIN TCPG CPG (NOLOCK)
    ON  CPG.CODCOLIGADA = OC.CODCOLIGADA
    AND CPG.CODCPG      = OC.CODCPG

LEFT JOIN GUSUARIO USU (NOLOCK)
    ON  USU.CODUSUARIO = OC.USUARIOCRIACAO

LEFT JOIN TPRODUTO PROD (NOLOCK)
    ON  PROD.IDPRD = I.IDPRD

LEFT JOIN MPRJ PROJ (NOLOCK)
    ON  PROJ.CODCOLIGADA = OC.CODCOLIGADA
    AND PROJ.IDPRJ       = COALESCE(I.IDPRJ, OC.IDPRJ)

LEFT JOIN GCCUSTO CC (NOLOCK)
    ON  CC.CODCOLIGADA = OC.CODCOLIGADA
    AND CC.CODCCUSTO   = COALESCE(I.CODCCUSTO, OC.CODCCUSTO)

LEFT JOIN TMOVHISTORICO HIS (NOLOCK)                                          -- observação da OC (histórico curto e longo)
    ON  HIS.CODCOLIGADA = OC.CODCOLIGADA
    AND HIS.IDMOV       = OC.IDMOV

LEFT JOIN TITMMOVHISTORICO HIT (NOLOCK)                                       -- [opcional]
    ON  HIT.CODCOLIGADA = I.CODCOLIGADA
    AND HIT.IDMOV       = I.IDMOV
    AND HIT.NSEQITMMOV  = I.NSEQITMMOV

/* SC(s) de origem do item, pela relação item a item */
OUTER APPLY
(
    SELECT STRING_AGG(CAST(SC.NUMEROMOV AS VARCHAR(MAX)), ', ') AS NUMERO_SC
    FROM TITMMOVRELAC R (NOLOCK)
    INNER JOIN TMOV SC (NOLOCK)
        ON  SC.CODCOLIGADA = R.CODCOLORIGEM
        AND SC.IDMOV       = R.IDMOVORIGEM
    WHERE R.CODCOLDESTINO     = I.CODCOLIGADA
      AND R.IDMOVDESTINO      = I.IDMOV
      AND R.NSEQITMMOVDESTINO = I.NSEQITMMOV
) SCI

/* data de aprovação da OC — mesma regra da CUBO.SUP.OC (atendimento tipo 12, status F) */
OUTER APPLY
(
    SELECT MAX(HSX.DATA) AS DATA_APROVACAO_OC
    FROM TMOVATEND ATX (NOLOCK)
    INNER JOIN HATENDIMENTOBASE HX (NOLOCK)
        ON  HX.CODCOLIGADA        = ATX.CODCOLIGADAATEND
        AND HX.CODATENDIMENTO     = ATX.CODATENDIMENTO
        AND HX.CODTIPOATENDIMENTO = 12
    INNER JOIN HSTATUSATEND HSX (NOLOCK)
        ON  HSX.CODCOLIGADA    = HX.CODCOLIGADA
        AND HSX.CODLOCAL       = HX.CODLOCAL
        AND HSX.CODATENDIMENTO = HX.CODATENDIMENTO
        AND HSX.CODSTATUS      = 'F'
        AND HSX.DATA IS NOT NULL
    WHERE ATX.CODCOLIGADA = OC.CODCOLIGADA
      AND ATX.IDMOV       = OC.IDMOV
) APO

WHERE
    OC.CODCOLIGADA = :CODCOLIGADA_N
    AND OC.NUMEROMOV = :NUMEROMOV_S
    AND (:CODTMV_S = '' OR OC.CODTMV = :CODTMV_S)

ORDER BY
    I.NSEQITMMOV;
