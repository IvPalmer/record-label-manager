# Security Plan

## Autenticação

- O sistema utiliza autenticação via e-mail/senha com JWT (JSON Web Token).
- Login social via Google OAuth2 também está habilitado.
- Autenticação de múltiplos fatores (2FA) **não será implementada por enquanto**.
- As senhas são armazenadas com hashing seguro (Django default: PBKDF2).

## Autorização

- Todos os usuários autenticados possuem os mesmos níveis de permissão no sistema atual.
- O campo `role` (owner, manager, assistant) será usado apenas como metadado visual.
- O controle de acesso avançado poderá ser implementado no futuro, conforme necessário.

## Proteção de dados sensíveis

- A aplicação não armazena arquivos pesados ou sensíveis diretamente; apenas links externos ou versões leves.
- Dados como contratos, documentos e faixas estão disponíveis somente para usuários autenticados.
- A aplicação não criptografa dados além das senhas neste estágio.

## Boas práticas implementadas

- Validação de inputs e sanitização para evitar SQL injection e ataques XSS
- Restrições de CORS ativadas para domínios autorizados
- Uso de variáveis de ambiente para segredos (chaves de API, tokens, etc.)
- Logs de erro não expõem informações sensíveis
- HTTPS configurado via Let's Encrypt na VPS
