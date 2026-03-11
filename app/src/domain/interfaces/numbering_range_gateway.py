from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.src.domain.models.numbering_range import (
    NumberingRangeResponse,
    NumberingRangeListResponse,
    NumberingRangeCreate,
    NumberingRangeUpdate,
    NumberingRangeDeleteResponse,
    NumberingRangeSoftwareResponse,
)

class INumberingRangeGateway(ABC):
    @abstractmethod
    async def get_numbering_ranges(self, token: str, filters: Optional[Dict[str, Any]] = None) -> NumberingRangeListResponse:
        """
        Gets a list of numbering ranges using optional filters.
        """
        pass

    @abstractmethod
    async def get_numbering_range(self, id: int, token: str) -> NumberingRangeResponse:
        """
        Gets a specific numbering range by its ID.
        """
        pass

    @abstractmethod
    async def create_numbering_range(self, range_data: NumberingRangeCreate, token: str) -> NumberingRangeResponse:
        """
        Creates a new numbering range.
        """
        pass

    @abstractmethod
    async def update_numbering_range_consecutive(self, id: int, update_data: NumberingRangeUpdate, token: str) -> NumberingRangeResponse:
        """
        Updates the consecutive (current) value of a numbering range.
        """
        pass

    @abstractmethod
    async def delete_numbering_range(self, id: int, token: str) -> NumberingRangeDeleteResponse:
        """
        Deletes a numbering range by its ID.
        """
        pass

    @abstractmethod
    async def get_software_numbering_ranges(self, token: str) -> NumberingRangeSoftwareResponse:
        """
        Gets numbering ranges associated with the software from DIAN.
        """
        pass
