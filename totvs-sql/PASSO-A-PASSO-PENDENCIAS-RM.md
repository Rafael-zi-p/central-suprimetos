# Pendências do RM: passo a passo (histórico, já resolvido)

> **A TI não precisa fazer nada deste arquivo.** Ele registra como as consultas novas foram levantadas e validadas. As consultas já estão criadas no RM; a lista final está em `PARA-CRIAR-NO-RM/LEIA-ME.md`, e a TI só precisa liberá-las para o usuário de serviço.

Faça tudo no RM em **Gestão › Consultas SQL**. Siga esta ordem para evitar retrabalho.

---

## 1. Colunas da MTAREFA

1. Clique em **Incluir**, dê um código provisório (ex.: `TMP.MTAREFA`) e cole:

   ```sql
   SELECT COLUMN_NAME, DATA_TYPE
   FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_NAME = 'MTAREFA'
   ORDER BY ORDINAL_POSITION
   ```

2. **Execute.** Se der erro de permissão, troque o texto por este e execute de novo:

   ```sql
   SELECT TOP 5 * FROM MTAREFA WHERE CODCOLIGADA = 46
   ```

3. **Mande** um print ou cole o resultado.
4. Depois pode **excluir** a consulta provisória.

## 2. Texto da CUBO.SUP.ORC

1. Abra a **CUBO.SUP.ORC** e vá na aba do texto da consulta.
2. **Ctrl+A**, **Ctrl+C** e cole na conversa.
3. Escreva junto, em uma linha, o que queria ver nela (ex.: "orçado por etapa e insumo de cada obra").

## 3. Testar a CUBO.SUP.CRONO

1. Descubra o número do projeto de uma obra (consulta provisória). Troque `46` pela coligada que quiser testar:

   ```sql
   SELECT TOP 20 * FROM MPRJ WHERE CODCOLIGADA = 46
   ```

   Anote o **IDPRJ** do projeto da obra.

2. Abra a **CUBO.SUP.CRONO** e execute. Ela pede dois parâmetros:
   - `CODCOLIGADA_N`: a coligada (ex.: `46`);
   - `IDPRJ_N`: o IDPRJ anotado.

3. **O que mandar:**
   - **Se rodou:** quantas linhas vieram e um print das primeiras.
   - **Se der "nome de coluna inválido":** print do erro (as colunas do passo 1 resolvem).

## 4. Liberar as consultas para o usuário de serviço

O app lê o TOTVS por **um único usuário de serviço** (o que a TI definir). Libere para ele **todas** as consultas:
**CUBO.SUP.SC, CUBO.SUP.OC, CUBO.SUP.INS, CUBO.SUP.FORN, CUBO.SUP.OCDOC, CUBO.SUP.CRONO, CUBO.SUP.ORC** e a de Verbas.

1. Faça a mesma liberação já feita na **CUBO.SUP.OC**, só que para o usuário de serviço.
2. Confira se o **sistema** de cada uma é o mesmo da CUBO.SUP.OC (letra **T**). A de Verbas (CUBO7.12) continua no sistema dela (**M**).
3. Enquanto o usuário de serviço não existir, libere para o seu usuário, para conseguir fazer o teste do passo 5.

Sem isso, o teste do passo 5 dá erro de permissão.

## 5. Ligar no app e testar as colunas

No app, abra **Configurações › Consultas TOTVS**. Para cada aba da tabela abaixo:

1. clique na aba;
2. digite o código;
3. clique em **Testar e listar colunas**;
4. clique em **Salvar**.

| Aba | Código | O que conferir |
|---|---|---|
| SC | `CUBO.SUP.SC` | Troque o `CUBO.SUP.005`. Confira se **DATA_APROVACAO_SC** aparece como "encontrada no retorno". |
| Fornecedores | `CUBO.SUP.FORN` | Se trouxe e-mail e telefone. |
| PDF da OC | `CUBO.SUP.OCDOC` | Usa uma OC de amostra sozinho. |
| Cronograma | `CUBO.SUP.CRONO` | Parâmetros `CODCOLIGADA_N` e `IDPRJ_N`. |

**Mande** um print de cada aba depois do teste, principalmente se alguma coluna aparecer como **"não veio no retorno"**.

---

## Checklist

- [ ] 1. Colunas da MTAREFA enviadas
- [ ] 2. Texto da CUBO.SUP.ORC enviado
- [ ] 3. CUBO.SUP.CRONO testada (linhas ou erro enviados)
- [ ] 4. Consultas liberadas para o usuário de serviço (SC, OC, INS, FORN, OCDOC, CRONO, ORC, Verbas)
- [ ] 5. Consultas ligadas e testadas no app (prints enviados)

Com 1, 2 e 3 dá para fechar as consultas do cronograma e do orçamento. Com 5, passam a funcionar a data real de aprovação da SC, o PDF completo da OC e o contato do fornecedor.
