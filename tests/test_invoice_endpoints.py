"""
Integration tests for the invoice endpoints.

Uses FastAPI's TestClient (synchronous) with mocked gateways.
The local JWT auth dependency is overridden via dependency_overrides.
"""
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from app.src.main import app
from app.src.api.deps import get_current_user
from app.src.domain.models.user import User
from app.src.domain.models.invoice import (
    InvoiceResponse, DownloadResponse, InvoiceDataResponse,
    DeleteInvoiceResponse, SendEmailResponse, InvoiceEventsResponse,
)
from app.src.domain.exceptions import FactusAPIError
from app.src.infrastructure.gateways.factus_invoice_gateway import FactusInvoiceGateway
from tests.conftest import VALID_INVOICE_PAYLOAD

ADMIN_USER = User(username="admin", email="admin@example.com", full_name="Admin")
FACTUS_TOKEN_HEADER = {"x-factus-token": "fake-factus-token"}


def get_test_client() -> TestClient:
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    return TestClient(app)


class TestCreateInvoice:
    def test_create_invoice_success(self):
        from app.src.api.v1.endpoints.invoices import get_invoice_gateway

        mock_gw = AsyncMock(spec=FactusInvoiceGateway)
        mock_gw.create_invoice = AsyncMock(return_value=InvoiceResponse(
            number="SETT-1",
            prefix="SETT",
            cufe="abc123cufe",
            qr_url="https://qr.example.com",
            status="1",
            message="Factura validada",
        ))

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_invoice_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.post(
            "/api/v1/invoices/",
            json=VALID_INVOICE_PAYLOAD,
            headers=FACTUS_TOKEN_HEADER,
        )

        app.dependency_overrides.clear()
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["number"] == "SETT-1"
        assert body["data"]["cufe"] == "abc123cufe"

    def test_create_invoice_propagates_factus_status_code(self):
        from app.src.api.v1.endpoints.invoices import get_invoice_gateway

        mock_gw = AsyncMock(spec=FactusInvoiceGateway)
        mock_gw.create_invoice = AsyncMock(
            side_effect=FactusAPIError("Factura duplicada", status_code=409)
        )

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_invoice_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.post(
            "/api/v1/invoices/",
            json=VALID_INVOICE_PAYLOAD,
            headers=FACTUS_TOKEN_HEADER,
        )

        app.dependency_overrides.clear()
        assert response.status_code == 409

    def test_create_invoice_requires_local_jwt(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post(
            "/api/v1/invoices/",
            json=VALID_INVOICE_PAYLOAD,
            headers=FACTUS_TOKEN_HEADER,
        )
        assert response.status_code == 401

    def test_create_invoice_requires_factus_token_header(self):
        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        client = TestClient(app)
        response = client.post("/api/v1/invoices/", json=VALID_INVOICE_PAYLOAD)
        app.dependency_overrides.clear()
        assert response.status_code == 422

    def test_create_invoice_stringified_json_error(self):
        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        client = TestClient(app)
        
        stringified_payload = '{"document": "01", "customer": {"identification_document_id": 3, "identification": "123"}, "items": [{"code_reference": "ref", "name": "item"}]}'
        
        response = client.post(
            "/api/v1/invoices/",
            json=stringified_payload,
            headers={"x-factus-token": "fake-factus-token"},
        )
        app.dependency_overrides.clear()
        
        assert response.status_code == 422
        body = response.json()
        assert "cadena (string)" in body.get("detail", "")


class TestGetInvoice:
    def test_get_invoice_success(self):
        from app.src.api.v1.endpoints.invoices import get_invoice_gateway

        mock_gw = AsyncMock(spec=FactusInvoiceGateway)
        mock_gw.get_invoice = AsyncMock(return_value=InvoiceDataResponse(
            status="success",
            message="OK",
            data={}
        ))

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_invoice_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get("/api/v1/invoices/SETT-1", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        assert response.status_code == 200

    def test_get_invoice_not_found_propagates_404(self):
        from app.src.api.v1.endpoints.invoices import get_invoice_gateway

        mock_gw = AsyncMock(spec=FactusInvoiceGateway)
        mock_gw.get_invoice = AsyncMock(
            side_effect=FactusAPIError("No encontrada", status_code=404)
        )

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_invoice_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get("/api/v1/invoices/SETT-999", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        assert response.status_code == 404


class TestDownloadInvoice:
    def test_download_pdf_success(self):
        from app.src.api.v1.endpoints.invoices import get_invoice_gateway

        mock_gw = AsyncMock(spec=FactusInvoiceGateway)
        mock_gw.download_pdf = AsyncMock(return_value=DownloadResponse(
            file_name="SETT-1.pdf",
            file_content="base64content",
            extension="pdf",
        ))

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_invoice_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get("/api/v1/invoices/SETT-1/pdf", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        assert response.status_code == 200
        assert response.json()["data"]["extension"] == "pdf"

    def test_download_xml_success(self):
        from app.src.api.v1.endpoints.invoices import get_invoice_gateway

        mock_gw = AsyncMock(spec=FactusInvoiceGateway)
        mock_gw.download_xml = AsyncMock(return_value=DownloadResponse(
            file_name="SETT-1.xml",
            file_content="base64content",
            extension="xml",
        ))

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_invoice_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get("/api/v1/invoices/SETT-1/xml", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        assert response.status_code == 200
        assert response.json()["data"]["extension"] == "xml"


class TestDeleteInvoice:
    def test_delete_invoice_success(self):
        from app.src.api.v1.endpoints.invoices import get_invoice_gateway

        mock_gw = AsyncMock(spec=FactusInvoiceGateway)
        mock_gw.delete_invoice = AsyncMock(return_value=DeleteInvoiceResponse(
            status="success",
            message="Factura eliminada",
        ))

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_invoice_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.delete(
            "/api/v1/invoices/reference/REF-001",
            headers=FACTUS_TOKEN_HEADER,
        )

        app.dependency_overrides.clear()
        assert response.status_code == 200

    def test_delete_invoice_propagates_factus_error(self):
        from app.src.api.v1.endpoints.invoices import get_invoice_gateway

        mock_gw = AsyncMock(spec=FactusInvoiceGateway)
        mock_gw.delete_invoice = AsyncMock(
            side_effect=FactusAPIError("No se puede eliminar", status_code=422)
        )

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_invoice_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.delete(
            "/api/v1/invoices/reference/REF-001",
            headers=FACTUS_TOKEN_HEADER,
        )

        app.dependency_overrides.clear()
        assert response.status_code == 422


class TestSendEmail:
    def test_send_email_success(self):
        from app.src.api.v1.endpoints.invoices import get_invoice_gateway

        mock_gw = AsyncMock(spec=FactusInvoiceGateway)
        mock_gw.send_email = AsyncMock(return_value=SendEmailResponse(
            status="success",
            message="Correo enviado",
        ))

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_invoice_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.post(
            "/api/v1/invoices/SETT-1/send-email",
            json={"email": "cliente@example.com"},
            headers=FACTUS_TOKEN_HEADER,
        )

        app.dependency_overrides.clear()
        assert response.status_code == 200


class TestGetInvoiceEvents:
    def test_get_events_success(self):
        from app.src.api.v1.endpoints.invoices import get_invoice_gateway

        mock_gw = AsyncMock(spec=FactusInvoiceGateway)
        mock_gw.get_invoice_events = AsyncMock(return_value=InvoiceEventsResponse(
            status="success",
            message="OK",
            data=[],
        ))

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_invoice_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get(
            "/api/v1/invoices/SETT-1/events",
            headers=FACTUS_TOKEN_HEADER,
        )

        app.dependency_overrides.clear()
        assert response.status_code == 200
