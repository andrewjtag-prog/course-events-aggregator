from unittest.mock import AsyncMock, patch

import pytest
from httpx import Request, Response

from src.clients.provider import EventsPaginator, EventsProviderClient


@pytest.fixture
def client():
    # Создаем клиент для тестов с фейковыми настройками
    return EventsProviderClient(base_url="http://fake-api.com", api_key="test_key")

@pytest.mark.asyncio
async def test_get_events_page_success(client):
    # Создаем фейковый ответ от внешнего API
    fake_response_data = {
        "next": "http://fake-api.com/api/events/?cursor=123",
        "previous": None,
        "results": [{"id": "event1", "name": "Test Event"}]
    }
    
    # Важно: создаем настоящий объект Response из httpx, который уже содержит json
    mock_response = Response(
        status_code=200, 
        json=fake_response_data, 
        request=Request("GET", "http://fake-api.com/api/events/")
    )
    
    # Мокаем метод get нашего асинхронного клиента
    with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
        # Настраиваем, что "фейковый" сервер вернет наш объект Response
        mock_get.return_value = mock_response

        # Вызываем наш метод
        result = await client.get_events_page(changed_at="2000-01-01")

        # Проверяем, что метод отработал правильно
        assert result["results"][0]["name"] == "Test Event"
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_events_paginator(client):
    # Подготавливаем фейковые ответы для двух страниц
    page_1 = {
        "next": "http://fake-api.com/api/events/?changed_at=2000-01-01&cursor=page2",
        "results": [{"id": "1"}, {"id": "2"}]
    }
    page_2 = {
        "next": None,  # Конец данных
        "results": [{"id": "3"}]
    }

    # Мокаем метод get_events_page нашего клиента
    with patch.object(client, "get_events_page", new_callable=AsyncMock) as mock_get:
        # side_effect позволяет возвращать разные значения при разных вызовах
        mock_get.side_effect = [page_1, page_2]

        paginator = EventsPaginator(client, changed_at="2000-01-01")
        
        all_events = []
        # Проходимся по итератору
        async for page_results in paginator:
            all_events.extend(page_results)

        # Проверяем, что собрали все 3 события
        assert len(all_events) == 3
        assert all_events[0]["id"] == "1"
        assert all_events[2]["id"] == "3"
        
        # Проверяем, что клиент был вызван ровно 2 раза (2 страницы)
        assert mock_get.call_count == 2