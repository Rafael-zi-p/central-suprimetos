/* =========================================================
   CUBO.SUP.FORN — cadastro de fornecedores (aba Fornecedores)
   ---------------------------------------------------------
   Uma linha por fornecedor do cadastro do RM (FCFO).
   Sem parâmetros. Consulta só de leitura.

   O app cruza com as OCs que já sincroniza (CUBO.SUP.OC) pelo
   COD_FORNECEDOR (= OC.CODCFO) e pelo CNPJ: histórico de compras,
   preços, prazos de entrega e obras atendidas são calculados no
   app — por isso esta consulta fica leve (o proxy corta em 26 s).

   Como cadastrar no RM:
     1. Gestão › Consultas SQL › Incluir. Código sugerido:
        CUBO.SUP.FORN   (sistema: o mesmo da CUBO.SUP.OC)
     2. Cole este SQL, salve e execute para testar.
     3. Se o RM acusar "nome de coluna inválido", comente (--)
        a linha indicada: os campos marcados com [opcional]
        variam conforme a versão/customização do RM.
     4. Libere a consulta para os mesmos usuários da CUBO.SUP.OC.
     5. Informe o código no app: Configurações › Consultas TOTVS.
   ========================================================= */

SELECT

    /* ── identificação ── */
    F.CODCOLIGADA                                   AS COD_COLIGADA_CADASTRO,  -- 0 = cadastro global
    F.CODCFO                                        AS COD_FORNECEDOR,
    F.NOME                                          AS RAZAO_SOCIAL,
    COALESCE(NULLIF(LTRIM(RTRIM(F.NOMEFANTASIA)),''), F.NOME)
                                                    AS NOME_FANTASIA,
    F.CGCCFO                                        AS CNPJ_CPF,
    F.INSCRESTADUAL                                 AS INSCRICAO_ESTADUAL,     -- [opcional]

    CASE F.PESSOAFISOUJUR
        WHEN 'F' THEN 'FÍSICA'
        ELSE 'JURÍDICA'
    END                                             AS TIPO_PESSOA,            -- [opcional]

    CASE F.PAGREC
        WHEN 1 THEN 'CLIENTE'
        WHEN 2 THEN 'FORNECEDOR'
        WHEN 3 THEN 'CLIENTE E FORNECEDOR'
        ELSE CAST(F.PAGREC AS VARCHAR(10))
    END                                             AS CLASSIFICACAO,

    CASE WHEN F.ATIVO = 1 THEN 'ATIVO' ELSE 'INATIVO' END
                                                    AS SITUACAO,

    /* ── endereço ── */
    F.RUA                                           AS RUA,
    F.NUMERO                                        AS NUMERO,
    F.COMPLEMENTO                                   AS COMPLEMENTO,
    F.BAIRRO                                        AS BAIRRO,
    F.CIDADE                                        AS CIDADE,
    F.CODETD                                        AS UF,
    F.CEP                                           AS CEP,

    /* ── contato (usado no e-mail de envio da OC) ── */
    F.TELEFONE                                      AS TELEFONE,
    F.FAX                                           AS TELEFONE_2,             -- [opcional]
    F.EMAIL                                         AS EMAIL,
    F.CONTATO                                       AS CONTATO,                -- [opcional]

    /* ── pagamento ── */
    CASE
        WHEN NULLIF(LTRIM(RTRIM(CAST(F.FORMAPAGAMENTO AS VARCHAR(100)))),'') IS NULL
        THEN 'NÃO INFORMADO'
        ELSE CAST(F.FORMAPAGAMENTO AS VARCHAR(100))
    END                                             AS FORMA_PAGAMENTO

FROM FCFO F (NOLOCK)

WHERE
    F.CODCOLIGADA = 0           -- cadastro global (o mesmo que as OCs usam); sem isso o fornecedor se repete por coligada
    AND F.PAGREC IN (2, 3)      -- fornecedor ou cliente e fornecedor
;
