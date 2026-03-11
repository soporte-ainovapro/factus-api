from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from datetime import date

from app.domain.models.customer import Customer
from app.domain.models.establishment import Establishment
from app.domain.models.item import Item
from app.domain.models.shared import OrderReference, RelatedDocument, BillingPeriod, AllowanceCharge

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
    items: List[Item]

    @model_validator(mode="after")
    def validate_invoice(self):
        if not self.items:
            raise ValueError("Invoice must contain at least one item")
        if self.payment_form == "2" and not self.payment_due_date:
            raise ValueError("payment_due_date es obligatorio cuando payment_form es 2 (crédito)")
        return self
