# Testing Plan

## Visão Geral

A estratégia de testes para o Record Label Manager será simples, prática e focada na funcionalidade essencial, considerando que o projeto está sendo desenvolvido por uma pessoa só, em ciclos longos.

---

## 1. Testes Automatizados no Backend (Django)

**Ferramenta:** Testes nativos do Django (`unittest`) ou `pytest-django`

**Cobertura mínima sugerida:**

- Autenticação (login, logout, criação de usuário)
- Criação e edição de:
  - Labels
  - Artists
  - Releases e Tracks
  - Mixtapes
  - Documents
  - Calendar Events
  - Demos
- Regras de negócio básicas:
  - Faixas com `is_streaming_single` devem ter `streaming_release_date`
  - Releases devem ter `catalog_number`
  - Verificação de permissões por usuário

**Execução:** via `python manage.py test`

---

## 2. Testes Manuais no Frontend

**Objetivo:** Validar a interface e experiência do usuário

**Verificações recomendadas:**

- Login/logout
- Navegação via sidebar entre os módulos
- Cadastro de artista e lançamento
- Upload/linkagem de arquivos
- Preenchimento e validação de campos obrigatórios

**Ferramentas de apoio:** navegador e console devtools

---

## 3. Testes de Integração

**Objetivo:** Validar se a comunicação entre o frontend e a API está funcionando

**Ferramentas:** Postman, Insomnia, ou diretamente no navegador

**Verificações básicas:**

- Endpoints de API retornando dados esperados
- Erros tratados corretamente (ex: autenticação, campos inválidos)
- JSON retornado está no formato esperado para o frontend

---

## Observações

- O foco é manter testes simples, funcionais e que ajudem a evitar regressões durante o desenvolvimento
- Automação de testes de interface (ex: com Cypress) pode ser considerada futuramente, após MVP
