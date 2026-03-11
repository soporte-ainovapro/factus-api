from pydantic import BaseModel

class Establishment(BaseModel):
    name: str
    address: str
    phone_number: str
    email: str
    municipality_id: int
