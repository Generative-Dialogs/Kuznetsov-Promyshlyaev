from typing import Optional, Dict, List, Tuple, Any
from src.GameMaster.GameMaster import GameMaster
from src.DatabaseManager.DatabaseManager import DatabaseManager
from src.Actor.Actor import Actor
from src.config import DATABASE_NAME
from src.Descriptions.WorldDecription import base_world_description
from src.GamePresets.GamePresets import GamePresets, GameWorld, GameCharacter

class SessionManager:
    """!
    @brief Менеджер игровых сессий
    
    @details
    Класс отвечает за:
    - Создание и управление игровыми сессиями
    - Управление пользователями
    - Взаимодействие с базой данных для хранения информации о сессиях
    """
    def __init__(self) -> None:
        """!
        @brief Инициализация менеджера сессий
        """
        self.db = DatabaseManager()
        self.active_sessions: Dict[int, GameMaster] = {}
        
    def create_user(self) -> int:
        """!
        @brief Создание нового пользователя
        
        @return int ID созданного пользователя
        """
        return self.db.create_user()

    def start_session(self, session_id: int) -> GameMaster:
        """!
        @brief Запуск или возобновление игровой сессии
        
        @param session_id ID сессии
        
        @return GameMaster Объект мастера игры для управления сессией
        
        @throws ValueError если сессия не найдена
        """
        
        # Get session info
        session_info = self.db.get_session_info(session_id)
        if session_info is None:
            raise ValueError(f"Session {session_id} not found")
            
        
        # Create game master
        return GameMaster(session_id=session_id)

    def get_session(self, session_id: int) -> Optional[GameMaster]:
        """!
        @brief Получение активной игровой сессии
        
        @param session_id ID сессии
        
        @return Optional[GameMaster] Объект мастера игры или None, если сессия не найдена
        """
        return self.active_sessions.get(session_id)

    def delete_user(self, user_id: int) -> None:
        """!
        @brief Удаление всех данных пользователя
        
        @param user_id ID пользователя
        """
        self.db.delete_user_data(user_id) 
    
    def create_session(self, user_id: int, world_description: str, player_description: str, language: str, initial_message: str, initial_message_eng: str) -> int:
        """!
        @brief Создание новой игровой сессии
        
        @param user_id ID пользователя
        @param player_description Описание игрока
        @param language Язык сессии
        @param initial_message Начальное сообщение на языке сессии
        @param initial_message_eng Начальное сообщение на английском
        
        @return int ID созданной сессии
        """
        return self.db.create_session(user_id, world_description, player_description, language, initial_message, initial_message_eng)

    def create_session_by_preset(self, user_id: int, world: GameWorld, character: GameCharacter, language: str) -> int:
        """!
        @brief Создание новой игровой сессии с использованием предустановленных мира и персонажа
        
        @param user_id ID пользователя
        @param world Выбранный игровой мир
        @param character Выбранный персонаж
        @param language Язык сессии
        
        @return int ID созданной сессии
        
        @throws ValueError если персонаж не принадлежит выбранному миру
        """
        # Проверяем, что персонаж доступен в выбранном мире
        if not GamePresets.is_character_in_world(character, world):
            raise ValueError(f"Character {character.name} is not available in world {world.name}")
        
        # Получаем описания мира и персонажа
        world_description = GamePresets.get_world_description(world)
        character_description = GamePresets.get_character_description(character)
        
        # Получаем начальные сообщения персонажа
        initial_message = GamePresets.get_character_initial_message(character, language)
        initial_message_eng = GamePresets.get_character_initial_message(character, "English")
        
        # Создаем сессию с полученными описаниями
        return self.create_session(user_id, world_description, character_description, language, initial_message, initial_message_eng)
