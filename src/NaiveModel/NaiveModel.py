from typing import Optional, Tuple
from src.MessageGenerator.BaseMessageGenerator import get_base_message_generator, RequesterClass
from src.DatabaseManager.DatabaseManager import DatabaseManager
from src.ImageGenerator.ImageGeneratorGoogle import ImageGeneratorGoogle
import os
from src.config import IMAGE_OUTPUT_DIR

class NaiveModel:
    """!
    @brief Наивная модель для сравнения архитектур
    
    @details
    Простая реализация чат-модели, которая:
    1. Получает начальный промпт с описанием мира
    2. Обрабатывает запросы пользователя напрямую
    3. Генерирует изображения на основе ответов
    4. Сохраняет промпты для диалогов
    5. Не использует сложную архитектуру с GameMaster и Actor
    """
    
    def __init__(self, session_id: int) -> None:
        """!
        @brief Инициализация наивной модели
        
        @param session_id ID сессии
        """
        self.__session_id = session_id
        self.__db = DatabaseManager()
        self.__messageGenerator = get_base_message_generator(RequesterClass.GameMaster)
        self.__messageGeneratorDialog = get_base_message_generator(RequesterClass.DialogProcessor)

        self.__imageGenerator = ImageGeneratorGoogle(session_id)
        
        # Get session info from database
        session_info = self.__db.get_session_info(session_id)
        if session_info is None:
            raise ValueError(f"Session {session_id} not found")
            
        self.__world_description, self.__player_description, self.__language, self.__initial_message, self.__initial_message_eng = session_info
        
        # Initialize with world description
        self._initialize_world()
        
    def _initialize_world(self) -> None:
        """!
        @brief Инициализация мира
        
        @details
        Добавляет описание мира в историю сообщений
        """
        world_prompt = f"""
        You are a game master in a role-playing game. Your task is to respond to the player's actions and questions.
        
        World description:
        {self.__world_description}
        
        Player character description:
        {self.__player_description}
        
        Important:
        - All your responses must be in {self.__language} language
        - Be creative and engaging
        - Be brief, the usual answer is 1-2 sentences
        - Maintain consistency with the world description
        - Respond to player actions and questions directly
        - Never describe what the player is doing, respond to his actions
        
        If you understand these guidelines, write "Ready to narrate".
        """
        
        is_new_session = self.__db.is_new_session_gm_prompt(self.__session_id)
        
        self.__messageGenerator.add_system_message(world_prompt)
        response = "Ready to narrate"
        self.__messageGenerator.add_ai_message(response)
        self.__db.save_game_master_prompt(self.__session_id, "start", world_prompt, response)
        
        # Load message history
        master_history = self.__db.get_master_messages(self.__session_id)
        for _, user_input, master_output, _ in master_history:
            self.__messageGenerator.add_user_message(user_input)
            self.__messageGenerator.add_ai_message(master_output)

    def _extract_quotes(self, text: str, sequence_number: int) -> None:
        """!
        @brief Извлечение цитат из текста и сохранение промпта
        
        @param text Текст для обработки
        @param sequence_number Порядковый номер сообщения
        """
        quote_prompt = f"""
        You are a dialogue processor. Your task is to identify direct speech in the text and mark who is speaking.
        
        Rules:
        1. Format each direct speech segment as:
           Speaker=={{speaker_name}}
           Text=={{exact_quote}}
        
        2. Format requirements:
           - Each segment must start with "Speaker==" followed by the speaker's name
           - The next line must start with "Text==" followed by the EXACT quote
           - There must be no empty lines between Speaker== and Text==
           - Each new dialogue segment should be separated by a blank line
        
        3. Text processing rules:
           - ONLY mark direct speech (text in quotes)
           - Keep the exact quote as it appears in the text
           - Do not add any additional text or explanations
           - Do not modify the text content
           - Preserve all punctuation and formatting
        
        Text to process:
        {text}
        
        Return only the direct speech segments in the specified format, nothing else.
        """
        
        dialog_response = self.__messageGeneratorDialog.generate(quote_prompt)
        self.__db.save_dialogue_prompt(self.__session_id, sequence_number, quote_prompt, dialog_response)
    
    def generate_response(self, message: str) -> Tuple[str, Optional[str]]:
        """!
        @brief Генерация ответа на сообщение пользователя
        
        @param message Сообщение пользователя
        
        @return Tuple[str, Optional[str]] Кортеж (ответ модели, путь к изображению)
        """
        # Generate response
        response = self.__messageGenerator.generate(message)
        
        # Get sequence number for dialogue prompt
        sequence_number = len(self.__db.get_master_messages(self.__session_id)) + 1
        
        # Extract and save quotes
        self._extract_quotes(response, sequence_number)
        
        # Generate image prompt
        image_prompt = f"""
        Based on this game master's response, create a detailed visual description of the scene:
        {response}
        
        Important:
        - Focus on the visual elements and atmosphere
        - Do not include any text or words in the image
        - Make it cinematic and dramatic
        - Include environmental details
        - Show the scene from a third-person perspective
        3. Visual Style:
           - Use a consistent gloomy classical painting style
           - Emphasize dramatic chiaroscuro lighting
           - Use muted dark tones (charcoal black, deep navy, antique gold)
           - Include Baroque/Romantic-era aesthetics
           - Show weathered oil texture and cracked varnish aging
           - Use somber atmospheric lighting
           - Include Goya-esque melancholy and Caravaggio-inspired contrasts
           - Add Turner-like stormy ambiance
           - Include haunting ethereal undertones
           - Show detailed brushwork on textures (stone, fabric)
           - Use cold palette with crimson accents
           - Include gothic decay motifs and misty spectral ambiance

        """
        
        # Generate image
        image_path = None
        try:
            # Create image path
            image_number = len(self.__db.get_master_messages(self.__session_id)) + 1
            image_path = os.path.join(IMAGE_OUTPUT_DIR, str(self.__session_id), f"{image_number}.png")
            
            # Generate and save image
            image_path = self.__imageGenerator.generate_image_response(image_prompt, image_path)
        except Exception as e:
            print(f"Error generating image: {str(e)}")
        
        # Save to database
        self.__db.save_user_message(self.__session_id, message, response)
        self.__db.save_master_message(self.__session_id, message, response, response)
        
        return response, image_path 