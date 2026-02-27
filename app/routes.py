from flask import Blueprint, redirect, render_template, request, url_for

from .models import EnxovalItem, db


main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        codigo = (request.form.get("codigo") or "").strip().upper()
        descricao = (request.form.get("descricao") or "").strip() or None

        if nome and codigo:
            item = EnxovalItem(nome=nome, codigo=codigo, descricao=descricao)
            db.session.add(item)
            db.session.commit()
        return redirect(url_for("main.index"))

    itens = EnxovalItem.query.order_by(EnxovalItem.id.desc()).all()
    return render_template("index.html", itens=itens)


@main_bp.route("/inativar/<int:item_id>", methods=["POST"])
def inativar_item(item_id: int):
    item = db.session.get(EnxovalItem, item_id)
    if item:
        item.ativo = False
        db.session.add(item)
        db.session.commit()
    return redirect(url_for("main.index"))
