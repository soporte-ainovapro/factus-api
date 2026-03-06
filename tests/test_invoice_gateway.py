"""
Unit tests for FactusInvoiceGateway.

All HTTP calls are mocked — no real network requests.
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.src.infrastructure.gateways.factus_invoice_gateway import FactusInvoiceGateway
from app.src.domain.models.invoice import (
    Invoice, Customer, InvoiceItem,
    SendEmailRequest, InvoiceEventsResponse,
)

BASE_URL = "https://api-sandbox.factus.com.co"
TOKEN = "fake-factus-token"


def make_gateway() -> FactusInvoiceGateway:
    return FactusInvoiceGateway(base_url=BASE_URL)


def mock_response(status_code: int, json_body: dict) -> MagicMock:
    r = MagicMock()
    r.status_code = status_code
    r.is_success = 200 <= status_code < 300
    r.json.return_value = json_body
    r.text = str(json_body)
    return r


def make_invoice(**overrides) -> Invoice:
    """Build a minimal valid Invoice domain object."""
    defaults = dict(
        reference_code="REF-001",
        customer=Customer(
            identification_document_id=3,
            identification="900123456",
            legal_organization_id=1,
            tribute_id=21,
            names="Test User",
        ),
        items=[
            InvoiceItem(
                code_reference="ITEM-001",
                name="Producto",
                quantity=2,
                price=Decimal("5000.00"),
                discount_rate=Decimal("0.00"),
                tax_rate=Decimal("19.00"),
                unit_measure_id=70,
                standard_code_id=1,
                is_excluded=0,
                tribute_id=21,
            )
        ],
        payment_form="1",
        payment_method_code="10",
    )
    defaults.update(overrides)
    return Invoice(**defaults)


# ---------------------------------------------------------------------------
# create_invoice()
# ---------------------------------------------------------------------------

class TestCreateInvoice:
    @pytest.mark.asyncio
    async def test_returns_invoice_response_on_success(self):
        gateway = make_gateway()
        api_resp = {
            "message": "Factura creada",
            "data": {
                "bill": {
                    "number": "SETT-1",
                    "cufe": "abc-cufe",
                    "qr": "https://qr.example.com",
                    "status": "1",
                },
                "numbering_range": {"prefix": "SETT"},
            },
        }
        fake_resp = mock_response(200, api_resp)

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        invoice = make_invoice()
        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            result = await gateway.create_invoice(invoice, TOKEN)

        assert result.number == "SETT-1"
        assert result.prefix == "SETT"
        assert result.cufe == "abc-cufe"
        assert result.status == "1"

    @pytest.mark.asyncio
    async def test_sends_bearer_token_in_header(self):
        gateway = make_gateway()
        api_resp = {
            "message": "ok",
            "data": {
                "bill": {"number": "X1", "cufe": "", "qr": "", "status": "1"},
                "numbering_range": {"prefix": "X"},
            },
        }
        fake_resp = mock_response(200, api_resp)

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        invoice = make_invoice()
        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            await gateway.create_invoice(invoice, TOKEN)

        headers = mock_client.post.call_args.kwargs["headers"]
        assert headers["Authorization"] == f"Bearer {TOKEN}"

    @pytest.mark.asyncio
    async def test_raises_422_with_field_errors(self):
        """422 errors show the per-field messages, not '{}' or a raw dict."""
        gateway = make_gateway()
        fake_resp = mock_response(422, {
            "message": "El campo código de referencia es obligatorio. (and 1 more error)",
            "errors": {
                "reference_code": ["El campo código de referencia es obligatorio."],
                "items.0.quantity": ["El campo items.0.quantity es obligatorio."],
            }
        })

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        invoice = make_invoice()
        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            with pytest.raises(Exception) as exc_info:
                await gateway.create_invoice(invoice, TOKEN)

        error_msg = str(exc_info.value)
        assert "reference_code" in error_msg
        assert "El campo código de referencia es obligatorio." in error_msg

    @pytest.mark.asyncio
    async def test_raises_409_with_conflict_message(self):
        """409 errors use the list-of-objects shape."""
        gateway = make_gateway()
        fake_resp = mock_response(409, {
            "status": "Conflict",
            "errors": [{"code": 409, "message": "Se encontró una factura pendiente por enviar a la DIAN"}]
        })

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        invoice = make_invoice()
        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            with pytest.raises(Exception, match="Se encontró una factura pendiente"):
                await gateway.create_invoice(invoice, TOKEN)

    def test_invoice_rejects_credit_without_due_date(self):
        """Invoice model enforces payment_due_date when payment_form is '2' (crédito)."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="payment_due_date"):
            Invoice(
                reference_code="REF-001",
                payment_form="2",
                payment_method_code="10",
                customer=Customer(
                    identification_document_id=3,
                    identification="900123456",
                    legal_organization_id=1,
                    tribute_id=21,
                    names="Test",
                ),
                items=[
                    InvoiceItem(
                        code_reference="I1",
                        name="P",
                        quantity=1,
                        price="1000.00",
                        discount_rate="0.00",
                        tax_rate="19.00",
                        unit_measure_id=70,
                        standard_code_id=1,
                        is_excluded=0,
                        tribute_id=1,
                    )
                ],
            )


# ---------------------------------------------------------------------------
# _download() / download_pdf() / download_xml()
# ---------------------------------------------------------------------------

class TestDownload:
    @pytest.mark.asyncio
    async def test_download_pdf_extracts_pdf_field(self):
        gateway = make_gateway()
        fake_resp = mock_response(200, {
            "data": {
                "file_name": "factura.pdf",
                "pdf_base_64_encoded": "base64pdfcontent==",
            }
        })

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            result = await gateway.download_pdf("SETT-1", TOKEN)

        assert result.extension == "pdf"
        assert result.file_content == "base64pdfcontent=="
        assert result.file_name == "factura.pdf"

    @pytest.mark.asyncio
    async def test_download_xml_extracts_xml_field(self):
        gateway = make_gateway()
        fake_resp = mock_response(200, {
            "data": {
                "file_name": "factura.xml",
                "xml_base_64_encoded": "base64xmlcontent==",
            }
        })

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            result = await gateway.download_xml("SETT-1", TOKEN)

        assert result.extension == "xml"
        assert result.file_content == "base64xmlcontent=="

    @pytest.mark.asyncio
    async def test_download_raises_on_not_found(self):
        gateway = make_gateway()
        fake_resp = mock_response(404, {"message": "Factura no encontrada"})

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            with pytest.raises(Exception, match="Factura no encontrada"):
                await gateway.download_pdf("NONEXISTENT", TOKEN)

    @pytest.mark.asyncio
    async def test_download_uses_fallback_filename(self):
        """If file_name is absent, the fallback is {number}.{extension}."""
        gateway = make_gateway()
        fake_resp = mock_response(200, {
            "data": {"pdf_base_64_encoded": "data=="}
        })

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            result = await gateway.download_pdf("SETT-99", TOKEN)

        assert result.file_name == "SETT-99.pdf"


# ---------------------------------------------------------------------------
# get_invoice()
# ---------------------------------------------------------------------------

class TestGetInvoice:
    @pytest.mark.asyncio
    async def test_returns_invoice_data_response(self):
        gateway = make_gateway()
        api_resp = {
            "status": "200",
            "message": "ok",
            "data": {"bill": {"number": "SETT-1", "cufe": "abc"}},
        }
        fake_resp = mock_response(200, api_resp)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            result = await gateway.get_invoice("SETT-1", TOKEN)

        assert result.status == "200"
        assert result.data["bill"]["number"] == "SETT-1"

    @pytest.mark.asyncio
    async def test_raises_when_invoice_not_found(self):
        gateway = make_gateway()
        fake_resp = mock_response(404, {"message": "Not found"})

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            with pytest.raises(Exception, match="Not found"):
                await gateway.get_invoice("NONEXISTENT", TOKEN)


# ---------------------------------------------------------------------------
# delete_invoice()
# ---------------------------------------------------------------------------

class TestDeleteInvoice:
    @pytest.mark.asyncio
    async def test_returns_delete_response(self):
        gateway = make_gateway()
        fake_resp = mock_response(200, {"status": "200", "message": "Factura eliminada"})

        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            result = await gateway.delete_invoice("REF-001", TOKEN)

        assert result.status == "200"
        assert "eliminada" in result.message

    @pytest.mark.asyncio
    async def test_raises_on_delete_error(self):
        gateway = make_gateway()
        fake_resp = mock_response(400, {"message": "No se puede eliminar"})

        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            with pytest.raises(Exception, match="No se puede eliminar"):
                await gateway.delete_invoice("REF-001", TOKEN)


# ---------------------------------------------------------------------------
# send_email()
# ---------------------------------------------------------------------------

class TestSendEmail:
    @pytest.mark.asyncio
    async def test_sends_email_successfully(self):
        gateway = make_gateway()
        fake_resp = mock_response(200, {"status": "200", "message": "Email enviado"})

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        email_req = SendEmailRequest(email="client@example.com")
        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            result = await gateway.send_email("SETT-1", email_req, TOKEN)

        assert result.message == "Email enviado"

    @pytest.mark.asyncio
    async def test_includes_pdf_when_provided(self):
        gateway = make_gateway()
        fake_resp = mock_response(200, {"status": "200", "message": "ok"})

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        email_req = SendEmailRequest(email="x@example.com", pdf_base_64_encoded="pdfdata==")
        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            await gateway.send_email("SETT-1", email_req, TOKEN)

        sent_json = mock_client.post.call_args.kwargs["json"]
        assert sent_json["pdf_base_64_encoded"] == "pdfdata=="

    @pytest.mark.asyncio
    async def test_omits_pdf_when_not_provided(self):
        gateway = make_gateway()
        fake_resp = mock_response(200, {"status": "200", "message": "ok"})

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        email_req = SendEmailRequest(email="x@example.com")
        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            await gateway.send_email("SETT-1", email_req, TOKEN)

        sent_json = mock_client.post.call_args.kwargs["json"]
        assert "pdf_base_64_encoded" not in sent_json


# ---------------------------------------------------------------------------
# get_invoice_events()
# ---------------------------------------------------------------------------

class TestGetInvoiceEvents:
    @pytest.mark.asyncio
    async def test_returns_events_response(self):
        gateway = make_gateway()
        api_resp = {
            "status": "200",
            "message": "ok",
            "data": [
                {
                    "number": "SETT-1",
                    "cude": "cude-abc",
                    "event_code": "030",
                    "event_name": "Acuse de recibo",
                    "effective_date": "2024-01-15",
                    "effective_time": "10:00:00",
                }
            ],
        }
        fake_resp = mock_response(200, api_resp)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            result = await gateway.get_invoice_events("SETT-1", TOKEN)

        assert isinstance(result, InvoiceEventsResponse)
        assert len(result.data) == 1
        assert result.data[0].event_code == "030"

    @pytest.mark.asyncio
    async def test_raises_on_events_error(self):
        gateway = make_gateway()
        fake_resp = mock_response(404, {"message": "Factura no encontrada"})

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            with pytest.raises(Exception, match="Factura no encontrada"):
                await gateway.get_invoice_events("NONEXISTENT", TOKEN)
