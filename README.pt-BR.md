# linkedin-cli

<p>
  <img src="https://img.shields.io/badge/vers%C3%A3o-v0.1.1-blue" alt="Versão">
  <img src="https://img.shields.io/badge/licen%C3%A7a-MIT-green" alt="Licença">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/testes-159%20passando-brightgreen" alt="Testes">
  <img src="https://img.shields.io/badge/cobertura-100%25-brightgreen" alt="Cobertura">
</p>

**Idiomas:** [English](README.md) | [Português](#)

CLI para publicar e gerenciar posts no seu perfil pessoal do LinkedIn via terminal.

## Funcionalidades

- **Publicar** posts de texto ou imagem no perfil pessoal
- **Upload de imagem** com inicialização automática de mídia e texto alternativo acessível
- **Exibir** detalhes de um post pelo id
- **Deletar** posts pelo id
- **Listar** posts recentes (quando o escopo `r_member_social` é concedido)
- **Autenticação OAuth 2.0** — fluxo de 3 pernas com servidor de callback local
- **Interface bilíngue** — mensagens em inglês (padrão) ou português
- **Logs cíclicos da aplicação** — registra todos os comandos, mantendo apenas o número de dias configurado (padrão 120)
- **Escape do little text** — escapa automaticamente os caracteres reservados do LinkedIn, evitando o truncamento silencioso pela Posts API

## Instalação

```bash
pip install .
```

Desenvolvimento:

```bash
pip install -e ".[test,dev]"
```

## Configuração

1. Acesse [linkedin.com/developers](https://www.linkedin.com/developers/) e crie um app (requer uma LinkedIn Page)
2. Na aba **Products**, ative **Share on LinkedIn** (escopo `w_member_social`)
3. Na aba **Auth**, adicione o redirect URI `http://localhost:8080` em OAuth 2.0 settings
4. Copie o **Client ID** e o **Client Secret** da aba Auth
5. Configure o CLI:

```bash
linkedin config set --client-id SEU_CLIENT_ID --client-secret SEU_CLIENT_SECRET
```

> Todos os arquivos de configuração ficam em `~/.linkedin-cli/`:
> - `config.json` — credenciais e configurações do app
> - `token.json` — token de acesso OAuth (gerado automaticamente pelo `auth login`)
> - `logs/linkedin-cli.log` — log cíclico da aplicação (rotação diária, mantém `log_days`)
>
> Apps self-serve (Share on LinkedIn) recebem um token de acesso válido por **60 dias** sem refresh token. Quando o token expirar, execute `linkedin auth login` novamente.

## Uso

### Autenticação

```bash
linkedin auth login      # Abre o navegador e autentica
linkedin auth status     # Verifica o status da autenticação
linkedin auth logout     # Remove o token local
```

### Criar um post

```bash
# Post de texto
linkedin post create -t "Olá, LinkedIn!"

# Post de texto a partir de arquivo (Markdown é suportado)
linkedin post create -f post.md

# Post com imagem
linkedin post create -t "Veja isso" -i ./imagem.png --alt-text "Descrição da imagem"

# Restringir visibilidade para conexões
linkedin post create -t "Olá, rede!" --visibility CONNECTIONS
```

> A Posts API renderiza o commentary como *little text*: caracteres reservados
> sem escape (`\ | { } @ [ ] ( ) < > # * _ ~`) truncam o post silenciosamente. O
> CLI os escapa automaticamente e as barras não são renderizadas. Use
> `--no-escape` somente se o texto não contiver nenhum desses caracteres — o CLI
> avisa se contiver.

### Exibir / Deletar

```bash
linkedin post show urn:li:share:123456
linkedin post delete urn:li:share:123456
```

### Listar posts

```bash
linkedin post list
linkedin post list --max 20
```

> Listar posts usa o escopo restrito `r_member_social`, que não é concedido a apps self-serve. Nesse caso o comando retorna uma mensagem clara e o CLI recorre ao histórico local (planejado).

### Configuração

```bash
# Exibir a configuração atual (client_secret é mascarado)
linkedin config show

# Definir o idioma da interface (en padrão, pt suportado)
linkedin config set --language pt

# Definir retenção de logs em dias (cíclico, deleta os mais antigos)
linkedin config set --log-days 120

# Definir timeout de requisição em segundos (padrão 60)
linkedin config set --request-timeout 60

# Definir o cabeçalho LinkedIn-Version (YYYYMM)
linkedin config set --api-version 202604

# Atualizar credenciais ou redirect URI do app
linkedin config set --client-id NOVO_ID --client-secret NOVO_SECRET
linkedin config set --redirect-uri http://localhost:8080
```

A configuração é salva em `~/.linkedin-cli/config.json`.
Variáveis de ambiente sobrescrevem a configuração do arquivo:

| Variável | Descrição |
|---|---|
| `LINKEDIN_CLI_CLIENT_ID` | Client ID do app no LinkedIn |
| `LINKEDIN_CLI_CLIENT_SECRET` | Client Secret do app no LinkedIn |
| `LINKEDIN_CLI_REDIRECT_URI` | Redirect URI do OAuth (padrão `http://localhost:8080`) |
| `LINKEDIN_CLI_API_VERSION` | Cabeçalho `LinkedIn-Version` (padrão `202604`) |
| `LINKEDIN_CLI_LANGUAGE` | Idioma da interface, `en` ou `pt` (padrão `en`) |
| `LINKEDIN_CLI_LOG_DAYS` | Retenção de logs em dias (padrão 120) |
| `LINKEDIN_CLI_REQUEST_TIMEOUT` | Timeout de requisição em segundos (padrão 60) |

### Logs da Aplicação

O CLI escreve um log cíclico em `~/.linkedin-cli/logs/linkedin-cli.log`. Ele registra todos os comandos executados. O log rotaciona diariamente e arquivos antigos são deletados após `log_days` dias (padrão 120, configurável via `config set --log-days` ou `LINKEDIN_CLI_LOG_DAYS`).

A interface e o help do CLI são em inglês por padrão. As mensagens de saída seguem a config `language` (`en` ou `pt`).

## Estrutura do Projeto

```
linkedin-cli/
├── src/
│   └── linkedin_cli/
│       ├── __init__.py     # API pública com __all__
│       ├── __main__.py     # Entry point python -m linkedin_cli
│       ├── auth.py         # Autenticação OAuth 2.0 (AuthService)
│       ├── cli.py          # Interface CLI (click)
│       ├── client.py       # Wrapper da API REST do LinkedIn (LinkedInClient)
│       ├── config.py       # Dataclass Config + env vars
│       ├── formatter.py    # Escape do little text (escape_little_text)
│       ├── i18n.py         # Catálogos de mensagens (en/pt) e t()
│       ├── logging_utils.py # Logger rotativo cíclico (TimedRotatingFileHandler)
│       └── models.py       # Dataclasses: Post, QueuedPost, MediaAsset, AuthToken
├── tests/
│   ├── conftest.py         # Fixtures compartilhadas
│   ├── test_auth.py
│   ├── test_cli.py         # Testes com Click CliRunner
│   ├── test_client.py
│   ├── test_config.py
│   ├── test_formatter.py
│   ├── test_i18n.py
│   ├── test_logging_utils.py
│   └── test_models.py
├── assets/
│   └── logo.png            # Logo da aplicação
├── tools/
│   └── make_logo.py        # Script gerador do logo
├── pyproject.toml          # Config (ruff, pytest, mypy, bandit, packaging)
├── README.md               # Este arquivo
└── README.pt-BR.md         # Versão em português
```

## Testes

```bash
pytest                    # 159 testes
pytest --cov=             # Cobertura (100%)
```

## Qualidade

```bash
ruff check .              # Linter (0 problemas)
ruff format --check .     # Formatação
mypy src/linkedin_cli/    # Tipagem estática (strict)
bandit -r src/linkedin_cli/ -c pyproject.toml  # SAST
```
