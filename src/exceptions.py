class DomainException(Exception):
    """Базовое исключение для бизнес-логики"""
    pass

class EventNotFound(DomainException):
    pass

class EventNotPublished(DomainException):
    pass

class RegistrationDeadlinePassed(DomainException):
    pass

class SeatNotAvailable(DomainException):
    pass

class TicketNotFound(DomainException):
    pass

class ProviderAPIError(DomainException):
    pass