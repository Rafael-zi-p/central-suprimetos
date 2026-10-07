// Monta CUBO.SUP.OC-otimizada.sql: novos blocos WITH + a MESMA lista de colunas da consulta original (copiada do arquivo)
const fs=require("fs"), path=require("path");
const orig=fs.readFileSync(path.join(__dirname,"CUBO.SUP.OC-mes-a-mes.sql"),"utf8");
const ini=orig.indexOf("SELECT\n\n    /* =====================================================\n       IDENTIFICAÇÃO");
const fim=orig.indexOf("FROM TMOV OC (NOLOCK)", ini);
if(ini<0||fim<0) throw new Error("não achei o bloco de colunas");
let colunas=orig.slice(ini, fim).split("APO.DATA_APROVACAO_OC").join("AP.DATA_APROVACAO_OC");

const cab=`/* =========================================================
   CUBO.SUP.OC — versão OTIMIZADA (mesmas colunas, mesma ordem)
   ---------------------------------------------------------
   Devolve exatamente as mesmas colunas da versão anterior: o app
   não muda nada. O que mudou para ficar mais rápida:

   1. Aprovação da SC: antes varria TODAS as aprovações de SC do
      banco (todos os anos) e ordenava tudo antes de filtrar — e
      fazia isso duas vezes. Agora busca só as SCs ligadas às OCs
      do mês, uma vez por SC (OUTER APPLY com TOP 1).
   2. Aprovação da OC: antes era buscada uma vez por ITEM; agora
      uma vez por OC.
   3. SC por OC é derivada da mesma lista de SCs (sem repetir as
      junções), e os DISTINCT desnecessários saíram.
   4. As OCs do período são lidas direto da TMOV (filtro de
      coligada + data na própria tabela), com a mesma regra de
      antes: OC = movimento com atendimento de aprovação tipo 12.

   Como validar antes de trocar:
     Rode a versão antiga e esta para o MESMO mês e compare o nº
     de linhas e a soma de VALOR_TOTAL_ITEM. Têm de ser iguais.
     Depois, no app, Configurações › Consultas TOTVS › Testar.

   Parâmetros: :DATAINI_D e :DATAFIM_D (iguais aos de antes).
   ========================================================= */

WITH

/* OCs do período (cabeçalho) — base de tudo */
OC_PER AS
(
    SELECT
        M.CODCOLIGADA, M.IDMOV
    FROM TMOV M (NOLOCK)
    WHERE
        M.CODCOLIGADA IN (2, 7, 35, 36, 39, 40, 44, 46, 48, 51, 52, 63)
        AND M.DATACRIACAO >= :DATAINI_D
        AND M.DATACRIACAO <  DATEADD(DAY, 1, :DATAFIM_D)
        AND EXISTS
        (
            SELECT 1
            FROM TMOVATEND AT (NOLOCK)
            INNER JOIN HATENDIMENTOBASE H (NOLOCK)
                ON  H.CODCOLIGADA        = AT.CODCOLIGADAATEND
                AND H.CODATENDIMENTO     = AT.CODATENDIMENTO
                AND H.CODTIPOATENDIMENTO = 12
            WHERE AT.CODCOLIGADA = M.CODCOLIGADA
              AND AT.IDMOV       = M.IDMOV
        )
),

/* aprovação da OC — uma vez por OC (mesma regra de antes) */
APROV_OC AS
(
    SELECT
        O.CODCOLIGADA, O.IDMOV,
        X.CODATENDIMENTO, X.CODSTATUS, X.ABERTURA, X.FECHAMENTO, X.CODATENDENTE, X.CODATENDENTERESP,
        D.DATA_APROVACAO_OC
    FROM OC_PER O
    OUTER APPLY
    (
        SELECT TOP 1
            ATX.CODATENDIMENTO, ATX.CODCOLIGADAATEND, HX.CODLOCAL, HX.CODSTATUS,
            HX.ABERTURA, HX.FECHAMENTO, HX.CODATENDENTE, HX.CODATENDENTERESP
        FROM TMOVATEND ATX (NOLOCK)
        INNER JOIN HATENDIMENTOBASE HX (NOLOCK)
            ON  HX.CODCOLIGADA        = ATX.CODCOLIGADAATEND
            AND HX.CODATENDIMENTO     = ATX.CODATENDIMENTO
            AND HX.CODTIPOATENDIMENTO = 12
        WHERE ATX.CODCOLIGADA = O.CODCOLIGADA
          AND ATX.IDMOV       = O.IDMOV
        ORDER BY CASE WHEN HX.FECHAMENTO IS NULL THEN 0 ELSE 1 END, HX.ABERTURA DESC, ATX.CODATENDIMENTO DESC
    ) X
    OUTER APPLY
    (
        SELECT MAX(HSX.DATA) AS DATA_APROVACAO_OC
        FROM HSTATUSATEND HSX (NOLOCK)
        WHERE HSX.CODCOLIGADA    = X.CODCOLIGADAATEND
          AND HSX.CODLOCAL       = X.CODLOCAL
          AND HSX.CODATENDIMENTO = X.CODATENDIMENTO
          AND HSX.CODSTATUS      = 'F'
          AND HSX.DATA IS NOT NULL
    ) D
),

/* SCs ligadas às OCs do período (nível do movimento) */
REL_SC AS
(
    SELECT DISTINCT
        R.CODCOLDESTINO AS CODCOLIGADA, R.IDMOVDESTINO AS IDMOV_OC,
        R.CODCOLORIGEM  AS CODCOLIGADA_SC, R.IDMOVORIGEM AS IDMOV_SC
    FROM TMOVRELAC R (NOLOCK)
    INNER JOIN OC_PER O
        ON  O.CODCOLIGADA = R.CODCOLDESTINO
        AND O.IDMOV       = R.IDMOVDESTINO
),

/* dados da SC + aprovação (tipos 5 e 16, status F) — UMA busca por SC, só das SCs acima */
SC_DADOS AS
(
    SELECT
        S.CODCOLIGADA_SC, S.IDMOV_SC,
        SC.NUMEROMOV AS NUMERO_SC, SC.CODTMV AS CODTMV_SC,
        SC.DATAEMISSAO AS DATA_EMISSAO_SC, SC.DATACRIACAO AS DATA_CRIACAO_SC, SC.USUARIOCRIACAO AS GERADO_POR_SC,
        A.DATA_APROVACAO_SC, A.CODATENDIMENTO_APROVACAO_SC, A.CODTIPOATENDIMENTO_APROVACAO_SC
    FROM (SELECT DISTINCT CODCOLIGADA_SC, IDMOV_SC FROM REL_SC) S
    INNER JOIN TMOV SC (NOLOCK)
        ON  SC.CODCOLIGADA = S.CODCOLIGADA_SC
        AND SC.IDMOV       = S.IDMOV_SC
    OUTER APPLY
    (
        SELECT TOP 1
            HS.DATA AS DATA_APROVACAO_SC,
            SAT.CODATENDIMENTO AS CODATENDIMENTO_APROVACAO_SC,
            SH.CODTIPOATENDIMENTO AS CODTIPOATENDIMENTO_APROVACAO_SC
        FROM TMOVATEND SAT (NOLOCK)
        INNER JOIN HATENDIMENTOBASE SH (NOLOCK)
            ON  SH.CODCOLIGADA        = SAT.CODCOLIGADAATEND
            AND SH.CODATENDIMENTO     = SAT.CODATENDIMENTO
            AND SH.CODTIPOATENDIMENTO IN (5, 16)
        INNER JOIN HSTATUSATEND HS (NOLOCK)
            ON  HS.CODCOLIGADA    = SH.CODCOLIGADA
            AND HS.CODLOCAL       = SH.CODLOCAL
            AND HS.CODATENDIMENTO = SH.CODATENDIMENTO
            AND HS.CODSTATUS      = 'F'
            AND HS.DATA IS NOT NULL
        WHERE SAT.CODCOLIGADA = S.CODCOLIGADA_SC
          AND SAT.IDMOV       = S.IDMOV_SC
        ORDER BY HS.DATA DESC, SAT.CODATENDIMENTO DESC
    ) A
),

/* SCs por OC (fallback quando o item não tem vínculo próprio) */
SC_VINCULADAS AS
(
    SELECT
        R.CODCOLIGADA, R.IDMOV_OC,
        COUNT(*)                                                   AS QTD_SC_VINCULADAS,
        STRING_AGG(CAST(D.NUMERO_SC AS VARCHAR(MAX)), ', ')        AS NUMERO_SC,
        STRING_AGG(CAST(D.CODTMV_SC AS VARCHAR(MAX)), ', ')        AS CODTMV_SC,
        MIN(D.DATA_CRIACAO_SC)                                     AS DATA_CRIACAO_SC,
        MIN(D.DATA_EMISSAO_SC)                                     AS DATA_EMISSAO_SC,
        MAX(D.DATA_APROVACAO_SC)                                   AS DATA_APROVACAO_SC,
        STRING_AGG(CAST(D.GERADO_POR_SC AS VARCHAR(MAX)), ', ')    AS GERADO_POR_SC
    FROM REL_SC R
    INNER JOIN SC_DADOS D
        ON  D.CODCOLIGADA_SC = R.CODCOLIGADA_SC
        AND D.IDMOV_SC       = R.IDMOV_SC
    GROUP BY R.CODCOLIGADA, R.IDMOV_OC
),

/* SC por ITEM da OC (relação item a item) */
SC_ITEM_VINCULADAS AS
(
    SELECT
        R.CODCOLDESTINO AS CODCOLIGADA, R.IDMOVDESTINO AS IDMOV_OC, R.NSEQITMMOVDESTINO AS ITEM_OC,
        COUNT(DISTINCT R.IDMOVORIGEM)                              AS QTD_SC_ITEM,
        STRING_AGG(CAST(D.NUMERO_SC AS VARCHAR(MAX)), ', ')        AS NUMERO_SC_ITEM,
        STRING_AGG(CAST(D.CODTMV_SC AS VARCHAR(MAX)), ', ')        AS CODTMV_SC_ITEM,
        MIN(D.DATA_CRIACAO_SC)                                     AS DATA_CRIACAO_SC_ITEM,
        MIN(D.DATA_EMISSAO_SC)                                     AS DATA_EMISSAO_SC_ITEM,
        MAX(D.DATA_APROVACAO_SC)                                   AS DATA_APROVACAO_SC_ITEM,
        MIN(SI.DATAENTREGA)                                        AS DATA_NECESSIDADE_SC,
        MAX(SI.DATAENTREGA)                                        AS DATA_NECESSIDADE_SC_ULTIMA,
        STRING_AGG(CAST(D.GERADO_POR_SC AS VARCHAR(MAX)), ', ')    AS GERADO_POR_SC_ITEM,
        MAX(D.CODATENDIMENTO_APROVACAO_SC)                         AS CODATENDIMENTO_APROVACAO_SC,
        MAX(D.CODTIPOATENDIMENTO_APROVACAO_SC)                     AS CODTIPOATENDIMENTO_APROVACAO_SC
    FROM TITMMOVRELAC R (NOLOCK)
    INNER JOIN OC_PER O
        ON  O.CODCOLIGADA = R.CODCOLDESTINO
        AND O.IDMOV       = R.IDMOVDESTINO
    INNER JOIN SC_DADOS D
        ON  D.CODCOLIGADA_SC = R.CODCOLORIGEM
        AND D.IDMOV_SC       = R.IDMOVORIGEM
    INNER JOIN TITMMOV SI (NOLOCK)
        ON  SI.CODCOLIGADA = R.CODCOLORIGEM
        AND SI.IDMOV       = R.IDMOVORIGEM
        AND SI.NSEQITMMOV  = R.NSEQITMMOVORIGEM
    GROUP BY R.CODCOLDESTINO, R.IDMOVDESTINO, R.NSEQITMMOVDESTINO
),

/* recebimento por item da OC (mesma regra de antes) */
RECEBIMENTO AS
(
    SELECT
        R.CODCOLORIGEM AS CODCOLIGADA, R.IDMOVORIGEM AS IDMOV_OC, R.NSEQITMMOVORIGEM AS ITEM_OC,
        SUM(COALESCE(R.QUANTIDADE,0))                                                          AS QUANTIDADE_RECEBIDA,
        SUM(COALESCE(R.VALORRECEBIDO,0))                                                       AS VALOR_RECEBIDO_RM,
        SUM(CASE WHEN COALESCE(R.VALORRECEBIDO,0) <> 0 THEN R.VALORRECEBIDO
                 WHEN COALESCE(R.QUANTIDADE,0) <> 0 AND COALESCE(I.PRECOUNITARIO,0) <> 0 THEN R.QUANTIDADE * I.PRECOUNITARIO
                 ELSE 0 END)                                                                   AS VALOR_RECEBIDO,
        COUNT(DISTINCT R.IDMOVDESTINO)                                                         AS QTD_DOCUMENTOS_ENTRADA,
        STRING_AGG(CAST(NF.NUMEROMOV AS VARCHAR(MAX)), ', ')                                   AS NUMEROS_DOCUMENTOS_ENTRADA,
        MIN(CASE WHEN COALESCE(R.QUANTIDADE,0) > 0 THEN NF.DATACRIACAO END)                    AS DATA_PRIMEIRO_RECEBIMENTO,
        MAX(CASE WHEN COALESCE(R.QUANTIDADE,0) > 0 THEN NF.DATACRIACAO END)                    AS DATA_ULTIMO_RECEBIMENTO
    FROM TITMMOVRELAC R (NOLOCK)
    INNER JOIN OC_PER O
        ON  O.CODCOLIGADA = R.CODCOLORIGEM
        AND O.IDMOV       = R.IDMOVORIGEM
    INNER JOIN TITMMOV I (NOLOCK)
        ON  I.CODCOLIGADA = R.CODCOLORIGEM
        AND I.IDMOV       = R.IDMOVORIGEM
        AND I.NSEQITMMOV  = R.NSEQITMMOVORIGEM
    LEFT JOIN TMOV NF (NOLOCK)
        ON  NF.CODCOLIGADA = R.CODCOLDESTINO
        AND NF.IDMOV       = R.IDMOVDESTINO
    GROUP BY R.CODCOLORIGEM, R.IDMOVORIGEM, R.NSEQITMMOVORIGEM
)

`;

const rodape=`FROM OC_PER OX

INNER JOIN TMOV OC (NOLOCK)
    ON  OC.CODCOLIGADA = OX.CODCOLIGADA
    AND OC.IDMOV       = OX.IDMOV

INNER JOIN TITMMOV I (NOLOCK)
    ON  I.CODCOLIGADA = OC.CODCOLIGADA
    AND I.IDMOV       = OC.IDMOV

LEFT JOIN APROV_OC AP
    ON  AP.CODCOLIGADA = OC.CODCOLIGADA
    AND AP.IDMOV       = OC.IDMOV

LEFT JOIN GCOLIGADA COL (NOLOCK)
    ON  COL.CODCOLIGADA = OC.CODCOLIGADA

LEFT JOIN SC_VINCULADAS SCV
    ON  SCV.CODCOLIGADA = OC.CODCOLIGADA
    AND SCV.IDMOV_OC    = OC.IDMOV

LEFT JOIN SC_ITEM_VINCULADAS SCIV
    ON  SCIV.CODCOLIGADA = OC.CODCOLIGADA
    AND SCIV.IDMOV_OC    = OC.IDMOV
    AND SCIV.ITEM_OC     = I.NSEQITMMOV

LEFT JOIN RECEBIMENTO RC
    ON  RC.CODCOLIGADA = OC.CODCOLIGADA
    AND RC.IDMOV_OC    = OC.IDMOV
    AND RC.ITEM_OC     = I.NSEQITMMOV

LEFT JOIN TPRODUTO PROD (NOLOCK)
    ON  PROD.IDPRD = I.IDPRD

LEFT JOIN FCFO FORN (NOLOCK)
    ON  FORN.CODCFO      = OC.CODCFO
    AND FORN.CODCOLIGADA = 0

LEFT JOIN TCPG CPG (NOLOCK)
    ON  CPG.CODCOLIGADA = OC.CODCOLIGADA
    AND CPG.CODCPG      = OC.CODCPG

LEFT JOIN MPRJ PROJ (NOLOCK)
    ON  PROJ.CODCOLIGADA = OC.CODCOLIGADA
    AND PROJ.IDPRJ       = COALESCE(I.IDPRJ, OC.IDPRJ)

LEFT JOIN GCCUSTO CC (NOLOCK)
    ON  CC.CODCOLIGADA = OC.CODCOLIGADA
    AND CC.CODCCUSTO   = COALESCE(I.CODCCUSTO, OC.CODCCUSTO)

ORDER BY
    OC.CODCOLIGADA,
    OC.DATACRIACAO,
    OC.NUMEROMOV,
    I.NSEQITMMOV;
`;
const out=cab+colunas+rodape;
// conferências: nenhum alias antigo sobrando
["OC_IDENTIFICADAS","APO.","SC_BASE","SC_APROVACAO"].forEach(function(t){ if(out.indexOf(t)>=0) throw new Error("sobrou "+t); });
fs.writeFileSync(path.join(__dirname,"CUBO.SUP.OC-otimizada.sql"), out);
// mesma lista de colunas?
const cols=s=>(s.match(/\)\s*AS\s+[A-Z_0-9]+|[A-Z_]+\.[A-Z_0-9]+\s+AS\s+[A-Z_0-9]+/g)||[]).map(x=>x.split(/\s+AS\s+/).pop());
console.log("ok · colunas:", cols(colunas).length);
