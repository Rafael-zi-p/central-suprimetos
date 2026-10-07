# 01 — Regras de negócio

Os cálculos do app explicados em português, com o nome da função de origem entre parênteses, para quem for portar o código. Os números citados como padrão podem ser mudados pelo administrador em **Configurações › Parâmetros do sistema** (`pzParam`).

Convenções:
- datas em `aaaa-mm-dd`, no fuso local (`pzHojeISO`);
- "dias" são dias corridos;
- coligada = obra (cada obra é uma coligada do TOTVS).

---

## 1. Ciclo mensal do CUBO (`janelaDoMes`)

Cada mês tem quatro datas:

| Data | Padrão | Significado |
|---|---|---|
| `lim` | dia 9 | último dia para a obra **criar** a SC do mês |
| `ini`–`fim` | dias 10 a 13 | janela de **aprovação** das SCs |
| `reu` | dia 15 | reunião do CUBO (quem compra o quê) |

O administrador pode ajustar as datas de um mês específico (doc `param_janela_aprov`). Um dia maior que o último dia do mês vira o último dia.

## 2. Data de aprovação da SC (`scAprovacao`)

O prazo de **Suprimentos** (comprador) conta **da aprovação** da SC. O prazo da **obra** conta da **criação** (seção 5). A data de aprovação é a primeira disponível nesta ordem:

1. a coluna `DATA_APROVACAO_SC` da consulta de SC (fonte "TOTVS");
2. a data de aprovação que a consulta de OC traz para aquela SC (fonte "OC");
3. a estimativa pelo ciclo: SC criada até o `lim` do mês recebe o `fim` da janela daquele mês (fonte "janela");
4. a própria data de criação (fonte "criação").

A tela sempre informa qual fonte foi usada.

## 3. Categoria e prazos do SLA (`slaResolver`, `SLA_DATA`)

- Cada categoria da DQ.SUP.02 tem três prazos: **suprimentos** (`sup`, da aprovação até a OC), **entrega** (`ent`) e **total** (`total`). A tabela é editável em Configurações › Prazos SLA (doc `param_sla`). O padrão de fábrica é `SLA_PADRAO`.
- O produto da SC é ligado a uma categoria nesta ordem:
  1. regra por produto definida na Reunião do CUBO (`CUBO_REGRAS.slaProd`);
  2. regra por subgrupo ou grupo do insumo;
  3. aproximação por palavra-chave, marcada como "aproximado".

## 4. Prazo dos compradores (`calcSLAStatus`)

- **OC já emitida:** `dias = data da OC − início`, em que início é a aprovação, ou a criação na falta dela. Dentro do prazo quando `dias ≤ sup`.
- **Ainda sem OC:** mede até hoje. É "crítico" quando o atraso passa de 50% do prazo.

## 5. Prazo pedido pela obra (`slaObraPrazo`)

A obra precisa **criar a SC** com pelo menos o **prazo total** da categoria até a **data de necessidade**:

| Situação | Condição |
|---|---|
| **erro** (necessidade impossível) | data de necessidade no dia da criação da SC ou antes |
| **fora** (criada fora do SLA) | `necessidade − criação < total`; o app mostra quantos dias faltaram. É erro da obra |
| **ok** | demais casos |

O **prazo de entrega** do fornecedor **não é medido**: ele é combinado entre a obra e o fornecedor. O app não mostra "entrega atrasada" nem cobra atraso de entrega (decisão do usuário-chave, 06/10/2026).

## 5.1 Aprovação e cancelamento da OC no RM

O RM abre um "atendimento" de aprovação (tipo 12) para cada OC. O app lê o atendimento mais recente:

| Código | No app | O que significa |
|---|---|---|
| **F** | APROVADA | passou pelo processo de aprovação; libera PDF e envio ao fornecedor |
| **A** | PENDENTE | aguardando o aprovador |
| **C** (OC ativa) | REJEITADA | o aprovador rejeitou; o comprador abre, corrige e reenvia, e o RM abre um novo atendimento (volta a PENDENTE) |
| OC **cancelada** | CANCELADA | a OC fica inválida e o saldo volta para a SC, para fazer uma nova OC |

OC rejeitada avisa quem a criou e o responsável da SC, e o cartão da Mesa fica em "Comprando / OC". Confirmado com o usuário-chave em 07/10/2026 (consultas `totvs-sql/DIAG.APROV.OC*.sql`).

**Cuidado:** o número da OC (`NUMEROMOV`) se repete entre tipos de movimento. O app separa e marca "nº repetido" quando isso acontece na mesma obra.

## 6. SC "consumida" (`scConsumido`)

A SC sai dos contadores de "em aberto" e "pendentes" quando:
- o item foi marcado como comprado à mão; ou
- alguma OC do TOTVS aponta para ela, pelo campo SC de origem; ou
- o status dela é `RECEBIDO`.

## 7. Regularização (Configurações › CUBO › Regras)

- O movimento **1.1.06** (AT) conta como "Regularização (AT)".
- Palavras como *regulariz* no texto da SC ou na observação da OC contam como regularização "fora do AT".

As duas listas são editáveis (`CUBO_REGRAS.regMovimentos` e `regPalavras`).

## 8. Ordens de compra

- **Tipos de movimento:** SC = 1.1.01 a 1.1.06. OC = apenas os tipos em que a SC é recebida (lista em Configurações › Tipos de movimento).
- **Número repetido:** o mesmo nº de OC pode existir em tipos de movimento diferentes da mesma coligada. O app os diferencia como "161 (1.1.12)" (`ocxDesambiguar`).
- **Cancelamento:** OC cancelada não conta em valores, prazos, economia nem Cronograma.
- **Data de entrega da OC:** não é usada. É só um requisito do TOTVS para criar a OC (o comprador preenche uma data posterior à da OC). Não aparece no PDF, no e-mail, no detalhe da OC nem nos relatórios, e não entra em nenhum cálculo de prazo. A data que vale é a **necessidade da SC**, definida pela obra.

## 9. Saldo da verba (`vbSaldoLinha`, `vbKPIs`)

A consulta de verbas (CUBO7.12) traz campos brutos. Os indicadores são calculados assim:

| Indicador | Fórmula |
|---|---|
| Medido | `CONTRATO_VALOR_MEDIDO + CONTRATOTOTALMEDIDOEXTRA` |
| Contratado | `CONTRATO_PEDIDO_EXTRA_VALOR + CONTRATO_TOTAL_CONTRATADO + CONTRATO_CONTRATADO_VIA_OC_VALOR` |
| Realizado | `REALIZADO_EXTRA_VALOR + REALIZADO_APROP + REALIZADO_VALOR` |
| Saldo de contrato | Contratado − Medido |
| Saldo de OC | `PEDIDO_EXTRA_VALOR + PEDIDO_VALOR` |
| Comprometido | Saldo de OC + Saldo de contrato |
| **Saldo** | **Orçado − Realizado − Comprometido** |

- O mesmo vale em quantidade.
- Se a base já traz uma coluna "Saldo", ela é usada direto.
- O Quadro de Cotação compara a compra com o **saldo**, não com o orçado.
- **Validar com a Controladoria antes de uso amplo.**

## 10. Referência de preço e alerta de preço (`ocxPrecoRef`, `ocxPrecoAlto`)

- **Chave do item:** código do insumo (ou nome normalizado) + unidade.
- **Referência:** compras **anteriores** do mesmo item, de outras OCs, não canceladas:
  - média ponderada pela quantidade;
  - último preço, com a data e o fornecedor dele.
- **Alerta:** preço acima da média em mais de `alertaPrecoPct`, padrão **15%**, com pelo menos **2** compras anteriores, olhando as OCs dos últimos 30 dias.

## 11. Alerta de verba

- Linha de verba com uso acima de `alertaVerbaLinhaPct`, padrão **90%**: "perto do limite".
- Acima de 100%: "estourada".
- O alerta é dado só na linha mais detalhada, para não repetir pai e filho.

## 12. Relatório de economia (`ecoLinhas`, `ecoCotacoes`)

- **Compras:** `(referência − preço pago) × quantidade`. A referência é o último preço ou a média, à escolha do usuário. Período padrão: últimos 3 meses. Respeita os filtros da aba OC.
- **Cotações:** maior proposta − valor fechado, por quadro de cotação concluído.

## 13. Comprador do mês (`gmCalc`, `GM_REGRAS`)

Pontos por mês e por pessoa:

| Evento | Pontos |
|---|---|
| item de SC que virou OC | +10 |
| OC dentro do prazo do SLA | +5 |
| OC fora do prazo do SLA | −3 |
| item prioritário ou urgente atendido | +4 |
| cotação concluída | +8 |
| cotação concluída com 3 ou mais fornecedores | +4 a mais |
| regularização concluída | +5 |
| pendência fora do SLA no mês corrente | −1 (no máximo 40) |

- A pessoa é quem emitiu a OC no TOTVS. Na falta, vale o responsável do item.
- **Mês fechado:** vale a "foto" gravada pelo administrador (doc `gm_fech_<aaaa-mm>`), igual para todos e estável mesmo quando o mês sai do período de busca.

## 14. Cronograma de Compras e Contratações — curva A (`croCalc`)

> **Módulo em desenvolvimento.** O orçamento e a data planejada ainda são manuais (ver pendências).

### Entradas do item

- obra e descrição;
- categoria SLA da atividade;
- início do serviço (planejado e, se mudou, o da obra);
- orçado: quantidade, unitário e, opcionalmente, um total diferente de quantidade × unitário;
- números de SC e de OC/contrato;
- valores digitados à mão, que **sempre têm prioridade** sobre os automáticos.

### Preenchimento automático (`croAuto`)

- **Das SCs informadas:**
  - data da SC = a menor data de criação;
  - aprovação real = a menor aprovação vinda do TOTVS ou da OC.
- **Das OCs**, as informadas no item ou, na falta, as que saíram das SCs do item (canceladas não contam):
  - fechamento = a menor data de OC;
  - contratado = soma dos valores;
  - quantidade = soma dos itens na mesma unidade;
  - comprador = quem emitiu a OC.

### Prazos da categoria (`croPrazos`)

- `sup`, `ent` e `total` vêm do SLA.
- O tempo de contratação é `ctr = total − sup − ent`.

### Cálculos

| Campo | Fórmula |
|---|---|
| Data de solicitação | início − (sup + ctr + ent) |
| **Data máxima para a obra pedir** (`croDataMaxima`) | o `lim` do ciclo no mês da data de solicitação, se ela cair depois dele; senão, o `lim` do mês anterior |
| Início de suprimentos (`croStartSup`) | aprovação real; sem ela, o `fim` da janela do mês da SC (ou do mês seguinte, se a SC saiu depois do `lim`) |
| Limite de fechamento | início − (ent + ctr) |
| Dias para fechar | (início de suprimentos + sup + ctr) − hoje |
| SLA real de suprimentos | (fechamento − início de suprimentos) − sup − ctr; positivo = fechou depois do prazo |
| Saving | orçado total − contratado, só para item concluído |
| Variação de quantidade | (qtd contratada − qtd orçada) × unitário orçado |
| Variação de preço | (unitário orçado − unitário contratado) × qtd contratada |

### Situações

- **Obra:** atrasada mais de 30 dias · atrasada até 30 dias · pedir em até 15 dias · em até 30 dias · mais de 30 dias · ok (já pediu ou já fechou).
- **Suprimentos:** concluído · atrasado (dias para fechar < 0) · com SC · sem SC.
- **Concluído sem data:** quando a planilha trazia texto no fechamento (por exemplo "xx", ou uma data digitada errada), o item conta como concluído e a tela pede a data correta.

### Importação da planilha antiga

- Uso único, para migrar o histórico.
- Lê a aba "Cronograma" pelos nomes das colunas, a unidade da aba "Curva 25" e o orçamento por obra da 1ª tabela da aba "Aux.".
- Nome de obra não reconhecido abre uma janela para ligar à obra certa. A ligação fica guardada em `CRONO.apelidos`.
- **Importar de novo substitui todos os itens**, depois de uma confirmação.

### Alertas

- obra atrasada para pedir;
- contratação atrasada;
- obra precisa pedir em até 15 dias.

## 15. Contratações de mão de obra e serviços (aba Pré-Compras · `ctEditor`)

Substitui o fluxo por e-mail e o ZEEV. A obra abre o pedido; Orçamento, Engenharia e Jurídico conduzem até o contrato assinado e a OC.

| # | Etapa | Quem age | Para avançar |
|---|---|---|---|
| 1 | Abertura | quem abre (obra) | objeto, obra, tipo, novo ou aditivo, data de início, etapa orçamentária (quando a obra tem verbas) e **carta convite** anexada |
| 2 | Aprovação do GGO (sempre) | papel **GGO** | **planilha consolidada** anexada; ou devolve para a obra |
| 3 | Triagem do Orçamento | papel **Gerente de Orçamento** | aprova; ou devolve para a obra. **O SLA começa aqui** |
| 4 | Negociação | papel **Equipe de Orçamento** | **mapa de aprovação = quadro de contrato concluído no Quadro de Cotação** (botão "Montar o mapa no Quadro de Cotação"); avisa o GGO e a obra |
| 5 | SC, contrato e OC (em paralelo) | obra (SC), Engenharia, Jurídico e Assinatura (contrato), Equipe de Orçamento (OC) | SC informada, contrato assinado e OC informada |
| 6 | Contratada | — | automático quando os três itens da etapa 5 estão feitos |

- **Contrato:** solicitação (obra ou Orçamento) › Engenharia › Jurídico (anexa a **minuta**) › Assinatura (anexa o **contrato assinado**). Engenharia e Jurídico podem devolver; o contrato volta para a solicitação.
- **Etapa orçamentária e saldo:** vêm da aba Verbas da obra. O saldo do momento do envio fica guardado no pedido; o app avisa quando o valor passa do saldo.
- **Mobilização:** aviso quando faltam menos de 20 dias para a data de início.
- **SLA:** dias corridos da entrada na triagem até a contratação concluída, comparados com o prazo do tipo de contratação. Faixas: em dia; a partir de 80% do prazo, atenção; acima do prazo, fora. Uma devolução para a obra zera a contagem, que recomeça na nova entrada na triagem.
- **Mapa de aprovação:** o botão da Negociação abre o Quadro de Cotação no modo Contrato, com obra, objeto, etapa orçamentária e saldo da verba. Ao concluir o quadro, o vencedor, o valor, o CNPJ e o código do quadro voltam para a contratação, e o resumo da cotação aparece no pedido.
- **OC:** se a SC informada já tem OC na base, a OC é ligada sozinha.
- **Configuração (administrador):** pessoas de cada papel e tipos de contratação com o prazo, em Configurações › Pré-Compras e Contratações. O administrador pode agir em qualquer etapa.
- **Avisos:** cada passagem avisa quem age na etapa seguinte e quem abriu o pedido.
- **Dados:** `pre_<id>` (tipo `contratacao`, campos em `ct`) e anexos em `preanx_<id>`.

## 16. Gravação compartilhada sem perda (`pzMesclar`)

Antes de gravar um documento compartilhado, o app lê a versão do servidor e mescla em três vias: **base** (o que o usuário leu), **local** (o que ele mudou) e **servidor** (o que outros gravaram nesse meio-tempo).

- Mudou só de um lado: vale esse lado.
- Mudou nos dois lados: a mescla desce chave a chave.
- Listas de itens com `id` são mescladas item a item, respeitando exclusões.
- Listas simples (por exemplo, históricos): ficam as entradas do servidor, sem as que saíram daqui, mais as que entraram aqui.
- Valor simples alterado nos dois lados: vence o local.
