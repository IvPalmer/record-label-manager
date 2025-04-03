# Backend Documentation

## Framework and Language

- Framework: Django + Django REST Framework
- Language: Python
- Environment: Hospedado em VPS (Hostinger)
- Database: PostgreSQL

## API Design

- RESTful APIs organizadas por gravadora (label)
- Autenticação via JWT
- Endpoints para usuários, gravadoras, artistas, lançamentos, faixas, documentos, mixtapes, demos e calendário

## File Upload & Storage

- Arquivos originais pesados (ex: .wav) não são armazenados no servidor
- Usuário pode:
  - Linkar arquivos via serviços como Google Drive, Dropbox
  - Subir arquivos temporários convertidos em versões leves (.mp3)
- Campos armazenados: links, metadados, paths de versões leves (opcional)

## Auth & Permissions

- Registro/login via e-mail e senha
- Login social via Google OAuth2
- Usuários possuem papéis (owner, manager, assistant)
- Permissões baseadas na gravadora

## Admin Panel

- Admin do Django ativado para gestão total dos dados
- Útil para uso interno e testes

## Integrações futuras

- Bandcamp API (dados de venda)
- Serviços de email, distribuição e analytics
