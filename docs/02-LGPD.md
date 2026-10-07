# LGPD: inventário, retenção e encerramento do ambiente de testes

> **Aviso:** este documento organiza o inventário e o passo a passo técnico. Bases legais, prazos de retenção e o texto da declaração precisam da confirmação do encarregado (DPO) e do Jurídico. Os pontos marcados com **[confirmar]** dependem disso. Não é parecer jurídico.

Atende, na parte técnica, a cláusula 8.3 do Termo.

---

## Parte 1. Inventário de dados pessoais (v3)

Controladora: a empresa (Termo, cláusula 8.2). Operador técnico: a TI, no PostgreSQL e no Coolify da empresa. Os dados do app ficam só no servidor da empresa, no Brasil.

| # | Dado pessoal | Titulares | Onde fica na v3 | Quem acessa | Base legal sugerida **[confirmar]** | Retenção sugerida **[confirmar]** |
|---|---|---|---|---|---|---|
| 1 | Nome, e-mail, telefone, perfil, permissões e obras liberadas | Colaboradores | tabela `perfis` | Administradores; cada pessoa vê o próprio | Execução do contrato de trabalho e gestão de acesso (art. 7º, V) ou legítimo interesse (art. 7º, IX) | Enquanto a pessoa tiver acesso; desativar o perfil ao desligar |
| 2 | Conta Microsoft (oid) e e-mail | Colaboradores | `perfis.auth_user_id` e sessão no Redis | Servidor | Igual ao item 1 | Sessão expira sozinha; vínculo some com o perfil |
| 3 | Departamento e carteira de insumos de cada comprador | Colaboradores | `departamentos`, `pessoa_insumos` | Quem tem o módulo CUBO | Legítimo interesse (gestão de compras) | Enquanto durar o vínculo |
| 4 | Anotações, tarefas e lembretes | Colaboradores | `anotacoes` (privadas ou compartilhadas) | O dono; compartilhadas, a equipe | Legítimo interesse | Até a pessoa apagar ou o perfil sair; **[confirmar]** o que fazer ao desligar |
| 5 | Notificações | Colaboradores | `notificacoes` | O destinatário; administrador | Legítimo interesse | **[confirmar]** (sugestão: 12 meses) |
| 6 | Chat da equipe | Colaboradores | `canal_eventos` | Remetente e destinatário (privado) | Legítimo interesse | **Automática:** apaga após `CHAT_RETENCAO_MIN` (padrão 240 min) |
| 7 | Auditoria: quem mudou o quê, com valores antes e depois | Colaboradores | `auditoria` | Só administrador | Obrigação de controle e legítimo interesse (rastreabilidade de compras) | **Sem limpeza automática hoje.** Definir prazo, ver Parte 3 |
| 8 | "Comprador do mês": desempenho individual e pontos | Colaboradores | `dados_compartilhados` e Mesa (`mc_*`) | Equipe (conforme a tela) | Legítimo interesse, com teste de balanceamento. **Atenção:** é avaliação individual (J15; art. 20 da LGPD) | **[confirmar]**; decidir antes se o ranking fica |
| 9 | Contatos da obra (GGO, GO, assistente, almoxarife: nome, telefone, e-mail) | Colaboradores | documento `obras_painel` | Quem tem o módulo Obras | Execução de contrato / legítimo interesse | Enquanto estiverem na obra |
| 10 | Contatos do fornecedor e do vendedor (nome, telefone, e-mail) | Pessoas de fornecedores | `dados_compartilhados` (documento do vendedor por fornecedor; **[conferir o tipo]**), PDF e e-mail da OC | Quem tem o módulo OC | Execução de contrato e procedimentos preliminares (art. 7º, V) | Enquanto durar a relação, mais o prazo fiscal da OC **[confirmar]** |
| 11 | Avaliação de fornecedores, com justificativas e quem avaliou | Fornecedores (CNPJ) e o almoxarife que avaliou | `dados_compartilhados` (`forn_aval_*`) | Quem tem Fornecedores | Legítimo interesse | **[confirmar]** |
| 12 | Razão social, CNPJ, dados de compras | Fornecedores | `totvs_arquivos` e telas | Equipe, por obra liberada | Execução de contrato; não é dado pessoal quando é pessoa jurídica | Acompanha a atualização do TOTVS (arquivos antigos são apagados a cada execução) |
| 13 | Regularizações: NF, valor, quem pediu, anexos (nome do arquivo) | Colaboradores e fornecedores | `dados_compartilhados` (`regz_*`) | Quem tem o módulo | Obrigação fiscal e legítimo interesse | Prazo fiscal **[confirmar]** |
| 13b | Contratações: quem abriu e aprovou cada etapa, fornecedor e CNPJ, valor, anexos (carta convite, planilha, mapa de aprovação, minuta e contrato assinado) | Colaboradores e pessoas de fornecedores | `pre_<id>` e `preanx_<id>` (`dados_compartilhados`) | Quem tem a aba Pré-Compras | Execução de contrato (art. 7º, V) e obrigação legal de guarda **[confirmar]** | Prazo de guarda de contratos **[confirmar]** |
| 14 | Calendário de home office e visitas | Colaboradores | `dados_compartilhados` (`home_office`, `visitas`) | Equipe | Legítimo interesse. **Atenção:** é dado de rotina de trabalho **[confirmar]** | **[confirmar]** |
| 15 | Foto de perfil (opcional) | Colaboradores | `dados_compartilhados` (`perfil_extra_<id>`) **[conferir se existe]** | Equipe | Consentimento livre e revogável, por ser opcional | Até a pessoa remover |
| 16 | Consulta de CNPJ na BrasilAPI | Fornecedores (dado público) | Não grava; só consulta | Navegador de quem consulta | Dado público da Receita | Não se aplica |
| 17 | Assistente com IA | Quem fizer a pergunta | **Desligado.** Se ligado, envia texto ao provedor | Provedor | Só com contrato, DPA e política **[confirmar]** | Não ligar antes disso |

**Transferência internacional (art. 33):** na v3 não existe. O assistente com IA vem desligado. Ao ligar, o provedor está no exterior e exige instrumento (cláusulas contratuais ou equivalente).

**O que o app não guarda:** senha de usuário (o login é Microsoft), credencial do TOTVS (fica só nas variáveis do servidor), cartão ou dado financeiro de pessoa física.

**Para o encarregado:** o registro das operações (art. 37) pode partir desta tabela. Faltam três decisões do negócio: o ranking "Comprador do mês" fica ou sai (J15); o prazo de retenção da auditoria; e o aviso de privacidade para colaboradores e fornecedores.

---

## Parte 2. Encerramento do ambiente de testes

Os testes foram feitos em **servidor local**, com **dados de teste**. O app novo **começa limpo**: não há migração nem dado a importar.

> Faça o encerramento só depois que o app novo estiver no ar e a homologação (`ENTREGA-COMPLETA.md` §10) tiver passado.

### 2.1 O que o autor apaga

**[Rafael]**

1. **Banco de testes local:** pare o servidor de testes e apague a pasta de dados do banco local e qualquer cópia exportada.
2. **Navegadores** usados nos testes: **F12 › Application › Storage › Clear site data** para o endereço de testes (por exemplo `localhost`). Isso apaga o IndexedDB e o localStorage do app.
3. **Arquivos no computador:** apague, do disco e da lixeira, backups e exportações de teste (`backup*.json`, planilhas `.xlsx` de SC/OC/verbas) que tenham **dados reais** da empresa.
4. **Chaves e senhas de teste:** apague arquivos `.env` de teste e confira que nenhuma pasta guarda senha do TOTVS. Não copie esses valores para lugar nenhum.
5. Os **dados de demonstração** (nomes e valores fictícios das apresentações) não são dados da empresa e podem ficar.
6. Se houve dados reais da empresa colados em **conversas com assistentes de IA** ou em e-mails pessoais, apague essas conversas e mensagens.

### 2.2 Conferência

**[TI]** Confirma que o app novo é o único em uso e que ninguém da equipe usa mais o endereço de testes.

### 2.3 Declaração

**[Rafael assina; TI confere]** Anexe ao Termo (cláusula 8.3). Modelo:

```
DECLARAÇÃO DE ENCERRAMENTO DO AMBIENTE DE TESTES

Eu, Rafael Luís de Souza, declaro à <razão social da empresa>, controladora dos dados, que:

1. O aplicativo "Central de Suprimentos" foi testado em servidor local, com dados de teste.
2. A versão entregue começa limpa: não houve migração nem cópia de dados para o ambiente da empresa.
3. Em __/__/____ apaguei o banco de testes local, os dados do app nos navegadores usados
   nos testes e os backups e exportações de teste do meu computador.
4. Não mantenho cópia de dados reais da empresa.

Local, data, assinatura.
```

Conferir com o Jurídico o texto exato e o prazo.

---

## Parte 3. Rotina de LGPD no ambiente novo

### 3.1 Retenção que o servidor já faz
- Chat: apaga sozinho após `CHAT_RETENCAO_MIN`.
- Arquivos da atualização do TOTVS: os antigos são apagados a cada execução.

### 3.2 O que falta definir
- **Auditoria** (`auditoria`) não tem limpeza automática. Se a empresa fixar um prazo (por exemplo, 5 anos **[confirmar]**), a TI agenda:
  ```sql
  delete from auditoria where quando < now() - interval '5 years';
  ```
- **Notificações** lidas: sugestão de apagar após 12 meses:
  ```sql
  delete from notificacoes where lida and criado_em < now() - interval '12 months';
  ```

### 3.3 Pedido de um titular (art. 18) ou desligamento de colaborador
Troque `:email` pelo e-mail da pessoa. **Rode primeiro os `select`** e só então os `update` ou `delete`.

```sql
-- o que há sobre a pessoa
select id, nome, email, telefone, ativo from perfis where lower(email) = lower(:email);
select count(*) from notificacoes where lower(destinatario_email) = lower(:email);
select count(*) from anotacoes where dono = (select auth_user_id from perfis where lower(email) = lower(:email));
select count(*) from auditoria where lower(quem_email) = lower(:email);

-- desligamento: tira o acesso e mantém o histórico
update perfis set ativo = false, permissoes = '[]'::jsonb where lower(email) = lower(:email);

-- eliminação dos dados pessoais da pessoa (mantém o registro, anonimizado)
update perfis set nome = 'Ex-colaborador', email = null, telefone = null, auth_user_id = null, auth_legado = null
 where lower(email) = lower(:email);
delete from notificacoes where lower(destinatario_email) = lower(:email);
delete from anotacoes where dono = :auth_user_id and not compartilhada;  -- :auth_user_id = perfis.auth_user_id, lido antes da anonimização
```

A **auditoria** pode ter obrigação de guarda (rastreabilidade de compras). Em vez de apagar, anonimize `quem_email` quando o prazo definido acabar, e só com a aprovação do Jurídico.

Documentos de `dados_compartilhados` que citam a pessoa pelo nome (Mesa, avaliações, calendários, Anotações compartilhadas) não têm coluna de e-mail. Para esses, procure pelo nome:
```sql
select tipo from dados_compartilhados where dados::text ilike '%' || :nome || '%';
```
e edite pela tela ou por SQL, com o Jurídico definindo o que anonimizar.

### 3.4 Incidente de segurança
O servidor registra os acessos (logs do gunicorn no Coolify) e a auditoria. Para o plano de resposta (art. 48), o encarregado define o prazo de comunicação à ANPD e aos titulares. A TI guarda os logs por pelo menos o prazo que o encarregado indicar **[confirmar]**.

---

## Checklist de fechamento

| # | Item | Quem | Pronto |
|---|---|---|---|
| 1 | Homologação do app novo | TI | |
| 2 | Ambiente de testes apagado (banco local, navegadores, arquivos) | Rafael | |
| 3 | Declaração assinada e anexada ao Termo | Rafael / Jurídico | |
| 4 | Registro das operações (art. 37) e aviso de privacidade | DPO / Jurídico | |
| 5 | Decisões: ranking, retenção da auditoria e IA | Gestão / DPO | |
