# CENTRAL SUPRIMENTOS

Sistema interno de gestão e automação do Departamento de Suprimentos do Grupo Impper.

## Sobre o projeto

O CENTRAL SUPRIMENTOS foi desenvolvido para centralizar e automatizar processos do Departamento de Suprimentos, integrando informações de obras, Solicitações de Compra (SC), cotações, fornecedores, acompanhamento e dados do TOTVS RM.

## Principais recursos

- Gestão de Solicitações de Compra (SC)
- Acompanhamento de atendimento
- Integração com TOTVS RM
- Atualização automática dos dados
- Cotações e fornecedores
- Kanban de acompanhamento
- Chat interno
- Gestão de usuários e permissões
- Área administrativa
- Backup automático
- Atualização automática no servidor
- Verificação em duas etapas

## Arquitetura

O sistema utiliza:

- Front-end web
- Supabase
- PostgreSQL
- Supabase Edge Functions
- Supabase Storage
- pg_cron
- pg_net
- Integração com TOTVS RM

## Configuração

Para utilizar o sistema em uma nova instalação, é necessário configurar:

1. Projeto próprio no Supabase
2. Banco de dados e estruturas SQL
3. Edge Functions
4. Secrets de integração
5. Integração com TOTVS RM
6. Domínio da aplicação
7. Variáveis de configuração do projeto

## Implantação

O projeto pode ser hospedado em plataformas compatíveis com aplicações web.

O domínio utilizado pela aplicação pode ser configurado posteriormente pela empresa responsável pela implantação.

## Segurança

Este repositório deve permanecer privado.

Nunca publique:

- Senhas
- Tokens
- Chaves privadas
- Service Role Keys
- Credenciais do TOTVS
- Secrets das Edge Functions

## Grupo Impper

Projeto desenvolvido para utilização do Grupo Impper.

---

**Versão:** 1.0  
**Projeto:** CENTRAL SUPRIMENTOS
