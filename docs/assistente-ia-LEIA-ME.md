# IA do assistente — servidor

O assistente do app responde sozinho as perguntas sobre os dados (fornecedor mais barato, preço, SCs em aberto…).
Quando não entende, ou quando a pergunta começa com `ia:`, ele repassa a pergunta para uma IA (Claude ou ChatGPT) **pelo servidor**.

## Por que pelo servidor
- A chave da IA fica só no servidor (variável de ambiente). Se ficasse no navegador, qualquer pessoa poderia copiá-la.
- O servidor confere o login de quem pergunta e limita as perguntas por minuto.
- O resumo de números só é enviado se o administrador ligar essa opção. Ele não leva nomes, e-mails nem telefones.

## Como ligar
1. **TI:** registrar o `bp_ia` de `ia_endpoint.py` no Flask da Plataforma de Automações (rota `POST /api/ia`).
   Outra opção é um webhook no n8n que receba o mesmo JSON e devolva `{ "resposta": "..." }`.
2. **TI:** definir as variáveis de ambiente no Coolify (lista no topo do `ia_endpoint.py`).
   - Claude: `IA_PROVEDOR=anthropic` e `ANTHROPIC_API_KEY`.
   - ChatGPT: `IA_PROVEDOR=openai` e `OPENAI_API_KEY`.
3. **Admin do app:** em **Configurações › Assistente com IA**, informe o endereço (`/api/ia` se o app estiver no mesmo servidor), marque "Ligar" e clique em **Testar conexão**.
4. Se o endereço for de outro domínio, inclua-o em `connect-src` no arquivo `deploy/_headers`.

## Contrato
Pedido (`POST`, `Authorization: Bearer <token do login>`):
```json
{ "pergunta": "texto", "historico": [{ "papel": "usuario", "texto": "..." }], "contexto": { "comprado_no_mes": 123 } }
```
Resposta: `{ "resposta": "texto" }`.
Erros: `401` (sem login), `429` (limite), `500` (sem chave) e `502` (provedor fora).
