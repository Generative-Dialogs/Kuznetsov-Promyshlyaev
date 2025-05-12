from typing import List, Dict, Optional
from src.DatabaseManager.DatabaseManager import DatabaseManager
from src.MessageGenerator.BaseMessageGenerator import get_base_message_generator, RequesterClass
from src.GamePresets.GamePresets import GamePresets, GameWorld, GameCharacter


class Tester:
    """!
    @brief Класс для тестирования диалогов
    
    @details
    Класс имитирует пользовательский ввод, загружая сообщения из памяти
    и действуя от имени заданного персонажа игрока
    """
    def __init__(self, session_id: int) -> None:
        """!
        @brief Инициализация тестера
        
        @param session_id ID сессии для тестирования
        """
        self.db = DatabaseManager()
        self.session_id = session_id
        
        # Загружаем информацию о сессии
        session_info = self.db.get_session_info(session_id)
        if session_info is None:
            raise ValueError(f"Session {session_id} not found")
            
        world_description, player_description, language, _ , _ = session_info
        
        # Создаем генератор сообщений
        self.message_generator = get_base_message_generator(RequesterClass.Tester)
        
        # Формируем начальный промпт
        initial_prompt = f"""
            You're posing as a user-player in a role-playing game to test it. 
            The player, (that is, you) plays a certain character, its description will be given below. 
            You will receive information from the game in the text messages.   
            These messages reflect what happened in the game. As a player, you need to react to them somehow.
            The reaction should be the action your character is trying to do.         
            Game World:
            {world_description}

            Your Character:
            {player_description}

            Instructions:
            1. Stay in character at all times
            2. Maintain consistency with the game world's setting
            3. All answers must contain an action performed by your character.
            4. Do not break character or acknowledge being an AI
            5. Do not use meta-commentary about the game or role-playing
            6. Answer briefly 2-3 sentences.

            Begin the conversation in character.
            Important: All your responses must be in {language} language.

            """
        
        # Добавляем системное сообщение с полным промптом
        self.message_generator.add_system_message(initial_prompt)
        
        # Загружаем историю сообщений в генератор
        user_messages = self.db.get_user_messages(session_id)
        actor_messages = self.db.get_actor_messages(session_id)
        
        # Загружаем историю диалога в генератор
        for user_msg, actor_msg in zip(user_messages, actor_messages):
            self.message_generator.add_ai_message(user_msg)
            self.message_generator.add_user_message(actor_msg)

    def get_actor_response(self, message: str) -> str:
        """!
        @brief Тестовые запросы к модели
        
        @param message Сообщение тестируемоей модели
        
        @return str Следующий запрос к модели (шаг в диалоге)
        """
        return self.message_generator.generate(message)

