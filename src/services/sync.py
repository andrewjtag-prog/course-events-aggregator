import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.provider import EventsPaginator, EventsProviderClient
from src.models.sync_metadata import SyncMetadata
from src.repositories.event import EventRepository, PlaceRepository

logger = logging.getLogger(__name__)


class SyncService:
    def __init__(self, session: AsyncSession, client: EventsProviderClient):
        self.session = session
        self.client = client
        self.event_repo = EventRepository(session)
        self.place_repo = PlaceRepository(session)

    async def get_last_changed_at(self) -> str:
        """Получает дату последней синхронизации из БД"""
        result = await self.session.execute(select(SyncMetadata).limit(1))
        meta = result.scalar_one_or_none()
        if meta and meta.last_changed_at:
            return meta.last_changed_at
        return "2000-01-01"

    async def save_last_changed_at(self, changed_at: str):
        """Сохраняет дату последней синхронизации в БД"""
        result = await self.session.execute(select(SyncMetadata).limit(1))
        meta = result.scalar_one_or_none()
        
        if not meta:
            meta = SyncMetadata()
            self.session.add(meta)
        
        meta.last_changed_at = changed_at
        meta.last_sync_time = datetime.now(timezone.utc)
        meta.sync_status = "success"
        await self.session.commit()

    async def sync_events(self, changed_at: str = None) -> int:
        """
        Синхронизирует события с внешним API.
        Если changed_at не передан — использует дату последней синхронизации.
        """
        if changed_at is None:
            changed_at = await self.get_last_changed_at()

        logger.info("Starting sync with changed_at=%s", changed_at)
        paginator = EventsPaginator(self.client, changed_at=changed_at)
        processed_count = 0
        max_changed_at = changed_at

        try:
            async for page_results in paginator:
                for event_data in page_results:
                    await self._process_event(event_data)
                    processed_count += 1
                    
                    event_changed = event_data.get("changed_at", changed_at)
                    if event_changed > max_changed_at:
                        max_changed_at = event_changed
                
                await self.session.commit()
                
            # Сохраняем новую дату синхронизации
            await self.save_last_changed_at(max_changed_at)
                
            logger.info("Sync finished. Processed %s events.", processed_count)
            return processed_count
        except Exception as e:
            logger.error("Error during sync: %s", e)
            await self.session.rollback()
            raise e

    async def _process_event(self, event_data: dict):
        """Обрабатывает одно событие: сохраняет площадку и само событие"""
        place_data = event_data.pop("place", None)
        place_id = place_data["id"] if place_data else None

        if place_data:
            await self._save_place(place_data)

        existing_event = await self.event_repo.get_by_id(event_data["id"])

        event_time = datetime.fromisoformat(event_data["event_time"].replace("Z", "+00:00"))
        reg_deadline = datetime.fromisoformat(event_data["registration_deadline"].replace("Z", "+00:00"))
        changed_at = datetime.fromisoformat(event_data["changed_at"].replace("Z", "+00:00"))
        created_at = datetime.fromisoformat(event_data["created_at"].replace("Z", "+00:00"))
        status_changed_at = datetime.fromisoformat(event_data["status_changed_at"].replace("Z", "+00:00"))

        if existing_event:
            await self.event_repo.update(
                existing_event,
                name=event_data["name"],
                place_id=place_id, 
                event_time=event_time,
                registration_deadline=reg_deadline,
                status=event_data["status"],
                number_of_visitors=event_data["number_of_visitors"],
                changed_at=changed_at,
                status_changed_at=status_changed_at
            )
        else:
            await self.event_repo.create(
                id=event_data["id"],
                name=event_data["name"],
                place_id=place_id, 
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