from pydantic import BaseModel, EmailStr, model_validator
from typing import Optional

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
