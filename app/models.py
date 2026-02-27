from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class EnxovalItem(db.Model):
    __tablename__ = "enxoval_items"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    codigo = db.Column(db.String(64), unique=True, nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<EnxovalItem {self.codigo}>"
