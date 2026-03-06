from abc import ABC, abstractmethod
from typing import List
from app.src.domain.models.lookup import (
    Municipality, Tax, Unit, NumberingRange
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
