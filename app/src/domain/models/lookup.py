from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


class LookupBase(BaseModel):
    id: int
    name: str


class Municipality(LookupBase):
    code: str
    department: str


class Tax(LookupBase):
    code: str
    description: Optional[str] = None


class Unit(LookupBase):
    code: str


class NumberingRange(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    document: str
    prefix: str
    from_number: Optional[int] = Field(None, alias="from")
    to_number: Optional[int] = Field(None, alias="to")
    current: Optional[int] = None
    resolution_number: Optional[str] = None
    technical_key: Optional[str] = None
    is_active: bool


class Country(BaseModel):
    id: int
    code: str
    name: str


class Acquirer(BaseModel):
    name: str
    email: str


# --- Tablas de referencia fijas (norma DIAN) ---

class ReferenceEntry(BaseModel):
    """Entrada genérica con código de texto y nombre."""
    code: str
    name: str


class ReferenceEntryInt(BaseModel):
    """Entrada genérica con ID entero y nombre."""
    id: int
    name: str


class CustomerTributeEntry(BaseModel):
    id: int
    code: str
    name: str


class ReferenceTables(BaseModel):
    """Tablas de referencia fijas definidas por la DIAN / Factus."""
    identification_document_types: List[ReferenceEntryInt]
    legal_organization_types: List[ReferenceEntryInt]
    customer_tribute_types: List[CustomerTributeEntry]
    payment_methods: List[ReferenceEntry]
    payment_forms: List[ReferenceEntry]
    product_standard_codes: List[ReferenceEntryInt]
    document_types: List[ReferenceEntry]
