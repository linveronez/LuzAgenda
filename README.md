# LuzAgenda

Sistema web para agendamento de visitas e ligações da Clínica Luz da Vida.

## Rodar localmente

```bash
python -m pip install -r requirements.txt
python run.py
```

Acesse `http://127.0.0.1:5000`.

## Configuração

Copie `.env.example` para `.env` e ajuste:

- `SECRET_KEY`
- `ADMIN_PASSWORD`
- `DATABASE_URL`
- `CT_WHATSAPP`
- `CEL_ACOLHIDOS_1`
- `CEL_ACOLHIDOS_2`

Em desenvolvimento, pode usar SQLite. No Render, configure `DATABASE_URL` com PostgreSQL.
