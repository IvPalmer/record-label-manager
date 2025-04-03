```mermaid
flowchart TD

A[Login Page] --> B{Usuário já tem conta?}
B -- Não --> C[Cria conta (e-mail ou Google)]
B -- Sim --> D[Faz login]

C --> E{Tem gravadora?}
D --> E

E -- Não --> F[Cria nova gravadora]
F --> G[Preenche nome, descrição, país etc.]
G --> H[Redirecionado para módulo de Releases]

E -- Sim --> H

H[Entrou no módulo de Releases] --> I{Deseja importar do Drive?}
I -- Sim --> J[Conecta com Google Drive]
J --> K[Seleciona pasta com estrutura padrão (Ano/Catálogo)]
K --> L[Ferramenta extrai metadados e arquivos]
L --> M[Importa dados como rascunhos]
I -- Não --> N[Cria novo lançamento manualmente]

M --> O[Revisar, editar e salvar]
N --> O

O --> P[Acessa outros módulos via sidebar]
P --> Q[Artistas, Mixtapes, Documentos, Demos, Calendário]
```
