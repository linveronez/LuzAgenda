from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from dotenv import load_dotenv
import os

db = SQLAlchemy()


def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        if os.getenv("RENDER"):
            raise RuntimeError("DATABASE_URL precisa estar configurada no Render para usar PostgreSQL persistente.")
        database_url = "sqlite:///luzagenda.db"
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["ADMIN_PASSWORD"] = os.getenv("ADMIN_PASSWORD", "ctluzdavida2")
    app.config["CT_WHATSAPP"] = os.getenv("CT_WHATSAPP", "5511947395960")
    app.config["CEL_ACOLHIDOS_1"] = os.getenv("CEL_ACOLHIDOS_1", "5511939219318")
    app.config["CEL_ACOLHIDOS_2"] = os.getenv("CEL_ACOLHIDOS_2", "5511992588976")
    app.config["ENABLE_LIGACOES"] = os.getenv("ENABLE_LIGACOES", "false").lower() == "true"

    db.init_app(app)

    from app.routes import bp
    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()
        ensure_schema()

    return app


def ensure_schema():
    columns = {column["name"] for column in inspect(db.engine).get_columns("pacientes")}
    if "cadastro_ficticio" not in columns:
        db.session.execute(text("ALTER TABLE pacientes ADD COLUMN cadastro_ficticio BOOLEAN NOT NULL DEFAULT FALSE"))
        db.session.commit()


app = create_app()
