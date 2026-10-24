from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings

engine = create_async_engine(settings.get_database_url(), echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Зависимость для FastAPI (будем использовать в роутерах)
async def get_db():
    async with async_session_maker() as session:
        yield session