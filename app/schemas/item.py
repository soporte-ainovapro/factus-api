from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from decimal import Decimal

from app.schemas.enums import TributeType, IdentificationDocumentType


class WithholdingTax(BaseModel):
    code: str
    withholding_tax_rate: Decimal


class Mandate(BaseModel):
    document_type: IdentificationDocumentType
    identification: str


class Item(BaseModel):
    """Línea de producto/servicio en un documento de facturación."""

    code_reference: str
    name: str

    quantity: int = Field(gt=0)

    price: Decimal = Field(gt=0)
    discount_rate: Decimal = Field(default=Decimal("0.00"), ge=0)

    tax_rate: Decimal = Field(ge=0)

    # Códigos canónicos — el adaptador los traduce al ID entero del proveedor
    unit_measure_code: str     # Ej: "94" = unidad, "KGM" = kilogramo
    standard_code: str         # Ej: "1" = estándar de adopción del contribuyente

    is_excluded: bool = False  # True si el ítem está excluido de IVA
    tribute: TributeType

    # Campos avanzados opcionales
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
