from typing import Protocol, Optional, List, Dict


class ProtocolMessageGenerator(Protocol):
    """!
    @brief Протокол для генерации сообщений
    
    @details
    Определяет интерфейс для классов, реализующих генерацию сообщений.
    Используется как контракт для различных реализаций генераторов сообщений.
    """

    def generate(self, messages: str, model: str = '') -> str:
        """!
        @brief Генерация ответа на основе входного сообщения
        
        @param messages Входное сообщение для обработки
        @param model Название модели для генерации (опционально)
        
        @return str Сгенерированный ответ
        """
        ...

    def add_user_message(self, message: str) -> None:
        """!
        @brief Добавление сообщения пользователя в историю
        
        @param message Текст сообщения пользователя
        """
        ...

    def add_system_message(self, message: str) -> None:
        """!
        @brief Добавление системного сообщения в историю
        
        @param message Текст системного сообщения
        """
        ...

    def add_ai_message(self, message: str) -> None:
        """!
        @brief Добавление сообщения ИИ в историю
        
        @param message Текст сообщения ИИ
        """
        ...

    def get_message_history(self) -> List[Dict[str, str]]:
        """!
        @brief Получение истории сообщений
        
        @return List[Dict[str, str]] Список сообщений в формате словарей
        """
        ...
