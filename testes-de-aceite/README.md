# Testes de aceite

Casos com **entrada e resultado esperado** para as principais regras de negócio. Servem para provar que a versão reescrita calcula **igual** ao app de referência.

| Arquivo | Conteúdo |
|---|---|
| `casos.json` | os casos (id, regra, função de origem, entrada, esperado) e a conferência com dados reais do Cronograma |
| `rodar-no-app.js` | executa os casos **no app de referência**, pelo console do navegador, e imprime OK/FALHOU |

## Situação

Em 04/10/2026, rodando no `app-referencia/` desta entrega: **13 de 13 casos OK**.

## Como usar

**No app de referência** (confirma a referência):
1. Abra o app publicado e entre.
2. F12 › Console. Se o `casos.json` não estiver publicado junto do site, defina antes `window.CASOS_ACEITE = <conteúdo do casos.json>`.
3. Cole o conteúdo de `rodar-no-app.js` e tecle Enter. O script não grava nada no banco e restaura os parâmetros que mexe.

**Na versão nova:** transforme cada caso em um teste automatizado no framework de testes da empresa. Mesma entrada, mesmo esperado; números com tolerância de 0,005.

## Cobertura atual

| Regra (docs/01) | Casos |
|---|---|
| §1 ciclo do mês | CIC-01 |
| §2 aprovação estimada | APR-01, APR-02 |
| §4 prazo do comprador | SLA-01, SLA-02 |
| §9 saldo da verba | VB-01, VB-02 |
| §10 referência e alerta de preço | PRC-01 |
| §14 Cronograma | CRO-01, CRO-02, CRO-03 |
| §16 mescla em três vias | MES-01, MES-02 |
| Cronograma com dados reais | conferência: 275 itens, 230 concluídos e saving das 9 obras |

**Ainda sem caso (a acrescentar na reescrita):**
- §3 categoria do SLA por produto;
- §5 prazo pedido pela obra;
- §6–7 SC consumida e regularização;
- §11 alerta de verba;
- §12 economia;
- §13 ranking do comprador.

Para esses, use o app de referência como oráculo: mesma base, comparar a tela.
