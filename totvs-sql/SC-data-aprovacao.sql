/* =========================================================
   DATA DE APROVAÇÃO DA SC — trecho para a consulta de SC
   (a que alimenta a aba SC do app)

   Por quê: os prazos do SLA (da obra e dos compradores) contam
   da APROVAÇÃO da SC. Sem esta coluna, o app usa a data que a
   consulta de OC já traz (só para SCs que viraram OC) ou estima
   pelo ciclo do CUBO.

   Lógica: a mesma da consulta CUBO.SUP.OC (bloco SC_APROVACAO):
   atendimentos dos tipos 5 e 16, status F (aprovação), data em
   HSTATUSATEND.DATA; fica a aprovação mais recente.

   Como usar:
   1. Na consulta de SC, onde a SC é lida da TMOV (aqui com o
      apelido M), acrescente o OUTER APPLY abaixo antes do WHERE.
   2. Acrescente a coluna  APR.DATA_APROVACAO_SC  no SELECT.
   3. Troque "M" pelo apelido que a TMOV tem na sua consulta.
   4. Teste no TOTVS antes de salvar a consulta.
   O app reconhece a coluna pelo nome DATA_APROVACAO_SC.
   ========================================================= */

/* no SELECT: */
--  , APR.DATA_APROVACAO_SC

/* antes do WHERE: */
OUTER APPLY
(
    SELECT TOP 1
        HS.DATA AS DATA_APROVACAO_SC
    FROM TMOVATEND SAT (NOLOCK)
    INNER JOIN HATENDIMENTOBASE SH (NOLOCK)
        ON  SH.CODCOLIGADA = SAT.CODCOLIGADAATEND
        AND SH.CODATENDIMENTO = SAT.CODATENDIMENTO
        AND SH.CODTIPOATENDIMENTO IN (5, 16)
    INNER JOIN HSTATUSATEND HS (NOLOCK)
        ON  HS.CODCOLIGADA = SH.CODCOLIGADA
        AND HS.CODLOCAL = SH.CODLOCAL
        AND HS.CODATENDIMENTO = SH.CODATENDIMENTO
        AND HS.CODSTATUS = 'F'
        AND HS.DATA IS NOT NULL
    WHERE SAT.CODCOLIGADA = M.CODCOLIGADA
      AND SAT.IDMOV = M.IDMOV
    ORDER BY HS.DATA DESC, SAT.CODATENDIMENTO DESC
) APR
