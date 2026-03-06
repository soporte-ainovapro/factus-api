from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional

T = TypeVar("T")

class IRepository(ABC, Generic[T]):
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[T]:
        pass

    @abstractmethod
    async def get_all(self) -> List[T]:
        pass

    @abstractmethod
    async def add(self, entity: T) -> T:
        pass
