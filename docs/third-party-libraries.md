# Third-Party Libraries & APIs

## Frontend (React.js)

- **react-router-dom** – Navegação entre páginas
- **zustand** – Gerenciamento de estado global
- **axios** – Comunicação com API REST
- **classnames** – Manipulação condicional de classes CSS
- **react-hook-form** (ou controle manual) – Gerenciamento de formulários

## Backend (Django + DRF)

- **djangorestframework** – Criação de APIs REST
- **djangorestframework-simplejwt** – Autenticação via JWT
- **django-cors-headers** – Controle de CORS entre frontend e backend
- **python-dotenv** – Gerenciamento de variáveis de ambiente
- **ffmpeg-python** – Conversão de áudio para streaming
- **requests** – Requisições externas para APIs como Google Drive ou Bandcamp

## Integrações de Login e Importação

- **Google OAuth2** – Login social
- **Google Drive API** – Importação automatizada de lançamentos a partir de pastas organizadas

## Integrações de Streaming e Análise

- **SoundCloud API** – Acesso a faixas, playlists e usuários do SoundCloud
- **Spotify Web API** – Acesso a dados de faixas, álbuns e artistas (restrito a certas informações)
- **SymphonicMS** (opcional) – Plataforma de análise que consolida dados de streaming de Spotify, Apple Music, Amazon Music, Deezer, TikTok, YouTube etc. via dashboards e painéis
- **SoundCharts** (opcional) – Ferramenta de analytics que agrega dados de mídia social e plataformas de streaming

## Observações

- As integrações com Spotify e SoundCloud exigem autenticação via OAuth2
- Mudanças nas políticas do Spotify podem limitar o acesso direto a certos dados (ex: artistas relacionados, playlists oficiais)
- Alternativas como SymphonicMS e SoundCharts oferecem consolidação de dados para análise sem depender apenas da API do Spotify
