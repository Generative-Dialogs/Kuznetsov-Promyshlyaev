import os
from typing import Optional, Any, List
from google import genai  # type: ignore
from google.genai import types  # type: ignore
from dotenv import load_dotenv
import logging
from PIL import Image
from io import BytesIO
from src.ImageGenerator.ImageGeneratorProtocol import ImageGeneratorProtocol
from src.config import IMAGE_OUTPUT_DIR


class ImageGeneratorGoogle(ImageGeneratorProtocol):
    """!
    @brief Класс для генерации изображений с использованием Google Gemini API
    
    @details
    Реализует интерфейс ImageGeneratorProtocol для генерации изображений.
    Использует Google Gemini API для создания изображений на основе текстовых промптов
    и опциональных изображений персонажей.
    
    @note Требуется прокси/vpn для работы с Google API
    """
    __client: Any  # Using Any for google.genai.Client since it lacks type stubs
    __output_dir: str

    def __init__(self, session_id: int) -> None:
        """!
        @brief Инициализация генератора изображений
        
        @param session_id ID сессии для организации файлов изображений
        """
        load_dotenv()
        
        # Initialize Gemini API
        self.__client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        
        # Set up output directory
        self.__output_dir = os.path.join(IMAGE_OUTPUT_DIR, str(session_id))
        os.makedirs(self.__output_dir, exist_ok=True)

    def __save_image(self, image_data: bytes, target_path: str) -> Optional[str]:
        """!
        @brief Сохранение изображения в файл
        
        @param image_data Бинарные данные изображения
        @param target_path Путь для сохранения файла
        
        @return Optional[str] Путь к сохраненному файлу или None в случае ошибки
        """
        try:
            # Convert the image data to a PIL Image
            image = Image.open(BytesIO(image_data))
            
            # Save the image
            image.save(target_path)
            
            logging.info(f"Successfully saved image to {target_path}")
            return target_path
            
        except Exception as e:
            logging.error(f"Error saving image: {str(e)}")
            return None

    def generate_image_response(self, prompt: str, target_path: str, character_images: Optional[List[str]] = None) -> Optional[str]:
        """!
        @brief Генерация изображения с использованием Gemini API
        
        @param prompt Текстовый промпт для генерации изображения
        @param target_path Полный путь для сохранения изображения
        @param character_images Опциональный список путей к изображениям персонажей
        
        @return Optional[str] Путь к сохраненному изображению или None в случае ошибки
        """
        try:
            # Prepare contents list with prompt and images
            contents: List[Any] = [prompt]
            
            # Add character images if provided
            if character_images:
                for image_path in character_images:
                    try:
                        image = Image.open(image_path)
                        contents.append(image)
                    except Exception as e:
                        logging.warning(f"Failed to load character image {image_path}: {str(e)}")
            
            # Generate the image using Gemini API
            response = self.__client.models.generate_content(
                model='gemini-2.0-flash-exp-image-generation',
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=['Text', 'Image']
                )
            )
            
            # Process the response
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    return self.__save_image(part.inline_data.data, target_path)
                    
            logging.error("No image data found in response")
            return None
            
        except Exception as e:
            logging.error(f"Error generating image: {str(e)}")
            return None 
    