import os
import shutil
from typing import Optional, Any, List
import logging
from src.DatabaseManager.DatabaseManager import DatabaseManager
from src.ImageGenerator.ImageGeneratorProtocol import ImageGeneratorProtocol
from src.ImageGenerator.ImageGeneratorGoogle import ImageGeneratorGoogle
from src.ImagePromptGenerator.ImagePromptGenerator import ImagePromptGenerator
from src.GameMaster.GameMasterPromts import off_topic_message_eng, off_topic_message_ru
from src.config import IMAGE_OUTPUT_DIR

error_image_path = 'src/ImageManager/error.png'

class ImageManager:
    """!
    @brief Менеджер для управления генерацией и хранением изображений
    
    @details
    Класс отвечает за:
    - Генерацию портретов персонажей
    - Создание изображений сцен
    - Управление файлами изображений
    - Взаимодействие с базой данных для хранения информации об изображениях
    """
    __session_id: int
    __db: DatabaseManager
    __image_generator: ImageGeneratorProtocol
    __prompt_generator: ImagePromptGenerator

    def __init__(self, session_id: int) -> None:
        """!
        @brief Инициализация менеджера изображений
        
        @param session_id ID сессии для организации файлов изображений
        """
        self.__session_id = session_id
        self.__db = DatabaseManager()
        self.__image_generator = ImageGeneratorGoogle(session_id)
        self.__prompt_generator = ImagePromptGenerator(session_id)

    def generate_character_portrait(self, character_name: str, character_description: str) -> Optional[str]:
        """!
        @brief Генерация портрета персонажа
        
        @param character_name Имя персонажа
        @param character_description Описание персонажа
        
        @return Optional[str] Путь к сохраненному портрету или None в случае ошибки
        """
        try:
            # Create character directory if it doesn't exist
            character_dir = os.path.join(IMAGE_OUTPUT_DIR, str(self.__session_id), "characters")
            os.makedirs(character_dir, exist_ok=True)
            
            # Create prompt for character portrait
            prompt = f"Create a portrait of {character_name}. {character_description}. The character should be centered on a neutral background. The style is Gloomy classical painting style with dramatic chiaroscuro, muted dark tones (charcoal black, deep navy, antique gold), Baroque/Romantic-era aesthetics, weathered oil texture, cracked varnish aging, somber atmospheric lighting, Goya-esque melancholy, Caravaggio-inspired contrasts, Turner-like stormy ambiance, haunting ethereal undertones, detailed brushwork on textures (stone, fabric), cold palette with crimson accents, gothic decay motifs, and misty spectral ambiance."
            
            # Generate image
            image_path = os.path.join(character_dir, f"{character_name}.png")
            return self.__image_generator.generate_image_response(prompt, image_path)
                
        except Exception as e:
            logging.error(f"Error generating character portrait: {str(e)}")
            return None

    def generate_and_save_image(self, user_input: str, actor_output: str, character_ids: List[int]) -> Optional[str]:
        """!
        @brief Генерация и сохранение изображения сцены
        
        @param user_input Ввод пользователя
        @param actor_output Описание сцены от актора
        @param character_ids Список ID персонажей, участвующих в сцене
        
        @return Optional[str] Путь к сохраненному изображению или None в случае ошибки
        """
        if actor_output in [off_topic_message_ru, off_topic_message_eng]:
            self.__db.save_image_prompt(self.__session_id, user_input, actor_output, off_topic_message_eng)
            image_prompts = self.__db.get_image_prompts(self.__session_id)
            next_sequence = len(image_prompts)            

            target_path = f"{IMAGE_OUTPUT_DIR}/{self.__session_id}/{next_sequence}.png"
            shutil.copy2(error_image_path, target_path)
            
            return target_path

        # Generate prompt with character information
        image_prompt = self.__prompt_generator.generate_prompt(user_input, actor_output, character_ids)
        
        # Get the next sequence number from database
        image_prompts = self.__db.get_image_prompts(self.__session_id)
        next_sequence = len(image_prompts)
        
        # Get character image paths
        character_images = []
        for char_id in character_ids:
            character = self.__db.get_character(char_id)
            if character:
                name, _ = character
                char_image_path = os.path.join(IMAGE_OUTPUT_DIR, str(self.__session_id), "characters", f"{name}.png")
                if os.path.exists(char_image_path):
                    character_images.append(char_image_path)
        
        # Generate and save image
        target_path = os.path.join(IMAGE_OUTPUT_DIR, str(self.__session_id), f"{next_sequence}.png")
        if image_prompt is None:
            return None
        return self.__image_generator.generate_image_response(image_prompt, target_path, character_images) 