from typing import Optional, Tuple, List
from src.GameMaster.GameMaster import GameMaster
from src.ImageManager.ImageManager import ImageManager
from src.DatabaseManager.DatabaseManager import DatabaseManager
from src.Actor.Actor import Actor
from src.ImagePromptGenerator.ImagePromptGenerator import ImagePromptGenerator
from src.ImageGenerator.ImageGeneratorGoogle import ImageGeneratorGoogle
from src.STT.STT import STT
from src.AudioManager.AudioManager import AudioManager
import logging


class GameManager:
    """!
    @brief Менеджер игрового процесса
    
    @details
    Координирует взаимодействие между различными компонентами игры:
    - Мастер игры (GameMaster)
    - Менеджер изображений (ImageManager)
    - Менеджер аудио (AudioManager)
    - База данных (DatabaseManager)
    - Актор (Actor)
    
    Отвечает за обработку пользовательского ввода и генерацию ответов,
    включая текстовые описания, изображения и аудио.
    """
    
    def __init__(self, session_id: int) -> None:
        """!
        @brief Инициализация менеджера игры
        
        @param session_id ID игровой сессии
        
        @details
        Создает новый экземпляр менеджера игры и инициализирует
        все необходимые компоненты для работы игровой сессии.
        """
        self.__session_id = session_id
        self.__db = DatabaseManager()
        world_description, player_description, language, _, _ = self.__db.get_session_info(session_id)

        self.__language = language
        self.__player_description = player_description
        self.__game_master = GameMaster(session_id,)
        self.__image_manager = ImageManager(session_id)
        self.__audio_manager = AudioManager(session_id, language=self.__language)
        self.__stt = STT()

    def process_audio_input(self, audio_path: str, generate_image: bool = True, generate_audio: bool = True) -> Tuple[str, Optional[str], Optional[str]]:
        """!
        @brief Обработка аудио ввода от пользователя
        
        @param audio_path Путь к аудиофайлу
        @param generate_image Флаг генерации изображения (по умолчанию True)
        @param generate_audio Флаг генерации аудио (по умолчанию True)
        
        @return Tuple[str, Optional[str], Optional[str]] Кортеж из:
            - Текстового ответа от мастера игры
            - Пути к сгенерированному изображению (если успешно и generate_image=True) или None
            - Пути к сгенерированному аудио (если успешно и generate_audio=True) или None
            
        @details
        Преобразует аудио в текст с помощью STT и обрабатывает полученный текст
        через process_input. Использует язык сессии для распознавания речи.
        """
        try:
            self.__stt.set_language(self.__language)
            
            text_input = self.__stt.audio_to_text(audio_path)
            
            if not text_input or text_input == "Речь не распознана":
                return "Извините, не удалось распознать речь. Пожалуйста, попробуйте еще раз.", None, None
                
            return self.process_input(text_input, generate_image, generate_audio)
            
        except Exception as e:
            logging.error(f"Error processing audio input: {str(e)}")
            return f"Произошла ошибка при обработке аудио: {str(e)}", None, None

    def process_input(self, user_input: str, generate_image: bool = True, generate_audio: bool = True) -> Tuple[str, Optional[str], Optional[str]]:
        """!
        @brief Обработка пользовательского ввода
        
        @param user_input Ввод пользователя
        @param generate_image Флаг генерации изображения (по умолчанию True)
        @param generate_audio Флаг генерации аудио (по умолчанию True)
        
        @return Tuple[str, Optional[str], Optional[str]] Кортеж из:
            - Текстового ответа от мастера игры
            - Пути к сгенерированному изображению (если успешно и generate_image=True) или None
            - Пути к сгенерированному аудио (если успешно и generate_audio=True) или None
        
        @details
        Обрабатывает пользовательский ввод, генерирует ответ и,
        при необходимости, создает изображение и аудио для текущей сцены.
        """
        # Get actor's response first
        text_response = self.__game_master.generate_answer(user_input)
        
        # Получаем текущий номер последовательности из user_messages
        user_messages = self.__db.get_user_messages(self.__session_id)
        current_sequence = len(user_messages) 
        print(current_sequence)
        character_ids = self.__db.get_active_characters_ids(self.__session_id, current_sequence)
        
        image_path = None
        if generate_image:
            try:
                image_path = self.__image_manager.generate_and_save_image(user_input, text_response, character_ids)
                if not image_path:
                    logging.error("Failed to generate image")
            except Exception as e:
                logging.error(f"Error generating image: {str(e)}")
                image_path = None
        
        
        audio_path = None
        if generate_audio:
            try:
                audio_path = self.__audio_manager.process_actor_message(current_sequence)
                if not audio_path:
                    logging.error("Failed to generate audio")
            except Exception as e:
                logging.error(f"Error generating audio: {str(e)}")
                audio_path = None


        return text_response, image_path, audio_path

    def generate_image(self, sequence: int) -> Optional[str]:
        """!
        @brief Генерация изображения для сообщения
        
        @param sequence Номер последовательности сообщения
        
        @return Optional[str] Путь к сгенерированному изображению или None в случае ошибки
        
        @details
        Генерирует изображение для указанного сообщения, используя
        данные из базы данных и активных персонажей.
        """
        try:
            message_data = self.__db.get_user_message(self.__session_id, sequence)
            if not message_data:
                logging.error(f"No message found for sequence {sequence}")
                return None
                
            user_input, actor_output = message_data
            
            character_ids = self.__db.get_active_characters_ids(self.__session_id, sequence)
            
            image_path = self.__image_manager.generate_and_save_image(user_input, actor_output, character_ids)
            if image_path:
                logging.info(f"Image generated and saved to: {image_path}")
                return image_path
            else:
                logging.error("Failed to generate image")
                return None
        except Exception as e:
            logging.error(f"Error generating image: {str(e)}")
            return None

    def generate_audio(self, sequence: int) -> Optional[str]:
        """!
        @brief Генерация аудио для сообщения
        
        @param sequence Номер последовательности сообщения
        
        @return Optional[str] Путь к сгенерированному аудио или None в случае ошибки
        
        @details
        Генерирует аудио для указанного сообщения, используя
        данные из базы данных и активных персонажей.
        """
        try:
            audio_path = self.__audio_manager.process_actor_message(sequence+1)
            if audio_path:
                logging.info(f"Audio generated and saved to: {audio_path}")
                return audio_path
            else:
                logging.error("Failed to generate audio")
                return None
        except Exception as e:
            logging.error(f"Error generating audio: {str(e)}")
            return None