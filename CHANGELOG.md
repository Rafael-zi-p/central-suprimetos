# Histórico de versões

## v3: servidor da empresa (07/10/2026)

**Infraestrutura**
- **Servidor Flask** no padrão da Plataforma de Automações:
  - login Microsoft Entra (`identity.flask`), sessão no Redis;
  - PostgreSQL com schema `suprimentos`;
  - Dockerfile para o Coolify.
- **Sem serviço externo**: a tela fala só com o próprio servidor.
- **Permissões conferidas no servidor**, com as mesmas regras do banco anterior, e auditoria gravada pelo servidor.
- **TOTVS pelo usuário de serviço**: ninguém digita senha do RM. Atualização automática no servidor, com agenda definida pelo administrador (rápida de SC e OC de 15 em 15 minutos, diária e completa semanal), com data "desde" única, definida pelo administrador.
- **Restrição por obra no servidor**: quem tem obras limitadas no perfil só recebe essas obras (proxy do RM, arquivos da atualização e `sc_itens`).
- **LGPD**: inventário de dados pessoais, retenção, pedido de titular e encerramento do ambiente de testes, com modelo de declaração (`docs/02-LGPD.md`).
- **Chat** pelo próprio servidor: mensagem privada só chega a quem deve.

**Regras de negócio e correções desde a v2.0**
- **SLA da obra:** conta da criação da SC até a data de necessidade. O prazo de entrega não é medido.
- **Aprovação da OC:** F = aprovada, A = pendente, C com OC ativa = rejeitada; aviso para quem criou e atalhos na aba OC.
- **Contratações (Pré-Compras):** fluxo da abertura pela obra até contrato assinado e OC, sem ZEEV: aprovação do GGO, triagem do Orçamento (início do SLA), negociação com mapa de aprovação, contrato (Engenharia, Jurídico e assinatura) e SC/OC em paralelo; papéis e prazos por tipo configuráveis; anexos por etapa. O mapa de aprovação é o quadro de contrato do Quadro de Cotação (vencedor e valor voltam sozinhos).
- **Atualização do TOTVS de 15 em 15 minutos:** agenda definida pelo administrador (rápida de SC e OC, diária com Verbas e Insumos, completa semanal), uma única tarefa agendada no servidor, e a tela recebe os dados novos sozinha, sem interromper quem está editando.
- **Data de entrega da OC fora do app:** é só trava do TOTVS; sai do PDF, do e-mail, do detalhe da OC, do Excel e do assistente. A necessidade da SC (obra) continua valendo.
- **Quadro de Cotação:** ao digitar a descrição do item, sugere insumos da Base de Insumos e preenche a unidade.
- **Pré-Compras:**
  - tickets e pacotes com quem criou e para quem foi direcionado;
  - categorias definidas pelo administrador;
  - ligação com cotação, SC e OC.
- **Ordens de Compra:**
  - PDF para o fornecedor com o tipo de cada item (produto ou serviço);
  - observação do TOTVS só sai no PDF e no assunto do e-mail se o comprador marcar (padrão: não sai), e pode ser copiada para editar;
  - marcações pela observação (regularização, caixinha, permuta);
  - aviso de número repetido em outro movimento.
- **Visão Geral:**
  - volumetria por comprador;
  - quadro de prazo obra × comprador;
  - gráficos repetidos removidos.
- **Análise completa do código:** cerca de 70 correções de cálculo, segurança e desempenho (detalhes no histórico do projeto).

## v2.0: referência (04/10/2026)

Versão entregue como referência funcional, para testes.
