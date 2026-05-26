# Manual Técnico — LuzAgenda

**Sistema de agendamento de visitas e ligações — Clínica Luz da Vida**  
Versão 1.0 | 2026

---

## 1. Visão geral da arquitetura

O LuzAgenda é uma aplicação web monolítica em Python/Flask com separação de responsabilidades em camadas. Não utiliza framework de frontend (React, Vue etc.) — todo o frontend é HTML5, CSS3 e JavaScript puro renderizados via templates Jinja2 no servidor.

```
Browser ──► Flask (routes.py) ──► SQLAlchemy ORM ──► SQLite / PostgreSQL
               │
               └──► Jinja2 Templates ──► HTML renderizado
               └──► JSON API (/api/*) ──► JavaScript (autocomplete, slots)
```

---

## 2. Stack completa

| Componente | Tecnologia | Versão |
|---|---|---|
| Linguagem | Python | 3.12 |
| Framework web | Flask | 3.0.3 |
| ORM | Flask-SQLAlchemy | 3.1.1 |
| Banco (dev) | SQLite | built-in |
| Banco (prod) | PostgreSQL | via psycopg2-binary |
| Variáveis de ambiente | python-dotenv | 1.0.1 |
| Servidor WSGI | Gunicorn | 22.0.0 |
| Hospedagem | Render | — |
| Controle de versão | GitHub | — |
| PWA | manifest.json + service worker | — |

---

## 3. Estrutura de diretórios

```
LuzAgenda/
├── app/
│   ├── __init__.py          # create_app(): factory com SQLAlchemy, Blueprint, PWA config
│   ├── models.py            # Paciente, AgendamentoVisita, AgendamentoLigacao
│   ├── routes.py            # Blueprint "main" com todas as rotas e lógica de negócio
│   ├── static/
│   │   ├── css/styles.css   # estilos globais
│   │   ├── js/app.js        # autocomplete, modal, localStorage token
│   │   ├── manifest.json    # PWA: nome, ícones, tema, display standalone
│   │   └── service-worker.js # cache de assets estáticos
│   └── templates/
│       ├── base.html             # layout base com PWA meta tags
│       ├── home.html             # landing page
│       ├── _modal_info.html      # modal informativo (incluso nos forms)
│       ├── agendar_visita.html   # formulário de visita
│       ├── agendar_ligacao.html  # formulário de ligação
│       ├── sucesso.html          # confirmação + links WhatsApp + ICS
│       ├── meu_agendamento.html  # consulta/cancelamento por token
│       ├── erro.html             # tela de erro genérica
│       ├── admin_login.html
│       ├── admin_dashboard.html
│       ├── admin_pacientes.html
│       └── admin_agendamentos.html
├── run.py          # python run.py → Flask dev server (porta 5000)
├── wsgi.py         # gunicorn wsgi:app → produção
├── Procfile        # web: gunicorn wsgi:app
├── requirements.txt
├── .env.example
└── docs/
```

---

## 4. Modelos de dados (models.py)

### Paciente

```python
class Paciente(db.Model):
    id              Integer, PK
    nome_completo   String(180), NOT NULL, index
    data_entrada    Date, NOT NULL
    status          String(20), default="ativo"    # ativo | inativo
    total_visitas   Integer, default=0
    total_ligacoes  Integer, default=0

    visitas         → relationship AgendamentoVisita
    ligacoes        → relationship AgendamentoLigacao
```

### AgendamentoVisita

```python
class AgendamentoVisita(db.Model):
    id                  Integer, PK
    token_uuid          String(36), UNIQUE, index   # controle sem login
    paciente_id         FK → pacientes.id
    responsavel_nome    String(160)
    responsavel_telefone String(30)
    parentesco          String(80)
    data_visita         Date, index
    horario_inicio      Time
    horario_fim         Time
    total_adultos       Integer
    total_criancas      Integer
    acompanhantes       JSON    # [{nome, parentesco, eh_crianca}]
    status              String(20), default="confirmado"  # confirmado | cancelado
    observacoes         Text, nullable
    criado_em           DateTime, default=utcnow
```

### AgendamentoLigacao

```python
class AgendamentoLigacao(db.Model):
    id                   Integer, PK
    token_uuid           String(36), UNIQUE, index
    paciente_id          FK → pacientes.id
    nome_solicitante     String(160)
    telefone_solicitante String(30)
    grau_parentesco      String(80)
    data_ligacao         Date, index
    horario              String(5)   # "HH:MM"
    numero_celular       Integer     # 1 ou 2
    status               String(20), default="confirmado"
    criado_em            DateTime, default=utcnow
```

---

## 5. Rotas (routes.py)

### Públicas

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Home / landing page |
| GET | `/api/pacientes?q=termo` | Autocomplete de pacientes (JSON) |
| GET | `/api/visitas/disponibilidade?data=YYYY-MM-DD` | Contagem de visitas no dia (JSON) |
| GET | `/api/ligacoes/slots?data=YYYY-MM-DD` | Slots de ligação com ocupação (JSON) |
| GET/POST | `/agendar-visita` | Formulário e processamento de visita |
| GET/POST | `/agendar-ligacao` | Formulário e processamento de ligação |
| GET | `/sucesso/<tipo>/<token>` | Tela de confirmação |
| GET | `/meu-agendamento?token=&tipo=` | Consulta por token |
| POST | `/cancelar/<tipo>/<token>` | Cancelamento pelo visitante |

### Admin (requer session["admin_ok"])

| Método | Rota | Descrição |
|---|---|---|
| GET/POST | `/admin/login` | Login administrativo |
| GET | `/admin/logout` | Logout |
| GET | `/admin` | Dashboard |
| GET | `/admin/agendamentos?tipo=&inicio=&fim=` | Listagem filtrada |
| GET/POST | `/admin/pacientes` | Cadastro e listagem de pacientes |
| POST | `/admin/pacientes/<id>/status` | Ativar/inativar paciente |
| POST | `/admin/cancelar/<tipo>/<id>` | Cancelar agendamento (admin) |

---

## 6. Lógica de negócio — funções auxiliares

```python
VISIT_DAYS = {4, 5, 6}          # sexta=4, sábado=5, domingo=6
CALL_DAYS  = {2, 3, 4}          # quarta=2, quinta=3, sexta=4
CALL_SLOTS = ["10:00", "10:20", ..., "17:40"]   # 24 slots
VISIT_TIME_SLOTS = ["10:00", "10:30", ..., "14:00"]

def visit_released(entry_date, target_date):
    # True se (dias >= 30) OU (é fds E dias >= 27)
    days = (target_date - entry_date).days
    return days >= 30 or (target_date.weekday() in VISIT_DAYS and days >= 27)

def date_choices(allowed_days, max_days):
    # Retorna lista de datas futuras válidas (usado nos selects dos formulários)

def weekend_range(reference):
    # Retorna (sexta, domingo) do fds da semana de referência
    # Usado no dashboard admin para exibir visitas do fds

def active_schedule_for_token(token, tipo):
    # Busca agendamento confirmado pelo token UUID
    # Usado em /meu-agendamento e para bloquear duplicatas

def whatsapp_link(number, text):
    # Gera link wa.me com texto URL-encoded
```

---

## 7. Controle de acesso sem login (localStorage + token UUID)

Ao criar um agendamento (visita ou ligação), o sistema:

1. Gera um UUID v4 (`str(uuid4())`)
2. Salva no banco no campo `token_uuid`
3. Redireciona para `/sucesso/<tipo>/<token>` — URL que contém o token
4. O JavaScript em `app.js` salva o token em `localStorage` com a chave `luzagenda_token`

Na página `/meu-agendamento`, o frontend lê o token do localStorage e envia como parâmetro de query. O servidor busca o agendamento pelo token e exibe os detalhes ou a mensagem "nenhum agendamento ativo".

**Limitação conhecida:** o token é válido apenas no mesmo navegador e dispositivo. Se o usuário trocar de dispositivo ou limpar o cache, perderá o acesso ao agendamento (mas o agendamento permanece no banco).

---

## 8. Progressive Web App (PWA)

### manifest.json

```json
{
  "name": "LuzAgenda",
  "short_name": "LuzAgenda",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#2563eb",
  "icons": [{ "src": "/static/img/logo-luz-da-vida.jpg", "sizes": "192x192" }]
}
```

### service-worker.js

Estratégia de cache: cache-first para assets estáticos (CSS, JS, imagens). Requisições de API e templates sempre buscam da rede.

### Instalação no iOS (Safari)

1. Abrir o sistema no Safari
2. Tocar no botão de compartilhamento (ícone de caixa com seta)
3. Selecionar "Adicionar à Tela de Início"

### Instalação no Android (Chrome)

1. Abrir o sistema no Chrome
2. Tocar nos três pontos do menu
3. Selecionar "Adicionar à tela inicial" ou aguardar o banner automático

---

## 9. Configuração de ambiente

### Variáveis de ambiente (.env)

```env
SECRET_KEY=chave-secreta-aleatoria          # obrigatório em produção
ADMIN_PASSWORD=senha-do-painel-admin        # default: ctluzdavida2
DATABASE_URL=sqlite:///luzagenda.db         # dev local
# DATABASE_URL=postgresql+psycopg://user:pass@host/db  # produção
CT_WHATSAPP=5511947395960                   # número WhatsApp da CT
CEL_ACOLHIDOS_1=5511939219318              # celular 1 para ligações
CEL_ACOLHIDOS_2=5511992588976              # celular 2 para ligações
```

### Compatibilidade de DATABASE_URL

O `__init__.py` converte automaticamente as variantes do Render:

```python
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
```

---

## 10. Deploy no Render

### Configuração do serviço

| Campo | Valor |
|---|---|
| Environment | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn wsgi:app` |
| Branch | `main` |

### Variáveis de ambiente no Render

Adicione todas as variáveis do `.env` no painel "Environment" do serviço Render. Não suba o arquivo `.env` para o repositório.

### Banco PostgreSQL

1. No painel Render, crie um banco PostgreSQL (plano free disponível)
2. Copie a "Internal Database URL"
3. Adicione como variável `DATABASE_URL` no serviço web

O SQLAlchemy cria todas as tabelas automaticamente no primeiro deploy via `db.create_all()` no `create_app()`.

---

## 11. Execução local para desenvolvimento

```bash
# Desenvolvimento com reload automático
python run.py

# Simular produção localmente
gunicorn wsgi:app --bind 0.0.0.0:5000

# Verificar banco SQLite
sqlite3 instance/luzagenda.db ".tables"
sqlite3 instance/luzagenda.db "SELECT * FROM pacientes;"
```

---

## 12. Segurança

- **Senha admin:** armazenada apenas como variável de ambiente, comparada em plain text (adequado para V1 com senha compartilhada pela equipe). Para V2, implementar hash bcrypt.
- **SECRET_KEY:** usada para assinatura da sessão Flask. Trocar obrigatoriamente em produção.
- **HTTPS:** o Render provisiona HTTPS automaticamente. Nunca opere em HTTP em produção.
- **Sem autenticação pública:** a área pública não exige login. O controle de duplicatas é feito pelo token UUID + validação server-side.
- **SQL Injection:** mitigado pelo ORM SQLAlchemy (queries parametrizadas).
- **CSRF:** não implementado em V1 (formulários simples sem dados sensíveis financeiros ou médicos). Adicionar Flask-WTF em V2.

---

## 13. Pontos de atenção para V2

- Substituir o controle de cota de ligações de "1 agendamento por semana" para "20 minutos totais" com cálculo granular
- Adicionar tela de edição de agendamento (data/horário)
- Implementar Flask-WTF para proteção CSRF
- Adicionar paginação nas listagens do admin
- Implementar backup automático do banco PostgreSQL
- Considerar Alembic para migrações de schema sem perda de dados
- Adicionar testes automatizados (pytest + pytest-flask)
