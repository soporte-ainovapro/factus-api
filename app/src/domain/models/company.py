from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr

class SimpleCodeName(BaseModel):
    code: str
    name: str

class Department(BaseModel):
    code: str
    name: str

class Municipality(BaseModel):
    code: str
    name: str
    department: Optional[Department] = None

class CompanyData(BaseModel):
    url_logo: Optional[str] = None
    nit: Optional[str] = None
    dv: Optional[str] = None
    company: Optional[str] = None
    trade_name: Optional[str] = None
    names: Optional[str] = None
    surnames: Optional[str] = None
    graphic_representation_name: Optional[str] = None
    registration_code: Optional[str] = None
    economic_activity: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    tribute: Optional[SimpleCodeName] = None
    legal_organization: Optional[SimpleCodeName] = None
    municipality: Optional[Municipality] = None
    responsibilities: Optional[List[SimpleCodeName]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class CompanyResponse(BaseModel):
    status: str
    message: str
    data: Optional[CompanyData] = None

class CompanyUpdate(BaseModel):
    legal_organization_code: str = Field(description="Código de los tipos de organizaciones")
    company: Optional[str] = None
    trade_name: Optional[str] = None
    names: str
    surnames: str
    registration_code: Optional[str] = None
    economic_activity: str
    phone: str
    email: EmailStr
    address: str
    tribute_code: str = Field(description="Tributos")
    municipality_code: str = Field(description="Municipios")
    responsibilities: str = Field(description="Responsabilidades fiscales")

class LogoData(BaseModel):
    url_log: str

class CompanyLogoUpdateResponse(BaseModel):
    status: str
    message: str
    data: Optional[LogoData] = None
