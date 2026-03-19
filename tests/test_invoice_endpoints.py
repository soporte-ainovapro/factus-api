"""
Integration tests for the invoice endpoints.

Uses FastAPI's TestClient (synchronous) with mocked gateways.
The API Key auth dependency is overridden via dependency_overrides.
"""
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import verify_api_key, get_invoice_service
from app.schemas.results import (
    InvoiceResult, DownloadResult, InvoiceDataResult,
    DeleteInvoiceResult, InvoiceEventsResult,
)
from app.core.exceptions import FactusAPIError
from app.services.factus_invoice_service import FactusInvoiceService
from tests.conftest import VALID_INVOICE_PAYLOAD

FACTUS_TOKEN_HEADER = {"x-factus-token": "fake-factus-token"}


class TestCreateInvoice:
    def test_create_invoice_success(self):
        mock_gw = AsyncMock(spec=FactusInvoiceService)
        mock_gw.create_invoice = AsyncMock(return_value=InvoiceResult(
            number="SETT-1",
            prefix="SETT",
            cufe="abc123cufe",
            qr_url="https://qr.example.com",
            status="1",
            message="Factura validada",
        ))

        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        app.dependency_overrides[get_invoice_service] = lambda: mock_gw

        client = TestClient(app)
        response = client.post(
            "/api/invoices/",
            json=VALID_INVOICE_PAYLOAD,
            headers=FACTUS_TOKEN_HEADER,
        )

        app.dependency_overrides.clear()
        assert response.status_code == 200
        body = response.json()
        assert body["number"] == "SETT-1"
        assert body["cufe"] == "abc123cufe"

    def test_create_invoice_propagates_factus_status_code(self):
        mock_gw = AsyncMock(spec=FactusInvoiceService)
        mock_gw.create_invoice = AsyncMock(
            side_effect=FactusAPIError("Factura duplicada", status_code=409)
        )

        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        app.dependency_overrides[get_invoice_service] = lambda: mock_gw

        client = TestClient(app)
        response = client.post(
            "/api/invoices/",
            json=VALID_INVOICE_PAYLOAD,
            headers=FACTUS_TOKEN_HEADER,
        )

        app.dependency_overrides.clear()
        assert response.status_code == 409

    def test_create_invoice_requires_api_key(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post(
            "/api/invoices/",
            json=VALID_INVOICE_PAYLOAD,
            headers=FACTUS_TOKEN_HEADER,
        )
        assert response.status_code in (401, 403)


    def test_create_invoice_requires_factus_token_header(self):
        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        client = TestClient(app)
        response = client.post("/api/invoices/", json=VALID_INVOICE_PAYLOAD)
        app.dependency_overrides.clear()
        assert response.status_code == 422

    def test_create_invoice_stringified_json_error(self):
        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        client = TestClient(app)

        stringified_payload = '{"numbering_range_prefix": "SETT", "customer": {"document_type": "CC"}, "items": []}'

        response = client.post(
            "/api/invoices/",
            json=stringified_payload,
            headers={"x-factus-token": "fake-factus-token"},
        )
        app.dependency_overrides.clear()

        assert response.status_code == 422
        body = response.json()
        assert "cadena (string)" in body.get("detail", "")


class TestGetInvoice:
    def test_get_invoice_success(self):
        mock_gw = AsyncMock(spec=FactusInvoiceService)
        mock_gw.get_invoice = AsyncMock(return_value=InvoiceDataResult(
            status="success",
            message="OK",
            data={}
        ))

        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        app.dependency_overrides[get_invoice_service] = lambda: mock_gw

        client = TestClient(app)
        response = client.get("/api/invoices/SETT-1", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        assert response.status_code == 200

    def test_get_invoice_not_found_propagates_404(self):
        mock_gw = AsyncMock(spec=FactusInvoiceService)
        mock_gw.get_invoice = AsyncMock(
            side_effect=FactusAPIError("No encontrada", status_code=404)
        )

        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        app.dependency_overrides[get_invoice_service] = lambda: mock_gw

        client = TestClient(app)
        response = client.get("/api/invoices/SETT-999", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        assert response.status_code == 404


class TestDownloadInvoice:
    def test_download_pdf_success(self):
        mock_gw = AsyncMock(spec=FactusInvoiceService)
        mock_gw.download_pdf = AsyncMock(return_value=DownloadResult(
            file_name="SETT-1.pdf",
            file_content="base64content",
            extension="pdf",
        ))

        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        app.dependency_overrides[get_invoice_service] = lambda: mock_gw

        client = TestClient(app)
        response = client.get("/api/invoices/SETT-1/pdf", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        assert response.status_code == 200
        assert response.json()["extension"] == "pdf"

    def test_download_xml_success(self):
        mock_gw = AsyncMock(spec=FactusInvoiceService)
        mock_gw.download_xml = AsyncMock(return_value=DownloadResult(
            file_name="SETT-1.xml",
            file_content="base64content",
            extension="xml",
        ))

        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        app.dependency_overrides[get_invoice_service] = lambda: mock_gw

        client = TestClient(app)
        response = client.get("/api/invoices/SETT-1/xml", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        assert response.status_code == 200
        assert response.json()["extension"] == "xml"


class TestDeleteInvoice:
    def test_delete_invoice_success(self):
        mock_gw = AsyncMock(spec=FactusInvoiceService)
        mock_gw.delete_invoice = AsyncMock(return_value=DeleteInvoiceResult(
            status="success",
            message="Factura eliminada",
        ))

        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        app.dependency_overrides[get_invoice_service] = lambda: mock_gw

        client = TestClient(app)
        response = client.delete(
            "/api/invoices/reference/REF-001",
            headers=FACTUS_TOKEN_HEADER,
        )

        app.dependency_overrides.clear()
        assert response.status_code == 200

    def test_delete_invoice_propagates_factus_error(self):
        mock_gw = AsyncMock(spec=FactusInvoiceService)
        mock_gw.delete_invoice = AsyncMock(
            side_effect=FactusAPIError("No se puede eliminar", status_code=422)
        )

        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        app.dependency_overrides[get_invoice_service] = lambda: mock_gw

        client = TestClient(app)
        response = client.delete(
            "/api/invoices/reference/REF-001",
            headers=FACTUS_TOKEN_HEADER,
        )

        app.dependency_overrides.clear()
        assert response.status_code == 422


class TestSendEmail:
    def test_send_email_success(self):
        mock_gw = AsyncMock(spec=FactusInvoiceService)
        mock_gw.send_email = AsyncMock(return_value=None)

        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        app.dependency_overrides[get_invoice_service] = lambda: mock_gw

        client = TestClient(app)
        response = client.post(
            "/api/invoices/SETT-1/send-email",
            json={"email": "cliente@example.com"},
            headers=FACTUS_TOKEN_HEADER,
        )

        app.dependency_overrides.clear()
        assert response.status_code == 200


class TestGetInvoiceEvents:
    def test_get_events_success(self):
        mock_gw = AsyncMock(spec=FactusInvoiceService)
        mock_gw.get_invoice_events = AsyncMock(return_value=InvoiceEventsResult(
            status="success",
            message="OK",
            data=[],
        ))

        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        app.dependency_overrides[get_invoice_service] = lambda: mock_gw

        client = TestClient(app)
        response = client.get(
            "/api/invoices/SETT-1/events",
            headers=FACTUS_TOKEN_HEADER,
        )

        app.dependency_overrides.clear()
        assert response.status_code == 200
