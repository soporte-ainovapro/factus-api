from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models.lookup import (
    Municipality, Tax, Unit, NumberingRange, Country, Acquirer
)

class ILookupGateway(ABC):
    @abstractmethod
    async def get_municipalities(self, token: str) -> List[Municipality]:
        pass

    @abstractmethod
    async def get_tax_types(self, token: str) -> List[Tax]:
        pass

    @abstractmethod
    async def get_units(self, token: str) -> List[Unit]:
        pass

    @abstractmethod
    async def get_numbering_ranges(self, token: str) -> List[NumberingRange]:
        pass

    @abstractmethod
    async def get_countries(self, token: str, name: Optional[str] = None) -> List[Country]:
        pass

    @abstractmethod
    async def get_acquirer(
        self,
        token: str,
        identification_document_id: int,
        identification_number: str
    ) -> Acquirer:
        pass
