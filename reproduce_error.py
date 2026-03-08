from pydantic import BaseModel, ValidationError
from typing import List, Optional
import json

class InvoiceItem(BaseModel):
    code_reference: str
    name: str

class Customer(BaseModel):
    identification_document_id: int
    identification: str

class Invoice(BaseModel):
    document: str = "01"
    customer: Customer
    items: List[InvoiceItem]

# Error case: string representing JSON
data_string = '{"document":"01","customer":{"identification_document_id":1,"identification":"123"},"items":[{"code_reference":"ref","name":"item"}]}'
try:
    print("Attempting to validate string...")
    Invoice.model_validate(data_string)
    print("String validation: Success")
except ValidationError as e:
    print(f"String validation: caught expected ValidationError:")
    print(e.json())
except Exception as e:
    print(f"String validation: Unexpected error: {type(e).__name__}: {e}")
