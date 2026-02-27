"""Smoke tests automatizados para o Controle de Enxoval.

Estes testes verificam rapidamente se as principais funcionalidades
estão operacionais. Devem ser executados frequentemente.
"""

import unittest
from datetime import datetime

from app import create_app
from app.models import Colaborador, EnxovalItem, Setor, TipoPeca, db


class SmokeTests(unittest.TestCase):
    """Testes rápidos de verificação básica do sistema."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Limpa o ambiente após os testes."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_servidor_responde(self):
        """Verifica se o servidor está respondendo."""
        response = self.client.get("/")
        self.assertIn(response.status_code, [200, 302])

    def test_pagina_principal_carrega(self):
        """Verifica se a página principal carrega corretamente."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        # Verifica elementos essenciais
        self.assertIn(b"Controle de Enxoval", response.data)
        self.assertIn(b"Dashboard", response.data)

    def test_cadastro_basico_item(self):
        """Testa o cadastro básico de uma peça."""
        response = self.client.post(
            "/",
            data={
                "nome": "Camisa Teste",
                "codigo": "CAM-001",
                "tamanho": "M",
                "status": "estoque",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            item = EnxovalItem.query.filter_by(codigo="CAM-001").first()
            self.assertIsNotNone(item)
            self.assertEqual(item.nome, "Camisa Teste")
            self.assertEqual(item.tamanho, "M")

    def test_movimentacao_item(self):
        """Testa a movimentação de uma peça."""
        # Primeiro cadastra uma peça
        with self.app.app_context():
            item = EnxovalItem(
                nome="Calça Teste",
                codigo="CAL-001",
                tamanho="G",
                status="estoque",
            )
            db.session.add(item)
            db.session.commit()
            item_id = item.id

        # Movimenta a peça
        response = self.client.post(
            f"/movimentar/{item_id}",
            data={
                "status": "em_uso",
                "colaborador": "João Silva",
                "setor": "Produção",
                "observacao": "Entrega ao colaborador",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            item = db.session.get(EnxovalItem, item_id)
            self.assertEqual(item.status, "em_uso")
            self.assertEqual(item.colaborador, "João Silva")

    def test_importacao_csv(self):
        """Testa a importação de CSV."""
        csv_data = """nome,codigo,tamanho,status
Camisa A,CAM-A,M,estoque
Camisa B,CAM-B,G,estoque"""

        response = self.client.post(
            "/importar",
            data={"arquivo": (io.BytesIO(csv_data.encode()), "test.csv")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_api_rfid_status(self):
        """Testa o endpoint de status da API RFID."""
        response = self.client.get("/api/rfid/status")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "online")
        self.assertIn("estatisticas", data)

    def test_api_rfid_scan(self):
        """Testa o endpoint de scan RFID."""
        # Cadastra peça com RFID
        with self.app.app_context():
            item = EnxovalItem(
                nome="Jaleco RFID",
                codigo="JAL-RFID-001",
                tamanho="M",
                status="estoque",
                tag_rfid="RFID-TEST-001",
            )
            db.session.add(item)
            db.session.commit()

        # Testa scan
        response = self.client.post(
            "/api/rfid/scan",
            json={
                "tag_rfid": "RFID-TEST-001",
                "status": "em_uso",
                "colaborador": "Maria Silva",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["sucesso"])

    def test_qrcode_geracao(self):
        """Testa a geração de QR code."""
        with self.app.app_context():
            item = EnxovalItem(
                nome="Peça QR",
                codigo="QR-001",
                tamanho="P",
                status="estoque",
            )
            db.session.add(item)
            db.session.commit()
            item_id = item.id

        response = self.client.get(f"/qrcode/{item_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "image/png")

    def test_relatorios_disponiveis(self):
        """Testa se os relatórios estão disponíveis."""
        for periodo in ["diario", "semanal", "mensal"]:
            response = self.client.get(f"/relatorio/{periodo}")
            self.assertEqual(response.status_code, 200)

    def test_exportacao_pdf(self):
        """Testa a exportação de PDF."""
        response = self.client.get("/relatorio/diario/pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/pdf")

    def test_exportacao_excel(self):
        """Testa a exportação de Excel."""
        response = self.client.get("/relatorio/diario/excel")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "spreadsheetml.sheet",
            response.content_type,
        )

    def test_cadastro_setor(self):
        """Testa o cadastro de setor."""
        response = self.client.post(
            "/setores",
            data={"nome": "Setor Teste"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            setor = Setor.query.filter_by(nome="Setor Teste").first()
            self.assertIsNotNone(setor)

    def test_cadastro_tipo_peca(self):
        """Testa o cadastro de tipo de peça."""
        response = self.client.post(
            "/tipos-peca",
            data={"nome": "Novo Tipo Teste"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            tipo = TipoPeca.query.filter_by(nome="Novo Tipo Teste").first()
            self.assertIsNotNone(tipo)

    def test_cadastro_colaborador(self):
        """Testa o cadastro de colaborador."""
        response = self.client.post(
            "/colaboradores",
            data={"nome": "Novo Colaborador", "telefone": "(51) 99999-9999"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            colab = Colaborador.query.filter_by(nome="Novo Colaborador").first()
            self.assertIsNotNone(colab)
            self.assertEqual(colab.telefone, "(51) 99999-9999")


class SmokeTestSuite:
    """Suite de smoke tests para execução automatizada."""

    @staticmethod
    def run_all():
        """Executa todos os smoke tests."""
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(SmokeTests)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()


if __name__ == "__main__":
    import io
    import sys

    # Configura saída
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=" * 60)
    print("SMOKE TESTS - Controle de Enxoval")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    success = SmokeTestSuite.run_all()

    print("-" * 60)
    if success:
        print("✅ TODOS OS SMOKE TESTS PASSARAM")
        sys.exit(0)
    else:
        print("❌ ALGUNS SMOKE TESTS FALHARAM")
        sys.exit(1)
