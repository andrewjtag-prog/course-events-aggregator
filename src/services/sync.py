import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from src.clients.provider import EventsProviderClient, EventsPaginator
from src.repositories.event import EventRepository, PlaceRepository
from src.models.place import Place

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self, session: AsyncSession, client: EventsProviderClient):
        self.session = session
        self.client = client
        self.event_repo = EventRepository(session)
        self.place_repo = PlaceRepository(session)

    async def sync_events(self, changed_at: str) -> int:
        """
        Синхронизирует события с внешним API.
        Возвращает количество обработанных событий.
        """
        logger.info(f"Starting sync with changed_at={changed_at}")
        paginator = EventsPaginator(self.client, changed_at=changed_at)
        processed_count = 0

        try:
            # Асинхронно итерируемся по страницам
            async for page_results in paginator:
                for event_data in page_results:
                    await self._process_event(event_data)
                    processed_count += 1
                
                # Коммитим изменения после каждой страницы, чтобы не держать гигантскую транзакцию
                await self.session.commit()
                
            logger.info(f"Sync finished. Processed {processed_count} events.")
            return processed_count
        except Exception as e:
            logger.error(f"Error during sync: {e}")
            await self.session.rollback()
            raise e

    async def _process_event(self, event_data: dict):
        """Обрабатывает одно событие: сохраняет площадку и само событие"""
        place_data = event_data.pop("place", None)
        
        # Вытаскиваем ID площадки, так как API присылает вложенный объект place
        place_id = place_data["id"] if place_data else None

        if place_data:
            await self._save_place(place_data)

        # Проверяем, есть ли уже такое событие в БД
        existing_event = await self.event_repo.get_by_id(event_data["id"])

        # Парсим строковые даты из ISO формата в объекты datetime
        # Заменяем 'Z' на '+00:00' для корректного парсинга в Python 3.10 и ниже
        event_time = datetime.fromisoformat(event_data["event_time"].replace("Z", "+00:00"))
        reg_deadline = datetime.fromisoformat(event_data["registration_deadline"].replace("Z", "+00:00"))
        changed_at = datetime.fromisoformat(event_data["changed_at"].replace("Z", "+00:00"))
        created_at = datetime.fromisoformat(event_data["created_at"].replace("Z", "+00:00"))
        status_changed_at = datetime.fromisoformat(event_data["status_changed_at"].replace("Z", "+00:00"))

        if existing_event:
            # Обновляем существующее
            await self.event_repo.update(
                existing_event,
                name=event_data["name"],
                place_id=place_id, # <--- ИСПРАВЛЕНО ЗДЕСЬ
                event_time=event_time,
                registration_deadline=reg_deadline,
                status=event_data["status"],
                number_of_visitors=event_data["number_of_visitors"],
                changed_at=changed_at,
                status_changed_at=status_changed_at
            )
        else:
            # Создаем новое
            await self.event_repo.create(
                id=event_data["id"],
                name=event_data["name"],
                place_id=place_id, # <--- ИСПРАВЛЕНО ЗДЕСЬ
                event_time=event_time,
                registration_deadline=reg_deadline,
                status=event_data["status"],
                number_of_visitors=event_data["number_of_visitors"],
                changed_at=changed_at,
                created_at=created_at,
                status_changed_at=status_changed_at
            )

    async def _save_place(self, place_data: dict):
        """Сохраняет или обновляет площадку"""
        existing_place = await self.place_repo.get_by_id(place_data["id"])
        
        changed_at = datetime.fromisoformat(place_data["changed_at"].replace("Z", "+00:00"))
        created_at = datetime.fromisoformat(place_data["created_at"].replace("Z", "+00:00"))

        if existing_place:
            await self.place_repo.update(
                existing_place,
                name=place_data["name"],
                city=place_data["city"],
                address=place_data["address"],
                seats_pattern=place_data["seats_pattern"],
                changed_at=changed_at
            )
        else:
            await self.place_repo.create(
                id=place_data["id"],
                name=place_data["name"],
                city=place_data["city"],
                address=place_data["address"],
                seats_pattern=place_data["seats_pattern"],
                changed_at=changed_at,
                created_at=created_at
            )