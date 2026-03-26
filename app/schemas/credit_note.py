from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from datetime import date

from app.schemas.customer import Customer
from app.schemas.establishment import Establishment
from app.schemas.item import Item
from app.schemas.shared import (
    BillingPeriod,
    AllowanceCharge,
    BillingReference,
)
from app.schemas.enums import PaymentForm


class CreditNote(BaseModel):
    """
    Documento de Nota Crédito en términos del dominio del negocio.
    Reutiliza Customer, Items y Establishment igual que la factura.
    """

    numbering_range_prefix: str
    reference_code: str
    
    # Target bill to apply credit note
    bill_id: int
    
    # Conceptos de corrección Factus (ej: 1=Devolución parte de bienes, 2=Anulación de factura electrónica, etc.)
    correction_concept_code: int
    customization_id: int = Field(
        default=20, 
        description="ID del tipo de operación (20 para Nota Crédito genérica, 22 para sin referencia a facturas)"
    )
    operation_type: Optional[str] = None

    observation: Optional[str] = Field(default=None, max_length=250)

    # Pago
    payment_method_code: str = Field(
        default="10",
        description="Código del método de pago (depende del proveedor). Ej: '10'=Efectivo, '48'=Tarjeta",
    )
    payment_form: PaymentForm = PaymentForm.CASH

    # Campos opcionales avanzados
    send_email: Optional[int] = None
    billing_period: Optional[BillingPeriod] = None
    establishment: Optional[Establishment] = None
    allowance_charges: Optional[List[AllowanceCharge]] = None

    billing_reference: Optional[BillingReference] = None

    customer: Customer
    items: List[Item]

    @model_validator(mode="after")
    def validate_credit_note(self):
        if not self.items:
            raise ValueError("CreditNote must contain at least one item")
        return self
