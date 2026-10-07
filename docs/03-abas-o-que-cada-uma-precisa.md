# Abas: de onde vêm os dados, o que configurar e como conferir

Use depois da instalação (`ENTREGA-COMPLETA.md` §4) e da primeira atualização completa do TOTVS. Cada linha diz o que a aba precisa para funcionar e o que olhar para saber que está certa.

**Duas formas de o app buscar no RM, ambas pelo usuário de serviço:**
- **Atualização automática** (agendada no servidor): SC e OC de 15 em 15 minutos (padrão), Verbas e Insumos uma vez por dia. A agenda fica em Configurações › Integração TOTVS.
- **Na hora, quando a aba abre**: Fornecedores, PDF da OC, Curva ABC, Obras e projetos, Orçado × Comprado e Compras sem etapa.

Os códigos das consultas já vêm preenchidos. Para conferir ou testar, use **Configurações › Consultas TOTVS** (botão **Testar e listar colunas**).

| Aba | Dados (consulta do RM) | Configurar antes | Como conferir |
|---|---|---|---|
| **Visão Geral** | `CUBO.SUP.SC`, `CUBO.SUP.OC`, `CUBO.SUP.VERBAS` | nada | Indicadores do mês, "Meu dia", volumetria e quadro de prazo obra × comprador com números |
| **Solicitações de Compras** | `CUBO.SUP.SC` | data **Buscar desde** (botão Atualizar) | 3 SCs conferidas com o RM: número, obra, itens e data de aprovação |
| **Mesa de Compras** | SC + OC; carteiras da Reunião do CUBO | carteiras de insumos dos compradores (Reunião do CUBO) | SCs novas em "Novas · sem responsável"; ao surgir a OC, o cartão anda sozinho |
| **Quadro de Cotação** | OC (histórico de preço e fornecedores sugeridos), Verbas (saldo), Base de Insumos (busca do item) | nada | Digitar um insumo mostra sugestões; "Fornecedores sugeridos" lista quem já vendeu; saldo da verba aparece no rodapé |
| **Ordens de Compra** | `CUBO.SUP.OC`; PDF pela `CUBO.SUP.OCDOC` | **Obras** (endereço, contatos, e-mail da NF-e); **Configurações › E-mail de envio da OC** | 3 OCs conferidas com o RM (aprovação, recebimento); gerar o PDF de uma OC aprovada |
| **Regularizações** | SC (movimento de AT e "REGULARIZAÇÃO" na observação) | **Configurações › Regularizações** (quem regulariza); **Tipos de movimento** | O quadro "Regularizações no TOTVS" conta as SCs; um pedido de teste com anexo |
| **Pré-Compras** | Base de Insumos, OC (preço de referência), SC (vínculo), Verbas (contratação) | **Configurações › Pré-Compras e Contratações**: categorias, **pessoas de cada papel** (GGO, Gerente e Equipe de Orçamento, Engenharia, Jurídico, Assinatura) e **tipos de contratação com prazo** | Uma contratação de teste passando por todas as etapas (`docs/01` §15) |
| **Anotações** | nenhuma (banco do app) | nada | Criar uma nota compartilhada e ver em outro usuário |
| **Obras** | cadastro na tela | GGO, GO, assistente, almoxarife, endereço, horário de recebimento, e-mail da NF-e e regras de segurança de cada obra | O PDF e o e-mail da OC saem com esses dados |
| **Base de Insumos** | `CUBO.SUP.INS` | nada | Total de insumos, grupos e "sem natureza orçamentária" |
| **Verbas** | `CUBO.SUP.VERBAS` (por obra e projeto) | projetos de cada obra em **Configurações › Coligadas** (sem cadastro, usa a lista padrão de projetos) | Coligada 35, projeto 4: orçado **R$ 85.125.853,18** (conferido em 07/10/2026) |
| **Prazos SLA** | SC + OC | **Configurações › Prazos SLA** (prazo por categoria) e janela de aprovação | Indicadores da obra e dos compradores; "SCs com erro" |
| **Fornecedores** | `CUBO.SUP.FORN` | nada | Busca por CNPJ; ranking depois das avaliações da obra |
| **Curva 25** | `CUBO.SUP.CRONO`, `CUBO.SUP.PROJ`, `CUBO.SUP.ORCCOMP`, `CUBO.SUP.SETAPA` | nada (obras e projetos vêm da PROJ) | Orçado × Comprado da coligada 35, projeto 4: total orçado igual ao das Verbas; "Sem etapa" ≈ R$ 1.887,48 |
| **Reunião do CUBO** | SC | regras por insumo e carteiras dos compradores | Itens novos sugeridos para cada comprador |
| **Configurações** | — | **Usuários & Permissões** (abas e obras de cada pessoa) e os itens acima | Pessoa sem a aba não a vê; pessoa com obra restrita só vê a obra dela |

## Fora das abas

- **Chat da equipe**: funciona pelo próprio servidor, sem configurar nada. Mensagens somem depois de `CHAT_RETENCAO_MIN`.
- **Assistente com IA**: vem **desligado** (`ENTREGA-COMPLETA.md` §9).
- **Alertas e notificações**: o sino do topo; a pessoa recebe os avisos das etapas em que age.

## Ordem sugerida para a primeira configuração

1. **Usuários & Permissões**: equipe, administradores, abas e obras.
2. **Obras**: os dados de cada obra.
3. **Botão Atualizar**: "Buscar desde" e **Rodar agora · completa**.
4. **Prazos SLA**, **Regularizações** e **Tipos de movimento**.
5. **Pré-Compras e Contratações**: papéis e prazos por tipo.
6. **Reunião do CUBO**: carteiras dos compradores.
7. Conferir cada aba pela coluna "Como conferir" acima.
