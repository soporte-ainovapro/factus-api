from pydantic import BaseModel
from typing import Optional
from datetime import date
from decimal import Decimal

class OrderReference(BaseModel):
    reference_code: str
    issue_date: Optional[date] = None

class RelatedDocument(BaseModel):
    code: str
    issue_date: date
    number: str

class BillingPeriod(BaseModel):
    start_date: date
    start_time: Optional[str] = None
    end_date: date
    end_time: str

class AllowanceCharge(BaseModel):
    concept_type: str
    is_surcharge: bool
    reason: str
    base_amount: Decimal
    amount: Decimal
