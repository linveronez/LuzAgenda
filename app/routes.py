from datetime import date, datetime, time, timedelta
from urllib.parse import quote
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for

from app import db
from app.models import AgendamentoLigacao, AgendamentoVisita, Paciente

bp = Blueprint("main", __name__)

VISIT_DAYS = {4, 5, 6}
CALL_DAYS = {2, 3, 4}
CALL_SLOTS = [f"{h:02d}:{m:02d}" for h in range(10, 18) for m in (0, 20, 40) if not (h == 17 and m > 40)]
VISIT_TIME_SLOTS = [f"{h:02d}:{m:02d}" for h in range(10, 14) for m in (0, 30)] + ["14:00"]
PARENTESCOS = ["Pai", "Mãe", "Irmã(o)", "Tia(o)", "Avó/Avô", "Esposa(o)", "Filha(o)", "Outros"]


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_time(value):
    return datetime.strptime(value, "%H:%M").time()


def visit_released(entry_date, target_date):
    days = (target_date - entry_date).days
    return days >= 30 or (target_date.weekday() in VISIT_DAYS and days >= 27)


def whatsapp_link(number, text):
    return f"https://wa.me/{number}?text={quote(text)}"


def require_admin():
    return session.get("admin_ok") is True


def date_choices(allowed_days, max_days):
    today = date.today()
    return [today + timedelta(days=offset) for offset in range(1, max_days + 1) if (today + timedelta(days=offset)).weekday() in allowed_days]


def weekend_range(reference=None):
    reference = reference or date.today()
    days_until_friday = (4 - reference.weekday()) % 7
    friday = reference + timedelta(days=days_until_friday)
    return friday, friday + timedelta(days=2)


def active_schedule_for_token(token, tipo=None):
    if not token:
        return None, None
    if tipo in (None, "visita"):
        visita = AgendamentoVisita.query.filter_by(token_uuid=token, status="confirmado").first()
        if visita:
            return "visita", visita
    if tipo in (None, "ligacao"):
        ligacao = AgendamentoLigacao.query.filter_by(token_uuid=token, status="confirmado").first()
        if ligacao:
            return "ligacao", ligacao
    return None, None


def ligacoes_enabled():
    return current_app.config.get("ENABLE_LIGACOES", False)


def active_future_visit_for_patient(paciente_id):
    query = AgendamentoVisita.query.filter(
        AgendamentoVisita.paciente_id == paciente_id,
        AgendamentoVisita.status == "confirmado",
        AgendamentoVisita.data_visita >= date.today(),
    )
    return query.order_by(AgendamentoVisita.data_visita, AgendamentoVisita.horario_inicio).first()


def companion_names(agendamento):
    nomes = [item.get("nome") for item in (agendamento.acompanhantes or []) if item.get("nome")]
    return ", ".join(nomes) if nomes else "Sem acompanhantes informados"


@bp.get("/")
def home():
    return render_template("home.html")


@bp.get("/api/pacientes")
def api_pacientes():
    termo = request.args.get("q", "").strip()
    query = Paciente.query.filter_by(status="ativo")
    if termo:
        query = query.filter(Paciente.nome_completo.ilike(f"%{termo}%"))
    pacientes = query.order_by(Paciente.nome_completo).limit(12).all()
    return jsonify([
        {"id": p.id, "nome": p.nome_completo, "data_entrada": p.data_entrada.isoformat()}
        for p in pacientes
    ])


@bp.get("/api/visitas/disponibilidade")
def api_visitas_disponibilidade():
    selected = parse_date(request.args["data"])
    count = AgendamentoVisita.query.filter_by(data_visita=selected, status="confirmado").count()
    return jsonify({"ocupadas": count, "lotado": count >= 5})


@bp.get("/api/ligacoes/slots")
def api_ligacoes_slots():
    if not ligacoes_enabled():
        return jsonify({"erro": "Modulo de ligacoes planejado para a V2."}), 503
    selected = parse_date(request.args["data"])
    rows = AgendamentoLigacao.query.filter_by(data_ligacao=selected, status="confirmado").all()
    usage = {slot: 0 for slot in CALL_SLOTS}
    for row in rows:
        usage[row.horario] = usage.get(row.horario, 0) + 1
    return jsonify([{"horario": slot, "ocupados": usage[slot], "lotado": usage[slot] >= 2} for slot in CALL_SLOTS])


@bp.route("/agendar-visita", methods=["GET", "POST"])
def agendar_visita():
    if request.method == "GET":
        return render_template("agendar_visita.html", datas=date_choices(VISIT_DAYS, 37), horarios=VISIT_TIME_SLOTS, parentescos=PARENTESCOS)

    token_atual = request.form.get("token_atual")
    if token_atual and active_schedule_for_token(token_atual, "visita")[1]:
        return render_template("erro.html", mensagem="Você já possui um agendamento ativo. Cancele o atual para fazer um novo.")

    paciente = Paciente.query.get_or_404(int(request.form["paciente_id"]))
    selected_date = parse_date(request.form["data_visita"])
    start = parse_time(request.form["horario_inicio"])
    duration = int(request.form["duracao"])
    end_dt = datetime.combine(selected_date, start) + timedelta(hours=duration)
    acompanhantes = []
    adultos_extra = 0
    criancas = 0
    for nome, parentesco, tipo in zip(request.form.getlist("ac_nome[]"), request.form.getlist("ac_parentesco[]"), request.form.getlist("ac_tipo[]")):
        if nome.strip():
            is_child = tipo == "crianca"
            acompanhantes.append({"nome": nome.strip(), "parentesco": parentesco.strip(), "eh_crianca": is_child})
            adultos_extra += 0 if is_child else 1
            criancas += 1 if is_child else 0

    total_adultos = 1 + adultos_extra
    count_day = AgendamentoVisita.query.filter_by(data_visita=selected_date, status="confirmado").count()
    if selected_date <= date.today() or selected_date > date.today() + timedelta(days=37) or selected_date.weekday() not in VISIT_DAYS:
        return render_template("erro.html", mensagem="Visitas só podem ser agendadas para sexta, sábado ou domingo.")
    if not visit_released(paciente.data_entrada, selected_date):
        return render_template("erro.html", mensagem="Este acolhido ainda está no período de carência para visitas.")
    if count_day >= 5:
        text = f"Olá! Vi que o dia {selected_date.strftime('%d/%m/%Y')} está lotado. Gostaria de verificar disponibilidade para visitar o acolhido {paciente.nome_completo}."
        return render_template("erro.html", mensagem="Este dia está lotado para visitas.", whatsapp=whatsapp_link(current_app.config["CT_WHATSAPP"], text))
    active_visit = active_future_visit_for_patient(paciente.id)
    if active_visit:
        return render_template("erro.html", mensagem=f"Este acolhido já possui visita confirmada para {active_visit.data_visita.strftime('%d/%m/%Y')} às {active_visit.horario_inicio.strftime('%H:%M')}. Fale com a equipe para ajustar ou cancelar o agendamento existente.")
    if total_adultos > 5:
        return render_template("erro.html", mensagem="O limite é de 5 adultos por visita. Crianças não entram nesse limite.")
    if criancas > 2:
        return render_template("erro.html", mensagem="O limite é de 2 crianças por visita.")
    if duration not in (2, 3, 4) or start < time(10) or end_dt.time() > time(16):
        return render_template("erro.html", mensagem="Escolha uma visita entre 10h e 16h, com duração de 2h a 4h.")

    token = str(uuid4())
    agendamento = AgendamentoVisita(
        token_uuid=token,
        paciente_id=paciente.id,
        responsavel_nome=request.form["visitante_nome"].strip(),
        responsavel_telefone=request.form.get("visitante_telefone", "").strip(),
        parentesco=request.form["parentesco"].strip(),
        data_visita=selected_date,
        horario_inicio=start,
        horario_fim=end_dt.time(),
        total_adultos=total_adultos,
        total_criancas=criancas,
        acompanhantes=acompanhantes,
        observacoes=request.form.get("observacoes", "").strip(),
    )
    paciente.total_visitas += 1
    db.session.add(agendamento)
    db.session.commit()
    return redirect(url_for("main.sucesso", tipo="visita", token=token))


@bp.route("/agendar-ligacao", methods=["GET", "POST"])
def agendar_ligacao():
    if not ligacoes_enabled():
        return render_template("erro.html", mensagem="O módulo de ligações foi reservado para a V2 e está em desenvolvimento.")
    if request.method == "GET":
        return render_template("agendar_ligacao.html", slots=CALL_SLOTS, datas=date_choices(CALL_DAYS, 14), parentescos=PARENTESCOS)

    token_atual = request.form.get("token_atual")
    if token_atual and active_schedule_for_token(token_atual, "ligacao")[1]:
        return render_template("erro.html", mensagem="Você já possui um agendamento ativo. Cancele o atual para fazer um novo.")

    paciente = Paciente.query.get_or_404(int(request.form["paciente_id"]))
    selected_date = parse_date(request.form["data_ligacao"])
    horario = request.form["horario"]
    if selected_date <= date.today() or selected_date > date.today() + timedelta(days=14) or selected_date.weekday() not in CALL_DAYS:
        return render_template("erro.html", mensagem="Ligações só podem ser agendadas para quarta, quinta ou sexta.")
    if (selected_date - paciente.data_entrada).days < 15:
        return render_template("erro.html", mensagem="Este acolhido ainda está no período de carência para ligações.")

    week_start = selected_date - timedelta(days=selected_date.weekday())
    week_end = week_start + timedelta(days=6)
    used = AgendamentoLigacao.query.filter(
        AgendamentoLigacao.paciente_id == paciente.id,
        AgendamentoLigacao.status == "confirmado",
        AgendamentoLigacao.data_ligacao.between(week_start, week_end),
    ).count()
    if used >= 1:
        return render_template("erro.html", mensagem="A cota semanal de 20 minutos deste acolhido já foi utilizada.")

    occupied = AgendamentoLigacao.query.filter_by(data_ligacao=selected_date, horario=horario, status="confirmado").all()
    used_numbers = {item.numero_celular for item in occupied}
    number_slot = 1 if 1 not in used_numbers else 2 if 2 not in used_numbers else None
    if number_slot is None:
        return render_template("erro.html", mensagem="Este horário já possui dois agendamentos.")

    token = str(uuid4())
    agendamento = AgendamentoLigacao(
        token_uuid=token,
        paciente_id=paciente.id,
        nome_solicitante=request.form["nome_solicitante"].strip(),
        telefone_solicitante=request.form["telefone_solicitante"].strip(),
        grau_parentesco=request.form["grau_parentesco"].strip(),
        data_ligacao=selected_date,
        horario=horario,
        numero_celular=number_slot,
    )
    paciente.total_ligacoes += 1
    db.session.add(agendamento)
    db.session.commit()
    return redirect(url_for("main.sucesso", tipo="ligacao", token=token))


@bp.get("/sucesso/<tipo>/<token>")
def sucesso(tipo, token):
    item = AgendamentoVisita.query.filter_by(token_uuid=token).first() if tipo == "visita" else AgendamentoLigacao.query.filter_by(token_uuid=token).first_or_404()
    if tipo == "visita":
        item = AgendamentoVisita.query.filter_by(token_uuid=token).first_or_404()
        text = f"Olá! Novo agendamento de visita:%0APaciente: {item.paciente.nome_completo}%0AResponsável: {item.responsavel_nome} ({item.parentesco})%0AAcompanhantes: {companion_names(item)}%0AData: {item.data_visita.strftime('%d/%m/%Y')} às {item.horario_inicio.strftime('%H:%M')}"
        links = {"ct": f"https://wa.me/{current_app.config['CT_WHATSAPP']}?text={text}"}
    else:
        text = f"Olá! Agendamento de ligação:%0APaciente: {item.paciente.nome_completo}%0ASolicitante: {item.nome_solicitante} ({item.grau_parentesco})%0AData: {item.data_ligacao.strftime('%d/%m/%Y')} às {item.horario}%0ATelefone para ligação: {item.telefone_solicitante}"
        links = {
            "atribuido": f"https://wa.me/{current_app.config[f'CEL_ACOLHIDOS_{item.numero_celular}']}?text={text}",
            "cel1": f"https://wa.me/{current_app.config['CEL_ACOLHIDOS_1']}?text={text}",
            "cel2": f"https://wa.me/{current_app.config['CEL_ACOLHIDOS_2']}?text={text}",
        }
    return render_template("sucesso.html", tipo=tipo, item=item, token=token, links=links)


@bp.route("/meu-agendamento")
def meu_agendamento():
    token = request.args.get("token", "")
    tipo = request.args.get("tipo")
    tipo, item = active_schedule_for_token(token, tipo)
    return render_template("meu_agendamento.html", token=token, tipo=tipo, item=item)


@bp.post("/cancelar/<tipo>/<token>")
def cancelar(tipo, token):
    item = AgendamentoVisita.query.filter_by(token_uuid=token).first_or_404() if tipo == "visita" else AgendamentoLigacao.query.filter_by(token_uuid=token).first_or_404()
    item.status = "cancelado"
    db.session.commit()
    return redirect(url_for("main.meu_agendamento", token=token))


@bp.post("/admin/cancelar/<tipo>/<int:item_id>")
def admin_cancelar(tipo, item_id):
    if not require_admin():
        return redirect(url_for("main.admin_login"))
    item = AgendamentoVisita.query.get_or_404(item_id) if tipo == "visita" else AgendamentoLigacao.query.get_or_404(item_id)
    item.status = "cancelado"
    db.session.commit()
    return redirect(url_for("main.admin_dashboard"))


@bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST" and request.form["senha"] == current_app.config["ADMIN_PASSWORD"]:
        session["admin_ok"] = True
        return redirect(url_for("main.admin_dashboard"))
    return render_template("admin_login.html")


@bp.get("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("main.home"))


@bp.route("/admin", methods=["GET"])
def admin_dashboard():
    if not require_admin():
        return redirect(url_for("main.admin_login"))
    today = date.today()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)
    friday, sunday = weekend_range(today)
    stats = {
        "pacientes": Paciente.query.filter_by(status="ativo").count(),
        "visitas_fds": AgendamentoVisita.query.filter(AgendamentoVisita.data_visita.between(friday, sunday), AgendamentoVisita.status == "confirmado").count(),
        "ligacoes_qua": AgendamentoLigacao.query.filter_by(data_ligacao=start_week + timedelta(days=2), status="confirmado").count(),
        "ligacoes_qui": AgendamentoLigacao.query.filter_by(data_ligacao=start_week + timedelta(days=3), status="confirmado").count(),
        "ligacoes_sex": AgendamentoLigacao.query.filter_by(data_ligacao=start_week + timedelta(days=4), status="confirmado").count(),
        "ligacoes_enabled": ligacoes_enabled(),
    }
    visitas = AgendamentoVisita.query.order_by(AgendamentoVisita.data_visita, AgendamentoVisita.horario_inicio).limit(20).all()
    ligacoes = AgendamentoLigacao.query.order_by(AgendamentoLigacao.data_ligacao, AgendamentoLigacao.horario).limit(20).all()
    call_dates = {
        "qua": start_week + timedelta(days=2),
        "qui": start_week + timedelta(days=3),
        "sex": start_week + timedelta(days=4),
    }
    return render_template("admin_dashboard.html", stats=stats, visitas=visitas, ligacoes=ligacoes, friday=friday, sunday=sunday, call_dates=call_dates)


@bp.get("/admin/agendamentos")
def admin_agendamentos():
    if not require_admin():
        return redirect(url_for("main.admin_login"))
    tipo = request.args.get("tipo", "visita")
    data_ini = request.args.get("inicio")
    data_fim = request.args.get("fim", data_ini)
    if tipo == "ligacao":
        query = AgendamentoLigacao.query
        date_field = AgendamentoLigacao.data_ligacao
    else:
        query = AgendamentoVisita.query
        date_field = AgendamentoVisita.data_visita
    if data_ini:
        query = query.filter(date_field.between(parse_date(data_ini), parse_date(data_fim)))
    items = query.filter_by(status="confirmado").order_by(date_field).all()
    return render_template("admin_agendamentos.html", tipo=tipo, items=items, data_ini=data_ini, data_fim=data_fim)


@bp.route("/admin/pacientes", methods=["GET", "POST"])
def admin_pacientes():
    if not require_admin():
        return redirect(url_for("main.admin_login"))
    if request.method == "POST":
        entrada = parse_date(request.form["data_entrada"])
        if entrada < date(2025, 1, 1) or entrada > date.today():
            return render_template("erro.html", mensagem="A data de entrada deve estar entre 01/01/2025 e a data atual.")
        paciente = Paciente(
            nome_completo=request.form["nome_completo"].strip(),
            data_entrada=entrada,
            status=request.form["status"],
        )
        db.session.add(paciente)
        db.session.commit()
        return redirect(url_for("main.admin_pacientes"))
    termo = request.args.get("q", "").strip()
    status = request.args.get("status", "")
    query = Paciente.query
    if termo:
        query = query.filter(Paciente.nome_completo.ilike(f"%{termo}%"))
    if status:
        query = query.filter_by(status=status)
    pacientes = query.order_by(Paciente.nome_completo).all()
    return render_template("admin_pacientes.html", pacientes=pacientes, termo=termo, status=status, hoje=date.today())


@bp.post("/admin/pacientes/<int:paciente_id>/status")
def admin_paciente_status(paciente_id):
    if not require_admin():
        return redirect(url_for("main.admin_login"))
    paciente = Paciente.query.get_or_404(paciente_id)
    paciente.status = request.form["status"]
    db.session.commit()
    return redirect(url_for("main.admin_pacientes"))
