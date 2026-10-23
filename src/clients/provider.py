import httpx
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs
from src.core.config import settings

class EventsProviderClient:
    def __init__(self, base_url: str = settings.BASE_URL, api_key: str = settings.API_KEY):
        self.base_url = base_url
        self.headers = {"x-api-key": api_key}
        self.client = httpx.AsyncClient(
            base_url=self.base_url, 
            headers=self.headers, 
            timeout=30.0, # Увеличим таймаут на всякий случай
            follow_redirects=True 
        )

    async def close(self):
        await self.client.aclose()

    async def get_events_page(self, changed_at: str, cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Получает одну страницу событий.
        Возвращает словарь с ключами: next, previous, results.
        """
        params = {"changed_at": changed_at}
        if cursor:
            params["cursor"] = cursor

        # Делаем GET запрос к внешнему API
        response = await self.client.get("/api/events/", params=params)
        
        # Если ошибка (4xx, 5xx) - выбрасываем исключение
        response.raise_for_status()
        
        return response.json()

    async def get_available_seats(self, event_id: str) -> List[str]:
        """Получает список свободных мест для события."""
        # Важно: в задании указано, что URL должен заканчиваться на слэш /
        response = await self.client.get(f"/api/events/{event_id}/seats/")
        response.raise_for_status()
        data = response.json()
        return data.get("seats", [])

    async def register_ticket(self, event_id: str, data: dict) -> str:
        """Регистрирует пользователя и возвращает ticket_id."""
        response = await self.client.post(f"/api/events/{event_id}/register/", json=data)
        response.raise_for_status()
        result = response.json()
        return result.get("ticket_id")

    async def cancel_ticket(self, event_id: str, ticket_id: str) -> bool:
        """Отменяет регистрацию."""
        # Внешнее API ожидает ticket_id в теле DELETE запроса
        response = await self.client.request(
            method="DELETE", 
            url=f"/api/events/{event_id}/unregister/", 
            json={"ticket_id": ticket_id}
        )
        response.raise_for_status()
        return response.json().get("success", False)
    from urllib.parse import urlparse, parse_qs

class EventsPaginator:
    def __init__(self, client: EventsProviderClient, changed_at: str):
        self.client = client
        self.changed_at = changed_at

    async def __aiter__(self):
        """
        Асинхронный итератор, который будет по очереди отдавать страницы с событиями.
        """
        cursor = None
        while True:
            # Запрашиваем страницу
            page_data = await self.client.get_events_page(
                changed_at=self.changed_at, 
                cursor=cursor
            )
            
            # Отдаем результаты (список событий) наружу
            yield page_data.get("results", [])
            
            # Берем URL следующей страницы из поля "next"
            next_url = page_data.get("next")
            
            if not next_url:
                # Если next равен null, значит это была последняя страница
                break
                
            # Внешнее API возвращает полный URL в поле next
            # Нам нужно вытащить из него только параметр cursor для следующего запроса
            parsed_url = urlparse(next_url)
            query_params = parse_qs(parsed_url.query)
            
            if "cursor" in query_params:
                cursor = query_params["cursor"][0]
            else:
                break