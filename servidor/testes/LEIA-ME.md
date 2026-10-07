# Testes do servidor

Testes usados antes da entrega. Eles rodam contra um **PostgreSQL de teste**, e não o de produção.

| Arquivo | O que faz |
|---|---|
| `rodar_local.py` | Sobe o servidor de verdade na porta 8143. Simula só o login Microsoft (`?como=email` escolhe o usuário), o Redis (em memória) e um RM falso na porta 8150. |
| `testar_agenda.py` | 17 testes da agenda da atualização automática (horário, dias, intervalo, diária e completa). Não precisa de banco. |
| `testar_api.py` | 71 testes de rotas e permissões: login, perfis, documentos, notificações, anotações, auditoria, restrição por obra, chat, TOTVS e atualização automática. **Apaga as tabelas do schema `suprimentos` do banco de teste.** |

Resultado em 07/10/2026, com PostgreSQL 18 local:
- `testar_api.py`: 71 de 71;
- religação das anotações no primeiro login: OK.

O login Microsoft de verdade só pode ser testado na homologação da TI, com o registro do app no Entra.
