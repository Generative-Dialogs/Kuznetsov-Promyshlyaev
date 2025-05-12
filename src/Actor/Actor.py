from src.GameMaster.ProtocolGameMaster import ProtocolGameMaster
from typing import List, Dict, Optional
import json
from src.DatabaseManager.DatabaseManager import DatabaseManager
from src.MessageGenerator.BaseMessageGenerator import get_base_message_generator, RequesterClass
from src.Actor.ActorPromts import start_message
from src.GameMaster.GameMasterPromts import off_topic_message_eng, off_topic_message_ru


class Actor:
    """!
    @brief Реализация актора в игровой системе
    
    @details
    Класс отвечает за генерацию детализированных описаний
    действий и событий в игре. Преобразует команды мастера
    игры в нарративные описания с учетом контекста и активных персонажей.
    """
    
    def __init__(self, game_master: ProtocolGameMaster, session_id: int) -> None:
        """!
        @brief Инициализация актора
        
        @param game_master Экземпляр мастера игры
        @param session_id ID игровой сессии
        
        @details
        Создает нового актора с заданными параметрами и инициализирует
        необходимые компоненты для генерации описаний.
        """
        self.__game_master = game_master
        self.__session_id = session_id
        self.__db = DatabaseManager()
        
        # Get session info from database
        session_info = self.__db.get_session_info(session_id)
        if session_info is None:
            raise ValueError(f"Session {session_id} not found")
            
        self.__world_description, self.__player_description, self.__language, self.__initial_message, self.__initial_message_eng = session_info
        
        self.__messageGenerator = get_base_message_generator(RequesterClass.Actor)
        self.__active_characters: Dict[str, str] = {}

        formatted_start_message: str = f'''
        {start_message}
        Story world context: {self.__world_description}

        Important: All your responses must be in {self.__language} language.
        If you understand these guidelines, write "Ready to narrate concisely".
        '''

        is_new_session = self.__db.is_new_session_actor_prompt(session_id)
        
        if is_new_session:
            self.__messageGenerator.add_system_message(formatted_start_message)
            response = "Ready to narrate concisely"
            self.__messageGenerator.add_ai_message(response)
            self.__db.save_actor_prompt(session_id, formatted_start_message, response)
        else:
            # Load prompts from database for existing session
            for prompt_content, model_response in self.__db.get_actor_prompts(session_id):
                self.__messageGenerator.add_system_message(prompt_content)
                self.__messageGenerator.add_ai_message(model_response)

        # Load actor message history
        actor_history = self.__db.get_actor_messages(session_id)
        for _, master_prompt, actor_response in actor_history:
            self.__messageGenerator.add_user_message(master_prompt)
            self.__messageGenerator.add_ai_message(actor_response)

    def update_active_characters(self, characters: Dict[str, str]) -> None:
        """!
        @brief Обновление списка активных персонажей
        
        @param characters Словарь с именами и описаниями активных персонажей
        
        @details
        Обновляет список персонажей, которые в данный момент
        присутствуют в сцене и могут участвовать в действиях.
        """
        self.__active_characters = characters

    def get_detailed_action(self, game_master_output: str, user_input: str) -> str:
        """!
        @brief Получение детализированного описания действия
        
        @param game_master_output Выходные данные мастера игры
        @param user_input Ввод пользователя
        
        @return str Детализированное описание действия
        
        @details
        Генерирует подробное нарративное описание действия
        на основе команд мастера игры и контекста активных персонажей.
        Учитывает язык генерации и сохраняет историю сообщений.
        """
        # Format character information
        characters_info = "\n".join([f"{name}: {desc}" for name, desc in self.__active_characters.items()])
        if game_master_output == off_topic_message_eng:
            if self.__language == 'Russian':
                response = off_topic_message_ru
            else:
                response =  off_topic_message_eng
            self.__db.save_actor_message(self.__session_id, game_master_output, response)
            return response

        narration_prompt = f'''
        Current scene characters:
        {characters_info}

        User's input: "{user_input}"
        Game Master's output: {game_master_output}

        Transform this into a concise narrative following the established guidelines.
        Remember:
            Never describe a dialogue, write what it says.
            If you have been given an answer with specific details, they should be described if this is important information for the plot that the character obviously sees. If this information is part of the dialogue, describe it if a normal conversation between people involves the disclosure of this information.
            Never describe the actions of a player character.
            Never describe something that has already been described in a player's input unless you change it.
        '''
        
        response = self.__messageGenerator.generate(narration_prompt)
        
        # Save to database
        self.__db.save_actor_message(self.__session_id, game_master_output, response)
        
        return response

    def get_message_history(self) -> List[Dict[str, str]]:
        """!
        @brief Получение истории сообщений
        
        @return List[Dict[str, str]] Список словарей с историей сообщений
        
        @details
        Возвращает полную историю сообщений, включая системные
        сообщения, сообщения пользователя и ответы актора.
        """
        return self.__messageGenerator.get_message_history()
