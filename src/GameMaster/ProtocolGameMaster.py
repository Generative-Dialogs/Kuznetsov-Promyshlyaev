from typing import Protocol, Optional, List, Tuple, Set
from src.GameMaster.CommandData import CommandData

class ProtocolGameMaster(Protocol):
    """!
    @brief Протокол для мастера игры
    
    @details
    Определяет интерфейс для мастера игры, который отвечает за:
    - Генерацию ответов на действия игрока
    - Управление игровыми персонажами
    - Поддержание целостности игрового мира
    - Обработку команд и инструкций
    """
    world_description: str
    player_description: str
    
    def generate_answer(self, message: str) -> str:
        """!
        @brief Генерация ответа на сообщение игрока
        
        @param message Сообщение игрока
        @return str Ответ системы
        """
        ...

    def generate_instruction(self, message: str) -> Tuple[List[CommandData], str]:
        """!
        @brief Генерация инструкций на основе сообщения
        
        @param message Сообщение для обработки
        @return Tuple[List[CommandData], str] Кортеж из списка команд и текстового вывода
        """
        ...

    def parse_commands(self, commands: List[CommandData]) -> Tuple[str, Set[str]]:
        """!
        @brief Обработка списка команд
        
        @param commands Список команд для обработки
        @return Tuple[str, Set[str]] Кортеж из текстового вывода и множества имен активных персонажей
        """
        ...

    def validate_and_parse(self, input_text: str) -> Tuple[Optional[List[CommandData]], str]:
        """!
        @brief Валидация и парсинг входного текста
        
        @param input_text Текст для валидации и парсинга
        @return Tuple[Optional[List[CommandData]], str] Кортеж из списка команд (или None) и сообщения об ошибке
        """
        ...
