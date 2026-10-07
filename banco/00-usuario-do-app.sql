-- ════════════════════════════════════════════════════════════════════
--  Usuário do banco para o app (rodar como administrador do PostgreSQL,
--  ANTES do 01-estrutura.sql). Troque a senha. O app só enxerga o schema
--  "suprimentos": não lê nem grava nada da Plataforma de Automações.
-- ════════════════════════════════════════════════════════════════════
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'suprimentos_app') then
    create role suprimentos_app login password 'TROQUE-ESTA-SENHA';
  end if;
end $$;

create schema if not exists suprimentos authorization suprimentos_app;
grant usage on schema suprimentos to suprimentos_app;
alter default privileges in schema suprimentos grant select, insert, update, delete on tables to suprimentos_app;
alter default privileges in schema suprimentos grant usage, select on sequences to suprimentos_app;

-- depois do 01-estrutura.sql (garante as permissões nas tabelas já criadas):
-- grant select, insert, update, delete on all tables in schema suprimentos to suprimentos_app;
-- grant usage, select on all sequences in schema suprimentos to suprimentos_app;
-- revoke update, delete on suprimentos.auditoria from suprimentos_app;   -- auditoria só cresce
