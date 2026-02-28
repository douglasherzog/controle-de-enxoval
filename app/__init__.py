from flask import Flask
from flask_login import LoginManager

from .models import Configuracao, User, db
from .rfid import rfid_bp
from .routes import main_bp, seed_tamanhos, seed_tipos_peca


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

    login_manager = LoginManager()
    login_manager.login_view = "main.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        return db.session.get(User, int(user_id))

    with app.app_context():
        db.create_all()
        if not Configuracao.query.first():
            db.session.add(Configuracao(periodicidade_revisao_dias=7))
            db.session.commit()
        if not User.query.filter_by(username="admin").first():
            admin_user = User(username="admin", is_admin=True)
            admin_user.set_password("admin")
            admin_user.must_change_password = True
            db.session.add(admin_user)
            db.session.commit()
        else:
            admin_user = User.query.filter_by(username="admin").first()
            if (
                admin_user
                and admin_user.check_password("admin")
                and not admin_user.must_change_password
            ):
                admin_user.must_change_password = True
                db.session.add(admin_user)
                db.session.commit()
        seed_tipos_peca()
        seed_tamanhos()

    app.register_blueprint(main_bp)
    app.register_blueprint(rfid_bp)
    return app
