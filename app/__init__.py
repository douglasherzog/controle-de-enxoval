from flask import Flask

from .models import db
from .routes import main_bp, seed_tipos_peca


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="change-me",
        SQLALCHEMY_DATABASE_URI="postgresql+psycopg://controle:controle123@db:5432/controle_enxoval",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    app.config.from_prefixed_env()
    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_tipos_peca()

    app.register_blueprint(main_bp)
    return app
