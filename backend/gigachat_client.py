import os
import json
import re
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")

# --- Промпт для создания верхнеуровневых этапов ---
INITIAL_PROMPT_MESSAGES = [
    Messages(
        role=MessagesRole.SYSTEM,
        content="""Ты — AI-наставник. Твоя задача — создавать структурированные пошаговые планы в формате JSON. Ты отвечаешь ТОЛЬКО валидным JSON-массивом, без какого-либо дополнительного текста или форматирования."""
    ),
    Messages(
        role=MessagesRole.USER,
        content="Моя цель: 'Выучить Go для бэкенд-разработки'"
    ),
    Messages(
        role=MessagesRole.ASSISTANT,
        content="""[{"title": "Этап 1: Основы языка Go", "description": "Изучение базового синтаксиса, типов данных, управляющих конструкций и горутин.", "difficulty": "green"}, {"title": "Этап 2: Веб-сервер на Go", "description": "Практика создания простого HTTP-сервера с использованием стандартной библиотеки.", "difficulty": "yellow"}, {"title": "Этап 3: Работа с базами данных", "description": "Подключение к PostgreSQL, выполнение CRUD-операций.", "difficulty": "red"}, {"title": "Этап 4: Деплой приложения", "description": "Сборка приложения в Docker-контейнер и развертывание на сервере.", "difficulty": "purple"}]"""
    ),
]

# --- Промпт для декомпозиции одного этапа на подзадачи ---
DECOMPOSE_PROMPT_MESSAGES = [
    Messages(
        role=MessagesRole.SYSTEM,
        content="""Ты — AI-наставник. Твоя задача — детализировать этап плана, разбивая его на подзадачи в формате JSON. Ты отвечаешь ТОЛЬКО валидным JSON-массивом, без какого-либо дополнительного текста или форматирования."""
    ),
    Messages(
        role=MessagesRole.USER,
        content="Детализируй этап: 'Этап 2: Веб-сервер на Go', описание: 'Практика создания простого HTTP-сервера с использованием стандартной библиотеки.'"
    ),
    Messages(
        role=MessagesRole.ASSISTANT,
        content="""[{"title": "Настройка роутинга", "description": "Создание обработчиков для разных URL-путей.", "difficulty": "green"}, {"title": "Работа с JSON", "description": "Научиться принимать и отправлять данные в формате JSON.", "difficulty": "yellow"}, {"title": "Middleware", "description": "Реализовать промежуточное ПО для логирования и аутентификации.", "difficulty": "yellow"}]"""
    ),
]

def _clean_and_parse_json(ai_response: str) -> list[dict]:
    """
    "Бронебойный" парсер: очищает ответ AI от мусора и извлекает JSON.
    """
    match = re.search(r'```json\s*([\s\S]*?)\s*```', ai_response)
    if match:
        json_str = match.group(1)
    else:
        json_start = ai_response.find('[')
        json_end = ai_response.rfind(']') + 1
        if json_start != -1 and json_end != 0:
            json_str = ai_response[json_start:json_end]
        else:
            raise ValueError("JSON-массив не найден в ответе модели")

    return json.loads(json_str)

async def _get_ai_response(base_messages: list, user_prompt: str) -> list[dict]:
    if not GIGACHAT_CREDENTIALS:
        print("Ошибка: Учетные данные GigaChat не настроены.")
        return []
    try:
        full_messages = base_messages + [Messages(role=MessagesRole.USER, content=user_prompt)]
        
        with GigaChat(credentials=GIGACHAT_CREDENTIALS, verify_ssl_certs=False) as giga:
            response = giga.chat(Chat(messages=full_messages, temperature=0.7))
            response_text = response.choices[0].message.content
            return _clean_and_parse_json(response_text)
            
    except Exception as e:
        print(f"Произошла ошибка при обращении к GigaChat: {e}")
        return []

async def generate_initial_steps(prompt: str) -> list[dict]:
    updated_initial_messages = list(INITIAL_PROMPT_MESSAGES)
    updated_initial_messages[0] = Messages(
        role=MessagesRole.SYSTEM,
        content="""Ты — AI-наставник. Твоя задача — создавать структурированные пошаговые планы в формате JSON. Ты отвечаешь ТОЛЬКО валидным JSON-массивом, без какого-либо дополнительного текста или форматирования. Для каждого этапа определи сложность по шкале: 'green' (легко), 'yellow' (средне), 'red' (сложно), 'purple' (очень сложно, ключевой этап)."""
    )

    user_prompt_content = f"Моя цель: '{prompt}'"
    return await _get_ai_response(updated_initial_messages, user_prompt_content)

async def generate_sub_steps(step_title: str, step_description: str) -> list[dict]:
    updated_decompose_messages = list(DECOMPOSE_PROMPT_MESSAGES)
    updated_decompose_messages[0] = Messages(
        role=MessagesRole.SYSTEM,
        content="""Ты — AI-наставник. Твоя задача — детализировать этап плана, разбивая его на подзадачи в формате JSON. Ты отвечаешь ТОЛЬКО валидным JSON-массивом, без какого-либо дополнительного текста или форматирования. Для каждой подзадачи определи сложность по шкале: 'green', 'yellow', 'red', 'purple'."""
    )
    
    user_prompt_content = f"Детализируй этап: '{step_title}', описание: '{step_description}'"
    return await _get_ai_response(updated_decompose_messages, user_prompt_content)