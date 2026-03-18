from pydantic import BaseModel, Field, model_validator
from typing import List, Optional

from app.domain.models.customer import Customer
from app.domain.models.establishment import Establishment
from app.domain.models.item import Item
from app.domain.models.shared import BillingPeriod, AllowanceCharge
from app.domain.models.enums import CorrectionConcept


class CreditNote(BaseModel):
    """
    Nota crédito electrónica en términos del dominio del negocio.
    Usa valores canónicos independientes del proveedor.
    """

    numbering_range_prefix: str   # Prefijo del rango (ej "NC"). El adaptador resuelve el ID.

    correction_concept: CorrectionConcept = Field(
        ...,
        description="Motivo de la nota crédito"
    )

    # Si references_invoice=True, bill_reference_number es obligatorio
    references_invoice: bool = True
    bill_reference_number: Optional[str] = None   # Número de factura original (ej "SETT-5")

    reference_code: str
    observation: Optional[str] = None

    payment_method_code: str = Field(default="10")
    send_email: Optional[bool] = None

    billing_period: Optional[BillingPeriod] = None
    establishment: Optional[Establishment] = None
    customer: Customer
    items: List[Item]
    allowance_charges: Optional[List[AllowanceCharge]] = None

    @model_validator(mode="after")
    def validate_credit_note(self):
        if not self.items:
            raise ValueError("Credit note must contain at least one item")
        if self.references_invoice and not self.bill_reference_number:
            raise ValueError(
                "bill_reference_number es obligatorio cuando references_invoice=True"
            )
        return self
