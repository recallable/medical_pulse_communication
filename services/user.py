from models.entity.user import User
from services.base import BaseService

class UserService(BaseService[User]):
    model = User

    async def get_user_by_username(self, username: str) -> User:
        return await self.model.get_or_none(username=username)
