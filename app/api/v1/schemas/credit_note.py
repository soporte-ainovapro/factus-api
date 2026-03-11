from pydantic import BaseModel
from typing import Optional

class CreditNoteResponse(BaseModel):
    number: str
    prefix: str
    cufe: str # For Credit Notes it's usually CUDE, but reusing similar fields might happen depending on Factus API. They usually call it 'qr_url', 'cufe' internally sometimes or 'cude'. Let's map it based on what Factus returns.
    qr_url: str
    status: str
    message: Optional[str] = None
