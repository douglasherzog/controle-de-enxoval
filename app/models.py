from datetime import UTC, datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class EnxovalItem(db.Model):
    __tablename__ = "enxoval_items"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    codigo = db.Column(db.String(64), unique=True, nullable=False)
    tag_rfid = db.Column(db.String(64), unique=True, nullable=True)
    tamanho = db.Column(db.String(20), nullable=False)
    tamanho_customizado = db.Column(db.Text, nullable=True)
    descricao = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=False, default="estoque")
    colaborador = db.Column(db.String(120), nullable=True)
    setor = db.Column(db.String(120), nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    movimentacoes = db.relationship(
        "Movimentacao",
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="Movimentacao.created_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<EnxovalItem {self.codigo}>"


class Movimentacao(db.Model):
    __tablename__ = "movimentacoes"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("enxoval_items.id"), nullable=False)
    status = db.Column(db.String(32), nullable=False)
    colaborador = db.Column(db.String(120), nullable=True)
    setor = db.Column(db.String(120), nullable=True)
    observacao = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    item = db.relationship("EnxovalItem", back_populates="movimentacoes")


class Configuracao(db.Model):
    __tablename__ = "configuracoes"

    id = db.Column(db.Integer, primary_key=True)
    periodicidade_revisao_dias = db.Column(db.Integer, default=7, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))


class Revisao(db.Model):
    __tablename__ = "revisoes"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("enxoval_items.id"), nullable=False)
    conferente = db.Column(db.String(120), nullable=False)
    setor = db.Column(db.String(120), nullable=True)
    colaborador = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    item = db.relationship("EnxovalItem")


class Setor(db.Model):
    __tablename__ = "setores"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), unique=True, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        return f"<Setor {self.nome}>"


class TipoPeca(db.Model):
    __tablename__ = "tipos_peca"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), unique=True, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        return f"<TipoPeca {self.nome}>"


class Colaborador(db.Model):
    __tablename__ = "colaboradores"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), unique=True, nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        return f"<Colaborador {self.nome}>"


class Tamanho(db.Model):
    __tablename__ = "tamanhos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), unique=True, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        return f"<Tamanho {self.nome}>"


class User(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    must_change_password = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
