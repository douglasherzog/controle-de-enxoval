from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy


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
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

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
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    item = db.relationship("EnxovalItem", back_populates="movimentacoes")


class Setor(db.Model):
    __tablename__ = "setores"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), unique=True, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Setor {self.nome}>"


class TipoPeca(db.Model):
    __tablename__ = "tipos_peca"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), unique=True, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<TipoPeca {self.nome}>"


class Colaborador(db.Model):
    __tablename__ = "colaboradores"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), unique=True, nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Colaborador {self.nome}>"
