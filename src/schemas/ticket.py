from pydantic import BaseModel, EmailStr

class TicketCreateSchema(BaseModel):
    event_id: str
    first_name: str
    last_name: str
    email: EmailStr  # Pydantic сам проверит валидность email
    seat: str

class TicketResponseSchema(BaseModel):
    ticket_id: str

class SeatsResponseSchema(BaseModel):
    event_id: str
    available_seats: list[str]