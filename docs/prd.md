# Product Requirements Document (PRD)

## App Overview

**Name:** Record Label Manager  
**Description:** Um aplicativo web para donos e gestores de selos de música eletrônica, com o objetivo de facilitar a rotina de gestão de lançamentos, organização de calendário, análise de dados e armazenamento de documentos e conteúdos relacionados ao selo.  
**Tagline:** Automatize e organize o dia a dia da sua gravadora.

## Target Audience

Voltado para donos de gravadoras e membros de equipes que atuam na manutenção de selos de música eletrônica. Os usuários têm familiaridade com processos como o upload de lançamentos, organização de cronogramas, promoções musicais e gestão de catálogos.

## Key Features (em ordem de prioridade)

1. Gerenciador de lançamentos (cadastro completo de releases)
2. Integração entre módulos (calendário, promo, análise)
3. Calendário de prazos e lançamentos
4. Geração de e-mails promocionais
5. Análise de dados (vendas e desempenho)
6. Demos e pré-demos
7. Armazenamento de mixtapes
8. Armazenamento de documentos

## Platform

Web (desktop-first), com possibilidade futura de versão mobile para consulta.

## Assumptions

- Backend hospedado em VPS (Hostinger)
- Frontend em React.js
- Backend em Python com Django + DRF
- Armazenamento de arquivos via links externos (Google Drive, Dropbox etc.) ou versões compactas
- Navegação via sidebar lateral

## Success Metrics

- Redução no tempo de gestão de lançamentos
- Aumento na organização do cronograma de atividades
- Integração fluida entre lançamentos e análise
- Adoção por múltiplos selos independentes
