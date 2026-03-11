from pydantic import BaseModel, Field, model_validator
from typing import List, Optional

from app.domain.models.customer import Customer
from app.domain.models.establishment import Establishment
from app.domain.models.item import Item
from app.domain.models.shared import BillingPeriod, AllowanceCharge

class CreditNote(BaseModel):
    numbering_range_id: int
    correction_concept_code: int = Field(..., description="1: Devolución parcial, 2: Anulación factura, 3: Rebaja, 4: Descuento, etc.")
    customization_id: int = Field(default=20, description="20: Nota de crédito que referencia una factura electrónica. 22: Nota crédito sin referencia a facturas.")
    
    bill_id: Optional[int] = None
    reference_code: str
    observation: Optional[str] = None
    
    payment_method_code: str = Field(default="10")
    send_email: Optional[int] = Field(default=None, description="1 para enviar email, 0 para no enviar (o booleano según Factus). Factus a veces usa bool 0/1.")

    billing_period: Optional[BillingPeriod] = None
    establishment: Optional[Establishment] = None
    customer: Customer
    items: List[Item]
    allowance_charges: Optional[List[AllowanceCharge]] = None

    @model_validator(mode="after")
    def validate_credit_note(self):
        if not self.items:
            raise ValueError("Credit note must contain at least one item")
        if self.customization_id == 20 and not self.bill_id:
            raise ValueError("bill_id es obligatorio para notas crédito que referencian facturas (customization_id=20)")
        return self
