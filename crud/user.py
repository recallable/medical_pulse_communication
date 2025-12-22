from typing import Optional

from crud.base import BaseCRUD
from models import User


class CRUDUser(BaseCRUD[User]):
    async def get_by_username(self, username: str) -> Optional[User]:
        return await self.model.get_or_none(username=username)

    async def get_by_phone(self, phone: str) -> Optional[User]:
        return await self.model.get_or_none(phone=phone)

user_crud = CRUDUser(User)
