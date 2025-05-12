from groq import Groq
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict
from src.MessageGenerator.ProtocolMessageGenerator import ProtocolMessageGenerator


class MessageGeneratorGroq(ProtocolMessageGenerator):
    """!
    @brief Генератор сообщений с использованием Groq API
    
    @details
    Реализует интерфейс ProtocolMessageGenerator для генерации сообщений
    через Groq API, предоставляющий доступ к высокопроизводительным языковым моделям.
    """
    __client: Groq
    __messages: List[Dict[str, str]]
    __model: str

    def __init__(self, model: str = 'llama-3.3-70b-versatile') -> None:
        """!
        @brief Инициализация генератора сообщений
        
        @param model Название модели для генерации (по умолчанию 'llama-3.3-70b-versatile')
        """
        load_dotenv()
        self.__client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.__messages = []
        self.__model = model

    def generate(self, input_message: str, model: Optional[str] = None) -> str:
        """!
        @brief Генерация ответа с использованием Groq API
        
        @param input_message Входное сообщение для обработки
        @param model Название модели для генерации (опционально)
        
        @return str Сгенерированный ответ
        """
        if model is None or model == '':
            model = self.__model
        self.add_user_message(input_message)
        completion = self.__client.chat.completions.create(
            model=model,
            messages=self.__messages,  # type: ignore
            max_tokens=1024,
            temperature=1,
            top_p=1,
            stream=False,
            stop=None,
        )
        output: str = completion.choices[0].message.content  # type: ignore

        self.add_ai_message(output)
        return output
    

    def add_user_message(self, message_content: str) -> None:
        """!
        @brief Добавление сообщения пользователя в историю
        
        @param message_content Текст сообщения пользователя
        """
        formatted_output: Dict[str, str] = {
            "role": 'user',
            "content": message_content
        }
        self.__messages.append(formatted_output)

    def add_ai_message(self, message_content: str) -> None:
        """!
        @brief Добавление сообщения ИИ в историю
        
        @param message_content Текст сообщения ИИ
        """
        formatted_output: Dict[str, str] = {
            "role": 'assistant',
            "content": message_content
        }
        self.__messages.append(formatted_output)

    def add_system_message(self, message_content: str) -> None:
        """!
        @brief Добавление системного сообщения в историю
        
        @param message_content Текст системного сообщения
        """
        formatted_output: Dict[str, str] = {
            "role": 'system',
            "content": message_content
        }
        self.__messages.append(formatted_output)

    def get_message_history(self) -> List[Dict[str, str]]:
        """!
        @brief Получение истории сообщений
        
        @return List[Dict[str, str]] Список сообщений в формате словарей
        """
        return self.__messages
