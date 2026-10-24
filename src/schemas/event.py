from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class PlaceSchema(BaseModel):
    id: str
    name: str
    city: str
    address: str
    seats_pattern: str

    model_config = ConfigDict(from_attributes=True)

class EventShortSchema(BaseModel):
    id: str
    name: str
    place: PlaceSchema
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int

    model_config = ConfigDict(from_attributes=True)

class EventDetailSchema(EventShortSchema):
    # Если понадобятся дополнительные поля для детального просмотра, добавим их тут
    pass

class PaginatedEventsSchema(BaseModel):
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: List[EventShortSchema]