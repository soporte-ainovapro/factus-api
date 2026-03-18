from pydantic import BaseModel, EmailStr, model_validator
from typing import Optional

from app.domain.models.enums import IdentificationDocumentType, LegalOrganizationType, TributeType


class Customer(BaseModel):
    """Cliente en un documento de facturación. Usa códigos agnósticos al proveedor."""

    document_type: IdentificationDocumentType
    identification: str

    dv: Optional[str] = None           # Dígito verificación (obligatorio para NIT)
    company: Optional[str] = None      # Razón social (persona jurídica)
    trade_name: Optional[str] = None   # Nombre comercial
    names: Optional[str] = None        # Nombre (persona natural)

    address: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    municipality_code: Optional[str] = None   # Código DANE del municipio, ej "05001"
    organization_type: LegalOrganizationType
    tribute: TributeType

    @model_validator(mode="after")
    def validate_customer(self):
        if self.company is not None:
            if not self.company.strip():
                raise ValueError("Company name cannot be empty")
        else:
            if not self.names:
                raise ValueError("Names is required for natural persons")

        if self.document_type == IdentificationDocumentType.NIT and not self.dv:
            raise ValueError("DV is required for NIT")

        return self
