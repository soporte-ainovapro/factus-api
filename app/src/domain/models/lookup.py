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
