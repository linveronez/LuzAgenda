# LuzAgenda

Sistema web de agendamento de visitas e ligações para a Clínica Luz da Vida — comunidade terapêutica de reabilitação de dependência química localizada em Itapecerica da Serra, São Paulo.

Acesse em produção: **https://luz-agenda.onrender.com**

---

## O que o sistema faz

- Agendamento público de **visitas** (sexta, sábado e domingo) sem necessidade de login
- Agendamento público de **ligações** (quarta, quinta e sexta) em slots de 20 minutos
- Controle automático de **carência**, **vagas por dia**, **limite de acompanhantes** e **cota semanal de ligações**
- **Painel administrativo** protegido por senha para gestão de pacientes e agendamentos
- **Notificação via WhatsApp** com mensagem pré-formatada ao confirmar agendamento
- **Token UUID** salvo em localStorage: o visitante consulta, visualiza e cancela o próprio agendamento sem login
- **Progressive Web App (PWA)**: instalável no celular como aplicativo nativo

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12 + Flask 3.0.3 |
| ORM | Flask-SQLAlchemy 3.1.1 |
| Banco (dev) | SQLite |
| Banco (produção) | PostgreSQL |
| Frontend | HTML5, CSS3, JavaScript puro |
| PWA | manifest.json + service worker |
| Servidor WSGI | Gunicorn |
| Hospedagem | Render |
| Versão | GitHub |

---

## Rodar localmente

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/LuzAgenda.git
cd LuzAgenda

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure o ambiente (opcional para dev)
cp .env.example .env
# Edite o .env se necessário

# 4. Rode a aplicação
python run.py
```

Acesse: `http://127.0.0.1:5000`

Em desenvolvimento, o banco SQLite é criado automaticamente em `instance/luzagenda.db`.

---

## Configuração (.env)

```env
SECRET_KEY=troque-por-chave-segura
ADMIN_PASSWORD=sua-senha-admin
DATABASE_URL=sqlite:///luzagenda.db       # dev
# DATABASE_URL=postgresql://...           # produção
CT_WHATSAPP=5511947395960                 # número da CT (visitas)
CEL_ACOLHIDOS_1=5511939219318            # celular 1 (ligações)
CEL_ACOLHIDOS_2=5511992588976            # celular 2 (ligações)
```

---

## Estrutura de arquivos

```
LuzAgenda/
├── app/
│   ├── __init__.py          # factory create_app, configuração Flask/SQLAlchemy
│   ├── models.py            # modelos: Paciente, AgendamentoVisita, AgendamentoLigacao
│   ├── routes.py            # todas as rotas e regras de negócio
│   ├── static/
│   │   ├── css/styles.css
│   │   ├── js/app.js
│   │   ├── manifest.json    # PWA
│   │   └── service-worker.js
│   └── templates/
│       ├── base.html
│       ├── home.html
│       ├── agendar_visita.html
│       ├── agendar_ligacao.html
│       ├── sucesso.html
│       ├── meu_agendamento.html
│       ├── erro.html
│       ├── _modal_info.html
│       ├── admin_login.html
│       ├── admin_dashboard.html
│       ├── admin_pacientes.html
│       └── admin_agendamentos.html
├── run.py                   # entrada de desenvolvimento
├── wsgi.py                  # entrada de produção (Gunicorn)
├── Procfile                 # configuração Render/Heroku
├── requirements.txt
├── .env.example
└── docs/
    ├── MANUAL_USUARIO.md
    ├── MANUAL_TECNICO.md
    └── DOCUMENTACAO_TECNICA.md
```

---

## Regras de negócio — resumo

### Visitas
- Dias: sexta, sábado e domingo
- Horário: 10h às 16h | Duração: 2h, 3h ou 4h
- Máximo 5 visitas por dia | Máximo 5 adultos por visita
- Crianças não entram no limite de adultos
- Carência: 30 dias após data de entrada do acolhido
  - Se os 30 dias caírem em dia de semana, libera o final de semana anterior (mínimo 27 dias)
- Lotação: redireciona para WhatsApp da CT com mensagem pronta

### Ligações
- Dias: quarta, quinta e sexta
- Slots de 20 min: 10:00, 10:20, 10:40 … 17:40
- 2 números disponíveis por slot (Cel Acolhidos 1 e 2)
- Carência: 15 dias após data de entrada
- Cota: 1 agendamento de ligação por acolhido por semana

---

## Deploy no Render

1. Fork/push para GitHub
2. Crie um Web Service no Render apontando para o repositório
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn wsgi:app`
5. Adicione as variáveis de ambiente no painel do Render
6. Provisione um PostgreSQL no Render e copie a `DATABASE_URL`

---

## Roadmap

### V2
- Edição de agendamento (além de cancelar)
- Notificação automática via WhatsApp Business API
- Exportação de agendamentos em Excel/CSV
- Gráficos no dashboard (visitas e ligações por semana/mês)
- Tela de busca de agendamento por telefone do responsável

### V3
- Níveis de acesso (admin / equipe terapêutica)
- Lembrete automático 24h antes via WhatsApp
- Controle granular da cota de 20 minutos por ligação
- Integração com o Sistema CT (cadastro de pacientes unificado)

### V4
- Notificações push (PWA avançado)
- Auditoria e logs de atividade
- API pública documentada para integração externa

---

## Contexto acadêmico

Desenvolvido como artefato do **Projeto Integrador — Desenvolvimento de Sistemas** (6º módulo), curso de **Análise e Desenvolvimento de Sistemas**, Universidade Santo Amaro (UNISA), 2026.1.

Orientador: Prof. Angelo Luiz da Cruz Oliveira  
Autor: Lincoln Veronez de Araujo

O projeto cobre também os objetivos da disciplina de adaptação **Laboratório de Programação** e serve de base arquitetural para o **Projeto Integrador — Desenvolvimento Web** (8º módulo).

---

## Licença

Código aberto para fins educacionais e de uso institucional sem fins lucrativos.
