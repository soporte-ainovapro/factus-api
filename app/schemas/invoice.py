from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import List, Optional
from datetime import date

from app.schemas.customer import Customer
from app.schemas.establishment import Establishment
from app.schemas.item import Item
from app.schemas.shared import (
    OrderReference,
    RelatedDocument,
    BillingPeriod,
    AllowanceCharge,
)
from app.schemas.enums import DocumentType, PaymentForm


class Invoice(BaseModel):
    """
    Documento de factura electrónica en términos del dominio del negocio.
    Usa valores canónicos (Enums y códigos de texto) independientes del proveedor.
    El adaptador de cada proveedor traduce estos valores al formato que su API requiere.
    """

    # Rango de numeración identificado por su prefijo (ej "SETT", "FE")
    # El adaptador de Factus lo resolverá al numbering_range_id entero internamente.
    numbering_range_prefix: str

    document_type: DocumentType = DocumentType.INVOICE
    reference_code: str
    observation: Optional[str] = Field(default=None, max_length=250)

    # Pago
    payment_method_code: str = Field(
        default="10",
        description="Código del método de pago (depende del proveedor). Ej: '10'=Efectivo, '48'=Tarjeta",
    )
    payment_form: PaymentForm = PaymentForm.CASH
    payment_due_date: Optional[date] = None

    # Campos opcionales avanzados
    operation_type: Optional[str] = None
    send_email: Optional[bool] = None
    order_reference: Optional[OrderReference] = None
    related_documents: Optional[List[RelatedDocument]] = None
    billing_period: Optional[BillingPeriod] = None
    establishment: Optional[Establishment] = None
    allowance_charges: Optional[List[AllowanceCharge]] = None

    customer: Customer
    items: List[Item]

    @model_validator(mode="after")
    def validate_invoice(self):
        if not self.items:
            raise ValueError("Invoice must contain at least one item")
        if self.payment_form == PaymentForm.CREDIT and not self.payment_due_date:
            raise ValueError(
                "payment_due_date es obligatorio cuando payment_form es 'credit'"
            )
        return self


class SendEmailRequest(BaseModel):
    email: EmailStr
    pdf_base_64_encoded: Optional[str] = None
