from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

class NumberingRangeCreate(BaseModel):
    document: str
    prefix: str
    current: int
    resolution_number: str

class NumberingRangeUpdate(BaseModel):
    current: int

class NumberingRange(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    document: str
    document_name: Optional[str] = None
    prefix: str
    from_: Optional[int] = Field(None, alias="from")
    to: Optional[int] = None
    current: int
    resolution_number: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    technical_key: Optional[str] = None
    is_expired: bool
    is_active: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class NumberingRangeResponse(BaseModel):
    status: str
    message: str
    data: Optional[NumberingRange] = None

class NumberingRangeListResponse(BaseModel):
    status: str
    message: str
    data: Optional[List[NumberingRange]] = None

class NumberingRangeSoftware(BaseModel):
    resolution_number: str
    prefix: str
    from_: str = Field(alias="from")
    to: str
    start_date: str
    end_date: str
    technical_key: str

class NumberingRangeSoftwareResponse(BaseModel):
    status: str
    message: str
    data: Optional[List[NumberingRangeSoftware]] = None

class NumberingRangeDeleteResponse(BaseModel):
    status: str
    message: str
