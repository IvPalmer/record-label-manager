# DevOps & Deployment

## Arquitetura Inicial

A aplicação será estruturada de forma modular, permitindo facilidade de migração entre ambientes de hospedagem no futuro.

### VPS (HostWare)

- Backend (Django + DRF) hospedado em VPS com Ubuntu
- Banco de dados PostgreSQL configurado na própria VPS
- Servidor acessado via Shell (SSH)
- Configuração personalizada: nginx, gunicorn, serviços de fila ou background
- HTTPS via Let's Encrypt (Certbot)
- Monitoramento básico via logs (journalctl, systemd)

### Frontend

- Frontend (React.js) poderá ser hospedado no mesmo VPS ou futuramente migrado para serviços como Vercel/Netlify
- Comunicação entre frontend e backend feita via API pública (REST)
- Configuração de CORS e proxy conforme necessário

## Modularidade e Migração

A estrutura do projeto foi pensada para facilitar a migração futura para serviços como Render, Railway ou DigitalOcean, com o mínimo de mudanças:

- Variáveis de ambiente controladas por `.env` e arquivos de configuração separados
- Domínio pode ser reconfigurado via DNS
- Armazenamento de arquivos mantido externo (Google Drive, Dropbox etc.), evitando acoplamento à instância
- Configuração do frontend desacoplada do backend (pode ser movida independentemente)

## Práticas Recomendadas

- Uso de ambiente virtual (venv) e requirements.txt para reprodutibilidade
- Backups regulares do banco de dados
- Scripts de setup e deploy automatizados para facilitar portabilidade
- Logs centralizados com systemd ou soluções externas (opcional)
- Separação clara entre código da aplicação e configurações do servidor
