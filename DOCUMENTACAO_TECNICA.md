# Documentação Técnica — LuzAgenda

**Versão 1.0 | Projeto Integrador — Desenvolvimento de Sistemas | UNISA 2026.1**  
Autor: Lincoln Veronez de Araujo | Orientador: Prof. Angelo Luiz da Cruz Oliveira

---

## 1. Contexto e motivação

O LuzAgenda nasceu de uma necessidade real: a Clínica Luz da Vida, comunidade terapêutica de reabilitação de dependência química em Itapecerica da Serra/SP, controlava visitas e ligações familiares de seus aproximadamente 62 acolhidos de forma manual. Anotações em papel, planilhas e mensagens avulsas de WhatsApp resultavam em conflitos de horário, descumprimento inadvertido das regras de carência e sobrecarga da equipe administrativa.

O autor atua profissionalmente na instituição como terapeuta holístico especializado em toxicodependência, o que permitiu que os requisitos fossem levantados com precisão e que a validação ocorresse em uso real desde o primeiro deploy.

---

## 2. Decisões de arquitetura

### Por que Flask e não Django ou FastAPI?

- **Flask** oferece leveza e controle total sem "magia" de framework: adequado para o escopo e para demonstração acadêmica
- **Django** traria overhead desnecessário (admin embutido, ORM com migrations obrigatórias) para o tamanho do projeto
- **FastAPI** seria excelente para API pura, mas o projeto usa templates server-side (Jinja2), tornando Flask mais natural

### Por que renderização server-side (SSR) e não SPA?

- Visitantes da instituição usam celulares de entrada com conexão instável — SSR garante que a página funcione sem JavaScript avançado
- Simplicidade: sem build step, sem bundler, sem complexidade de SPA para um formulário de agendamento
- O PWA complementa o SSR com cache de assets e instalação como app

### Por que JSON para acompanhantes e não tabela separada?

- A lista de acompanhantes é sempre lida e gravada junto com o agendamento — nunca consultada isoladamente
- Evita JOIN adicional sem ganho funcional na V1
- PostgreSQL suporta JSON nativamente com bom desempenho para consultas simples

### Por que token UUID no localStorage e não login?

- O público-alvo (familiares de acolhidos) não deve ser obrigado a criar conta para fazer um agendamento
- O token UUID v4 tem probabilidade de colisão desprezível (~1 em 5,3 × 10³⁶)
- A perda do token (troca de dispositivo, limpeza de cache) resulta apenas em perda de acesso à tela de consulta — o agendamento permanece válido no banco

---

## 3. Fluxo completo — agendamento de visita

```
1. GET /agendar-visita
   └── Renderiza formulário com:
       - datas válidas (próximos 37 dias, apenas sex/sáb/dom)
       - horários disponíveis (10:00 a 14:00, de 30 em 30 min)
       - lista de parentescos

2. JavaScript: autocomplete de paciente
   └── GET /api/pacientes?q=termo
       └── Retorna JSON: [{id, nome, data_entrada}]
   └── Seleção salva paciente_id em campo hidden

3. JavaScript: verificação de disponibilidade ao selecionar data
   └── GET /api/visitas/disponibilidade?data=YYYY-MM-DD
       └── Retorna {ocupadas: N, lotado: bool}
   └── Exibe aviso visual se lotado

4. POST /agendar-visita
   Validações server-side (em ordem):
   a. Token existente → bloqueia duplicata
   b. data_visita no passado ou fora do range → erro
   c. dia da semana não permitido → erro
   d. visit_released(data_entrada, data_visita) → erro de carência
   e. count_day >= 5 → erro com link WhatsApp
   f. total_adultos > 5 → erro
   g. criancas > 2 → erro
   h. duração inválida ou horário fora de 10h-16h → erro

5. Sucesso:
   - Gera UUID v4
   - Salva AgendamentoVisita no banco
   - Incrementa paciente.total_visitas
   - Redireciona para /sucesso/visita/<token>

6. GET /sucesso/visita/<token>
   - Exibe resumo
   - Link WhatsApp pré-formatado (wa.me)
   - Link ICS para Google Agenda
   - JavaScript salva token em localStorage["luzagenda_token"]
```

---

## 4. Fluxo completo — agendamento de ligação

```
1. GET /agendar-ligacao
   └── Renderiza com slots CALL_SLOTS e datas (próximos 14 dias, qua/qui/sex)

2. JavaScript: consulta slots ao selecionar data
   └── GET /api/ligacoes/slots?data=YYYY-MM-DD
       └── Retorna [{horario, ocupados, lotado}] para cada slot
   └── Renderiza slots: verde (livre), amarelo (1 ocupado), cinza (lotado)

3. POST /agendar-ligacao
   Validações:
   a. Token existente com ligação ativa → bloqueia
   b. Data inválida ou dia não permitido → erro
   c. (data - data_entrada).days < 15 → erro de carência
   d. Cota semanal: count de ligações confirmadas na semana >= 1 → erro
   e. Slot com ambos os números ocupados → erro

4. Atribuição de número:
   occupied = query por data+horario+status="confirmado"
   used_numbers = {item.numero_celular for item in occupied}
   number_slot = 1 if 1 not in used_numbers else 2 if 2 not in used_numbers else None

5. Sucesso:
   - Salva AgendamentoLigacao com numero_celular atribuído
   - Incrementa paciente.total_ligacoes
   - Redireciona para /sucesso/ligacao/<token>

6. Tela de sucesso exibe:
   - Qual celular foi atribuído
   - Botão WhatsApp para o celular atribuído (prioritário)
   - Botões alternativos para Cel 1 e Cel 2
```

---

## 5. API interna (JSON endpoints)

### GET /api/pacientes

```
Query params: q (string, optional)
Response: application/json

[
  {
    "id": 1,
    "nome": "João da Silva",
    "data_entrada": "2026-01-15"
  },
  ...
]

Filtros: status="ativo", ilike("%q%"), limit=12, order by nome
```

### GET /api/visitas/disponibilidade

```
Query params: data (YYYY-MM-DD, required)
Response: application/json

{
  "ocupadas": 3,
  "lotado": false
}
```

### GET /api/ligacoes/slots

```
Query params: data (YYYY-MM-DD, required)
Response: application/json

[
  { "horario": "10:00", "ocupados": 0, "lotado": false },
  { "horario": "10:20", "ocupados": 1, "lotado": false },
  { "horario": "10:40", "ocupados": 2, "lotado": true },
  ...
]
```

---

## 6. Configuração de WhatsApp

O sistema usa links `wa.me` (não a API oficial do WhatsApp Business). Esses links:

- Abrem o WhatsApp do dispositivo com número e mensagem pré-preenchidos
- São gratuitos e não exigem aprovação da Meta
- Requerem ação manual do usuário para enviar (um toque no botão "Enviar")
- Funcionam para qualquer número WhatsApp (não apenas Business)

**Formato do link:**

```
https://wa.me/[numero_com_DDI_sem_+]?text=[texto_url_encoded]
```

Os números são configurados por variáveis de ambiente:
- `CT_WHATSAPP` → número principal da instituição (usado em visitas e lotação)
- `CEL_ACOLHIDOS_1` → celular 1 para ligações
- `CEL_ACOLHIDOS_2` → celular 2 para ligações

---

## 7. Regras de carência — implementação detalhada

```python
VISIT_DAYS = {4, 5, 6}  # weekday(): seg=0, ..., dom=6

def visit_released(entry_date, target_date):
    days = (target_date - entry_date).days
    # Caso 1: 30+ dias → sempre liberado
    if days >= 30:
        return True
    # Caso 2: Entre 27-29 dias E é final de semana → liberado antecipado
    if days >= 27 and target_date.weekday() in VISIT_DAYS:
        return True
    return False
```

**Exemplo prático:**
- Entrada: 1º de janeiro
- 30 dias = 31 de janeiro (quinta-feira → dia de semana)
- Sistema libera: sábado 29 de janeiro (28 dias) ✓
- Sistema bloqueia: sexta 28 de janeiro (27 dias) — verifica se é fds → sim → ✓
- Sistema libera: sexta 28 de janeiro também ✓ (27 dias + é VISIT_DAY)

---

## 8. Segurança de sessão admin

```python
def require_admin():
    return session.get("admin_ok") is True

@bp.post("/admin/login")
def admin_login():
    if request.form["senha"] == current_app.config["ADMIN_PASSWORD"]:
        session["admin_ok"] = True
        return redirect(url_for("main.admin_dashboard"))
```

A sessão Flask é assinada com `SECRET_KEY`. Sem a chave correta, o cookie de sessão não pode ser forjado. Em produção, `SECRET_KEY` deve ser uma string aleatória longa (mínimo 32 caracteres).

---

## 9. Limitações conhecidas da V1

| Limitação | Impacto | Solução V2 |
|---|---|---|
| Token apenas no localStorage | Perde acesso ao trocar dispositivo | Associar token ao telefone do responsável |
| Cota de ligações: 1/semana (não 20 min) | Não divide a cota entre múltiplos solicitantes | Cálculo por duração acumulada |
| Sem edição de agendamento | Obriga cancelar e recriar | Tela de edição de data/horário |
| Senha admin em plain text | Adequada para V1 de equipe pequena | Hash bcrypt + usuários individuais |
| Sem proteção CSRF | Risco em formulários públicos | Flask-WTF |
| Sem paginação no admin | Pode ficar lento com muitos registros | Paginação SQLAlchemy |
| Sem testes automatizados | Validação apenas manual | pytest + pytest-flask |

---

## 10. Checklist de validação antes de apresentação

- [ ] Login admin funciona com senha configurada
- [ ] Autocomplete de paciente retorna resultados ao digitar
- [ ] Agendamento de visita valida carência corretamente
- [ ] Agendamento de visita bloqueia dia lotado com link WhatsApp
- [ ] Agendamento de visita bloqueia mais de 5 adultos
- [ ] Agendamento de ligação exibe slots coloridos (verde/amarelo/cinza)
- [ ] Agendamento de ligação valida carência de 15 dias
- [ ] Agendamento de ligação atribui número automaticamente
- [ ] Tela de sucesso exibe botões WhatsApp corretos
- [ ] "Meu Agendamento" exibe dados do agendamento feito no mesmo navegador
- [ ] Cancelamento funciona pelo visitante e pelo admin
- [ ] Dashboard admin exibe contadores corretos
- [ ] PWA: botão "Adicionar à tela inicial" aparece no mobile
- [ ] Deploy no Render responde em produção com PostgreSQL

---

## 11. Comandos úteis

```bash
# Desenvolvimento local
python run.py

# Produção local (simular Render)
gunicorn wsgi:app --bind 0.0.0.0:5000 --workers 2

# Inspecionar banco SQLite
sqlite3 instance/luzagenda.db ".schema"
sqlite3 instance/luzagenda.db "SELECT nome_completo, data_entrada FROM pacientes;"

# Ver agendamentos do dia
sqlite3 instance/luzagenda.db \
  "SELECT * FROM agendamentos_visita WHERE data_visita = date('now');"

# Contar ligações da semana por paciente
sqlite3 instance/luzagenda.db \
  "SELECT paciente_id, COUNT(*) FROM agendamentos_ligacao
   WHERE status='confirmado'
   AND data_ligacao BETWEEN date('now', 'weekday 0', '-6 days') AND date('now', 'weekday 0')
   GROUP BY paciente_id;"

# Instalar dependências
pip install -r requirements.txt

# Atualizar requirements após instalar novo pacote
pip freeze > requirements.txt
```
