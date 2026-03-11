from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from decimal import Decimal

class WithholdingTax(BaseModel):
    code: str
    withholding_tax_rate: Decimal

class Mandate(BaseModel):
    identification_document_id: int
    identification: str

class Item(BaseModel):
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
