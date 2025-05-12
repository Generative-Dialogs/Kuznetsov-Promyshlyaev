from typing import List, Dict, Optional
from src.MessageGenerator.BaseMessageGenerator import get_base_message_generator, RequesterClass
from src.DatabaseManager.DatabaseManager import DatabaseManager
from src.Descriptions.WorldDecription import base_world_description
import logging


class ImagePromptGenerator:
    """!
    @brief Генератор промптов для создания изображений
    
    @details
    Класс отвечает за:
    - Создание детальных промптов для генерации изображений
    - Поддержание согласованности описаний персонажей
    - Учет контекста сцены и действий
    - Генерацию стилистически согласованных описаний
    """
    def __init__(self, session_id: int) -> None:
        """!
        @brief Инициализация генератора промптов
        
        @param session_id ID сессии для организации промптов
        """
        self.__session_id = session_id
        self.__messageGenerator = get_base_message_generator(RequesterClass.ImagePromter)
        self.__db = DatabaseManager()
        
        start_message = f'''
        You are an expert at creating detailed image generation prompts. Your task is to create a prompt that will generate an image showing the final state of a scene after described events.

        World Description:
        {base_world_description}

        Guidelines for creating prompts:
        1. Character Consistency:
           - Maintain consistent appearance for each character across all images
           - Update character appearance based on events (injuries, changes in clothing, etc.)
           - Include detailed physical descriptions for each character
           - Reference previous character descriptions to maintain consistency
           - The image generation model will receive full character descriptions and their reference images

        2. Scene Composition:
           - Show the final state of the scene after all actions
           - Focus on what the player character sees at the moment
           - Include all relevant characters and their positions
           - Show environmental changes caused by events
           - DO NOT include any text, words, or writing in the generated image
           - The image should be purely visual without any text elements

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

        4. Technical Requirements:
           - Be extremely detailed in descriptions
           - Include specific colors, textures, and materials
           - Specify lighting conditions and atmosphere
           - Describe character expressions and body language
           - Include environmental details and weather conditions
           - Reference previous character appearances for consistency
           - The image generation model will receive complete character descriptions and reference images
           - Ensure no text or writing appears in the generated image

        Format your response as a single, detailed prompt without any additional text or explanations.
        '''

        # Load existing image prompts from database
        image_prompts = self.__db.get_image_prompts(session_id)
        for _, user_input, narrative_response, image_prompt in image_prompts:
            self.__messageGenerator.add_user_message(f"User's action: {user_input}\nScene description: {narrative_response}")
            self.__messageGenerator.add_ai_message(image_prompt)

        # Add the start message
        self.__messageGenerator.add_system_message(start_message)

    def generate_prompt(self, user_input: str, system_output: str, character_ids: List[int]) -> Optional[str]:
        """!
        @brief Генерация промпта для создания изображения
        
        @param user_input Ввод пользователя
        @param system_output Ответ системы
        @param character_ids Список ID персонажей, участвующих в сцене
        
        @return Optional[str] Сгенерированный промпт или None в случае ошибки
        """
        try:
            # Get character information from database
            character_info = []
            for char_id in character_ids:
                character = self.__db.get_character(char_id)
                if character:
                    name, description = character
                    character_info.append(f"{name}: {description}")
            
            # Construct the prompt with character information
            character_section = ""
            if character_info:
                character_section = "\n\nCharacter information:\n" + "\n".join(character_info)
            
            prompt = self.__messageGenerator.generate(
                f'''Don't describe the scenes of cruelty too colorfully. Scene description: {system_output} 
                \n It is character description image generation model also has this description and images of these characters: {character_section}''')
            character_section += "\n\nImages of these characters are attached for reference. In the same order"

            prompt += character_section
            prompt += "You can censor violent scenes if they don't comply with company policy."
            
            # Save the prompt to database
            self.__db.save_image_prompt(self.__session_id, user_input, system_output, prompt)
            
            return prompt
        except Exception as e:
            logging.error(f"Error generating image prompt: {str(e)}")
            return None

