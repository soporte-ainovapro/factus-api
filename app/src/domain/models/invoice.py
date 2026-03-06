from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import List, Optional
from datetime import date
from decimal import Decimal
from typing import Any, Dict

class WithholdingTax(BaseModel):
    code: str
    withholding_tax_rate: Decimal

class Mandate(BaseModel):
    identification_document_id: int
    identification: str

class InvoiceItem(BaseModel):
    code_reference: str
    name: str

    quantity: int = Field(gt=0)

    price: Decimal = Field(gt=0)
    discount_rate: Decimal = Field(default=Decimal("0.00"), ge=0)

    tax_rate: Decimal = Field(ge=0)
    unit_measure_id: int
    standard_code_id: int

    # Factus espera 0 o 1
    is_excluded: int = Field(ge=0, le=1)

    tribute_id: int

    # Campos avanzados (Opcionales)
    scheme_id: Optional[str] = None
    note: Optional[str] = None
    withholding_taxes: Optional[List[WithholdingTax]] = None
    mandate: Optional[Mandate] = None

    @model_validator(mode="after")
    def validate_decimals(self):
        for field in ["price", "discount_rate", "tax_rate"]:
            value = getattr(self, field)
            if value.as_tuple().exponent < -2:
                raise ValueError(f"{field} must have max 2 decimal places")
        return self

class Customer(BaseModel):
    identification_document_id: int
    identification: str

    dv: Optional[str] = None
    company: Optional[str] = None
    trade_name: Optional[str] = None
    names: Optional[str] = None

    address: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    municipality_id: Optional[int] = None
    legal_organization_id: int
    tribute_id: int

    @model_validator(mode="after")
    def validate_customer(self):
        # Si es empresa (persona jurídica)
        if self.company is not None:
            if not self.company.strip():
                raise ValueError("Company name cannot be empty")
        else:
            if not self.names:
                raise ValueError("Names is required for natural persons")

        # Si el documento es NIT (normalmente id 6, ajústalo según tu catálogo)
        if self.identification_document_id == 6 and not self.dv:
            raise ValueError("DV is required for NIT")

        return self

class OrderReference(BaseModel):
    reference_code: str
    issue_date: Optional[date] = None

class RelatedDocument(BaseModel):
    code: str
    issue_date: date
    number: str

class BillingPeriod(BaseModel):
    start_date: date
    start_time: Optional[str] = None
    end_date: date
    end_time: str

class Establishment(BaseModel):
    name: str
    address: str
    phone_number: str
    email: str
    municipality_id: int

class AllowanceCharge(BaseModel):
    concept_type: str
    is_surcharge: bool
    reason: str
    base_amount: Decimal
    amount: Decimal

class Invoice(BaseModel):
    numbering_range_id: Optional[int] = None
    document: str = Field(default="01")  # 01 Factura venta

    reference_code: str
    observation: Optional[str] = Field(default=None, max_length=250)

    # Pago — campos de primer nivel tal como espera Factus
    payment_method_code: str = Field(default="10", description="Código del método de pago. Default: 10 (efectivo)")
    payment_form: str = Field(default="1", description="1: Contado, 2: Crédito")
    payment_due_date: Optional[date] = None

    # Campos opcionales para factura avanzada
    operation_type: Optional[str] = None
    send_email: Optional[bool] = None
    order_reference: Optional[OrderReference] = None
    related_documents: Optional[List[RelatedDocument]] = None
    billing_period: Optional[BillingPeriod] = None
    establishment: Optional[Establishment] = None
    allowance_charges: Optional[List[AllowanceCharge]] = None

    customer: Customer
    items: List[InvoiceItem]

    @model_validator(mode="after")
    def validate_invoice(self):
        if not self.items:
            raise ValueError("Invoice must contain at least one item")
        if self.payment_form == "2" and not self.payment_due_date:
            raise ValueError("payment_due_date es obligatorio cuando payment_form es 2 (crédito)")
        return self

class InvoiceResponse(BaseModel):
    number: str
    prefix: str
    cufe: str
    qr_url: str
    status: str
    message: Optional[str] = None

class DownloadResponse(BaseModel):
    file_name: str
    file_content: str  # Base64
    extension: str

class InvoiceDataResponse(BaseModel):
    """
    Represents the full data of an invoice retrieved from Factus API.
    It can contain 'company', 'customer', 'bill', 'items', etc.
    """
    status: str
    message: Optional[str] = None
    data: Dict[str, Any]

class DeleteInvoiceResponse(BaseModel):
    status: str
    message: str

class SendEmailRequest(BaseModel):
    email: EmailStr
    pdf_base_64_encoded: Optional[str] = None

class SendEmailResponse(BaseModel):
    status: str
    message: str

class InvoiceEvent(BaseModel):
    number: str
    cude: str
    event_code: str
    event_name: str
    effective_date: str
    effective_time: str

class InvoiceEventsResponse(BaseModel):
    status: str
    message: Optional[str] = None
    data: List[InvoiceEvent]
