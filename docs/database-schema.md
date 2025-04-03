# Database Schema

## Overview

A estrutura segue modelo relacional usando PostgreSQL, com suporte a múltiplas gravadoras por usuário, e dados organizados para automação, calendário e análise.

---

## User

- `id`: UUID
- `first_name`: string
- `last_name`: string
- `email`: string (único)
- `password`: hashed string
- `role`: enum (`owner`, `manager`, `assistant`)
- `created_at`: datetime

---

## Label

- `id`: UUID
- `name`: string
- `description`: text
- `country`: string
- `owner_id`: foreign key → User
- `created_at`: datetime

---

## Artist

- `id`: UUID
- `name`: string (nome real)
- `project`: string (nome artístico)
- `bio`: text
- `email`: string
- `country`: string
- `image_url`: string (ou arquivo)
- `created_at`: datetime

Relacionamentos:
- Many-to-many com Labels
- One-to-many com Tracks e Mixtapes

Tabela intermediária:
- `ArtistLabel`: liga Artistas a Labels (many-to-many)

---

## Release

- `id`: UUID
- `title`: string
- `description`: text
- `release_date`: date
- `status`: enum (`draft`, `scheduled`, `released`)
- `catalog_number`: string (ex: "TTR023")
- `style`: string (ex: “Techno”, “Ambient”)
- `tags`: array de strings (ex: `["#Chillout", "#Organic"]`)
- `soundcloud_url`: string (opcional)
- `bandcamp_url`: string (opcional)
- `other_links`: text ou JSON (opcional)
- `label_id`: foreign key → Label
- `created_at`: datetime

---

## Track

- `id`: UUID
- `title`: string
- `src_code`: string (ISRC)
- `audio_url`: string (link ou caminho local)
- `is_streaming_single`: boolean
- `streaming_release_date`: date (opcional)
- `tags`: array de strings (ex: `["#DeepHouse", "#DubTechno"]`)
- `release_id`: foreign key → Release
- `artist_id`: foreign key → Artist
- `label_id`: foreign key → Label
- `created_at`: datetime

---

## Mixtape

- `id`: UUID
- `title`: string
- `description`: text
- `audio_url`: string (link ou caminho local)
- `release_date`: date
- `artist_id`: foreign key → Artist
- `label_id`: foreign key → Label
- `created_at`: datetime

---

## Document

- `id`: UUID
- `title`: string
- `description`: text
- `file_url`: string
- `label_id`: foreign key → Label
- `uploaded_by`: foreign key → User
- `created_at`: datetime

---

## CalendarEvent

- `id`: UUID
- `title`: string
- `description`: text
- `date`: date
- `label_id`: foreign key → Label
- `release_id`: optional foreign key → Release
- `created_by`: foreign key → User
- `created_at`: datetime

---

## Demo (baseado em Track, com campos extra)

- `id`: UUID
- `title`: string
- `audio_url`: string
- `artist_name`: string (texto livre)
- `label_id`: foreign key → Label
- `submitted_by`: foreign key → User
- `status`: enum (`new`, `reviewed`, `accepted`, `rejected`)
- `submitted_at`: datetime

---
