# API Documentation

## Overview

A API segue o padrão RESTful e organiza os recursos por gravadora (label) para garantir separação e controle de dados. Os endpoints têm a seguinte estrutura base:

`/api/labels/:label_id/[resource]/`

Todos os endpoints exigem autenticação JWT e verificam se o usuário tem permissão sobre a gravadora acessada.

---

## Autenticação

- `POST /api/auth/register/` – Cria novo usuário
- `POST /api/auth/login/` – Login com e-mail e senha
- `POST /api/auth/google/` – Login via Google OAuth2
- `GET /api/auth/me/` – Dados do usuário autenticado

---

## Labels

- `GET /api/labels/` – Lista todas as labels do usuário
- `POST /api/labels/` – Cria uma nova label
- `GET /api/labels/:label_id/` – Detalhes de uma label
- `PUT /api/labels/:label_id/` – Edita uma label
- `DELETE /api/labels/:label_id/` – Deleta uma label

---

## Artists

- `GET /api/labels/:label_id/artists/` – Lista artistas
- `POST /api/labels/:label_id/artists/` – Cadastra artista
- `GET /api/labels/:label_id/artists/:artist_id/` – Detalhes do artista
- `PUT /api/labels/:label_id/artists/:artist_id/` – Atualiza artista
- `DELETE /api/labels/:label_id/artists/:artist_id/` – Remove artista

---

## Releases

- `GET /api/labels/:label_id/releases/` – Lista lançamentos
- `POST /api/labels/:label_id/releases/` – Cadastra lançamento
- `GET /api/labels/:label_id/releases/:release_id/` – Detalhes do lançamento
- `PUT /api/labels/:label_id/releases/:release_id/` – Atualiza lançamento
- `DELETE /api/labels/:label_id/releases/:release_id/` – Remove lançamento

---

## Tracks

- `GET /api/labels/:label_id/releases/:release_id/tracks/` – Lista faixas do lançamento
- `POST /api/labels/:label_id/releases/:release_id/tracks/` – Cadastra faixa
- `GET /api/labels/:label_id/tracks/:track_id/` – Detalhes da faixa
- `PUT /api/labels/:label_id/tracks/:track_id/` – Atualiza faixa
- `DELETE /api/labels/:label_id/tracks/:track_id/` – Remove faixa

---

## Mixtapes

- `GET /api/labels/:label_id/mixtapes/`
- `POST /api/labels/:label_id/mixtapes/`
- `GET /api/labels/:label_id/mixtapes/:mixtape_id/`
- `PUT /api/labels/:label_id/mixtapes/:mixtape_id/`
- `DELETE /api/labels/:label_id/mixtapes/:mixtape_id/`

---

## Documents

- `GET /api/labels/:label_id/documents/`
- `POST /api/labels/:label_id/documents/`
- `GET /api/labels/:label_id/documents/:document_id/`
- `DELETE /api/labels/:label_id/documents/:document_id/`

---

## Calendar Events

- `GET /api/labels/:label_id/calendar/`
- `POST /api/labels/:label_id/calendar/`
- `GET /api/labels/:label_id/calendar/:event_id/`
- `PUT /api/labels/:label_id/calendar/:event_id/`
- `DELETE /api/labels/:label_id/calendar/:event_id/`

---

## Demos

- `GET /api/labels/:label_id/demos/`
- `POST /api/labels/:label_id/demos/`
- `GET /api/labels/:label_id/demos/:demo_id/`
- `PUT /api/labels/:label_id/demos/:demo_id/`
- `DELETE /api/labels/:label_id/demos/:demo_id/`

---

## Observações

- Todos os endpoints podem retornar erros com status HTTP convencionais (400, 401, 403, 404, 500)
- Validações e autenticação são feitas no backend
