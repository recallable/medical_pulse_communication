from typing import TypeVar, Type, Generic, List, Optional, Any

from tortoise.models import Model

ModelType = TypeVar("ModelType", bound=Model)

class BaseCRUD(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, id: Any) -> Optional[ModelType]:
        return await self.model.get_or_none(id=id)

    async def get_all(self) -> List[ModelType]:
        return await self.model.all()

    async def create(self, **kwargs) -> ModelType:
        print(type(kwargs['uploader_id']))
        print(type(kwargs['module']))
        print(type(kwargs['source_file_size']))
        return await self.model.create(**kwargs)

    async def update(self, id: Any, obj_in: dict) -> Optional[ModelType]:
        obj = await self.get(id)
        if obj:
            await obj.update_from_dict(obj_in).save()
        return obj

    async def delete(self, id: Any) -> bool:
        obj = await self.get(id)
        if obj:
            await obj.delete()
            return True
        return False
