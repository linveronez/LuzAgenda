from datetime import datetime
from app import db


class Paciente(db.Model):
    __tablename__ = "pacientes"

    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(180), nullable=False, index=True)
    data_entrada = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ativo")
    total_visitas = db.Column(db.Integer, nullable=False, default=0)
    total_ligacoes = db.Column(db.Integer, nullable=False, default=0)

    visitas = db.relationship("AgendamentoVisita", backref="paciente", lazy=True)
    ligacoes = db.relationship("AgendamentoLigacao", backref="paciente", lazy=True)


class AgendamentoVisita(db.Model):
    __tablename__ = "agendamentos_visita"

    id = db.Column(db.Integer, primary_key=True)
    token_uuid = db.Column(db.String(36), nullable=False, unique=True, index=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"), nullable=False)
    responsavel_nome = db.Column(db.String(160), nullable=False)
    responsavel_telefone = db.Column(db.String(30), nullable=False)
    parentesco = db.Column(db.String(80), nullable=False)
    data_visita = db.Column(db.Date, nullable=False, index=True)
    horario_inicio = db.Column(db.Time, nullable=False)
    horario_fim = db.Column(db.Time, nullable=False)
    total_adultos = db.Column(db.Integer, nullable=False)
    total_criancas = db.Column(db.Integer, nullable=False)
    acompanhantes = db.Column(db.JSON, nullable=False, default=list)
    status = db.Column(db.String(20), nullable=False, default="confirmado")
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class AgendamentoLigacao(db.Model):
    __tablename__ = "agendamentos_ligacao"

    id = db.Column(db.Integer, primary_key=True)
    token_uuid = db.Column(db.String(36), nullable=False, unique=True, index=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"), nullable=False)
    nome_solicitante = db.Column(db.String(160), nullable=False)
    telefone_solicitante = db.Column(db.String(30), nullable=False)
    grau_parentesco = db.Column(db.String(80), nullable=False)
    data_ligacao = db.Column(db.Date, nullable=False, index=True)
    horario = db.Column(db.String(5), nullable=False)
    numero_celular = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="confirmado")
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
