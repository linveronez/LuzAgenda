from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

db = SQLAlchemy()


def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    database_url = os.getenv("DATABASE_URL", "sqlite:///luzagenda.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["ADMIN_PASSWORD"] = os.getenv("ADMIN_PASSWORD", "ctluzdavida2")
    app.config["CT_WHATSAPP"] = os.getenv("CT_WHATSAPP", "5511947395960")
    app.config["CEL_ACOLHIDOS_1"] = os.getenv("CEL_ACOLHIDOS_1", "5511939219318")
    app.config["CEL_ACOLHIDOS_2"] = os.getenv("CEL_ACOLHIDOS_2", "5511992588976")

    db.init_app(app)

    from app.routes import bp
    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()

    return app


app = create_app()
