from typing import TypeVar, Type, Generic
from tortoise.models import Model

T = TypeVar("T", bound=Model)

class BaseService(Generic[T]):
    model: Type[T]

    async def get_by_id(self, id: int) -> T:
        return await self.model.get_or_none(id=id)

    async def list_all(self):
        return await self.model.all()
