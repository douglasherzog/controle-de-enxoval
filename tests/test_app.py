import io
import unittest
from datetime import UTC, datetime, timedelta

from app import create_app
from app.models import EnxovalItem, Movimentacao, db


class EnxovalAppTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            }
        )
        self.client = self.app.test_client()

    def test_cadastro_e_movimentacao(self) -> None:
        with self.app.app_context():
            resposta = self.client.post(
                "/",
                data={
                    "nome": "Moletom",
                    "codigo": "MO-0001",
                    "tamanho": "M",
                    "descricao": "Teste",
                },
                follow_redirects=True,
            )
            self.assertEqual(resposta.status_code, 200)
            item = EnxovalItem.query.filter_by(codigo="MO-0001").first()
            self.assertIsNotNone(item)

            resposta = self.client.post(
                f"/movimentar/{item.id}",
                data={
                    "status": "entregue",
                    "colaborador": "Joao",
                    "setor": "Desossa",
                    "observacao": "Entrega",
                },
                follow_redirects=True,
            )
            self.assertEqual(resposta.status_code, 200)
            item_atualizado = db.session.get(EnxovalItem, item.id)
            self.assertEqual(item_atualizado.status, "entregue")

            historico = Movimentacao.query.filter_by(item_id=item.id).all()
            self.assertGreaterEqual(len(historico), 2)

    def test_importacao_csv(self) -> None:
        csv_content = (
            "nome,codigo,tag_rfid,tamanho,tamanho_customizado,descricao,colaborador,setor,status,observacao\n"
            "Calca NR10,CN-0001,,G,,Calca,,Corte,estoque,Importacao\n"
        )
        data = {
            "arquivo": (io.BytesIO(csv_content.encode("utf-8")), "import.csv"),
        }
        with self.app.app_context():
            resposta = self.client.post("/importar", data=data, content_type="multipart/form-data")
            self.assertEqual(resposta.status_code, 302)
            item = EnxovalItem.query.filter_by(codigo="CN-0001").first()
            self.assertIsNotNone(item)

    def test_alertas_por_dias(self) -> None:
        agora = datetime.now(UTC)
        with self.app.app_context():
            item_atencao = EnxovalItem(
                nome="Bata",
                codigo="BA-0001",
                tamanho="M",
                status="entregue",
            )
            item_critico = EnxovalItem(
                nome="Calca",
                codigo="CA-0001",
                tamanho="G",
                status="em_uso",
            )
            db.session.add_all([item_atencao, item_critico])
            db.session.flush()
            db.session.add_all(
                [
                    Movimentacao(
                        item=item_atencao,
                        status="entregue",
                        created_at=agora - timedelta(days=3),
                    ),
                    Movimentacao(
                        item=item_critico,
                        status="em_uso",
                        created_at=agora - timedelta(days=5),
                    ),
                ]
            )
            db.session.commit()

            resposta = self.client.get("/")
            self.assertEqual(resposta.status_code, 200)


if __name__ == "__main__":
    unittest.main()
