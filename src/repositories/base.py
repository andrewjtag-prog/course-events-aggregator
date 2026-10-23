from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, obj_id: str) -> Optional[ModelType]:
        """Получить запись по ID"""
        query = select(self.model).where(self.model.id == obj_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[ModelType]:
        """Получить все записи"""
        query = select(self.model)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> ModelType:
        """Создать новую запись"""
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush() # Отправляем в БД, но не коммитим (коммит будет в сервисе)
        return obj

    async def update(self, obj: ModelType, **kwargs) -> ModelType:
        """Обновить существующую запись"""
        for key, value in kwargs.items():
            setattr(obj, key, value)
        await self.session.flush()
        return obj