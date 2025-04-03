# User Flow

## Onboarding Inicial

```mermaid
graph TD
  A[Início / Login] --> B{Usuário já tem conta?}
  B -- Não --> C[Cria conta com e-mail ou Google]
  B -- Sim --> D[Faz login]
  C --> E[Verifica se tem gravadora]
  D --> E
  E -- Não tem --> F[Usuário é orientado a criar nova gravadora]
  F --> G[Preenche dados da gravadora]
  G --> H[Redirecionado para módulo de Releases]
  E -- Já tem --> H
```

## Módulo de Gravadoras

- Se o usuário possui mais de uma label, ele escolhe qual vai gerenciar no momento (pode alternar a qualquer hora)
- Após a escolha, o sistema carrega todos os dados associados àquela gravadora (artistas, releases, documentos etc.)

## Cadastro e Importação de Releases

```mermaid
graph TD
  H[Entrou no módulo de Releases] --> I{Tem lançamentos já?}
  I -- Não --> J[Opção: Criar novo lançamento manualmente]
  I -- Sim ou quer importar --> K[Opção: Importar releases via Google Drive]
  K --> L[Conecta Google Drive e seleciona pasta-base]
  L --> M[Ferramenta lê estrutura de pastas organizada por: Ano / Número do Catálogo / Arquivos]
  M --> N[Importa metadados, arquivos leves, imagem de capa]
  J --> O[Preenche título, data, catálogo, faixas, tags, links etc.]
  N --> O
  O --> P[Salva como rascunho ou publica]
```

## Fluxo nos Outros Módulos

- **Artistas:** Cadastrar manualmente ou importar via CSV (futuramente)
- **Mixtapes:** Upload ou link externo, com definição de artista e data
- **Documentos:** Upload direto ou arrastar arquivos (contratos, notas etc.)
- **Demos:** Visualizar, escutar e mudar status (novo, aceito, recusado)
- **Calendário:** Visualizar datas vinculadas a releases, mixtapes, demos

## Observações

- Importação via Drive será opcional, com suporte a estrutura padronizada de pastas
- O login pode ser pulado em ambiente de desenvolvimento (dev mode)
- O fluxo será estendido conforme surgirem novos módulos (ex: analytics, promo)
