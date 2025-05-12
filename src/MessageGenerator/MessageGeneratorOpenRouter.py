import os
from dotenv import load_dotenv
from typing import Optional, List, Dict
from src.MessageGenerator.ProtocolMessageGenerator import ProtocolMessageGenerator
from openai import OpenAI


class MessageGeneratorOpenRouter(ProtocolMessageGenerator):
    """!
    @brief Генератор сообщений с использованием OpenRouter API
    
    @details
    Реализует интерфейс ProtocolMessageGenerator для генерации сообщений
    через OpenRouter API, предоставляющий доступ к различным языковым моделям.
    """
    __client: OpenAI
    __messages: List[Dict[str, str]]
    __model: str

    def __init__(self, model: str = 'gpt-4.1-mini') -> None:
        """!
        @brief Инициализация генератора сообщений
        
        @param model Название модели для генерации 
        """
        load_dotenv()
        self.__client = OpenAI(api_key=os.getenv("PROXY_API"), base_url="https://api.proxyapi.ru/openai/v1")
        self.__messages = []
        self.__model = model

    def generate(self, input_message: str, model: Optional[str] = None) -> str:
        """!
        @brief Генерация ответа с использованием OpenRouter API
        
        @param input_message Входное сообщение для обработки
        @param model Название модели для генерации (опционально)
        
        @return str Сгенерированный ответ
        """
        if model is None:
            model = self.__model
        self.add_user_message(input_message)
        completion = self.__client.chat.completions.create(
            model=model,
            messages=self.__messages,  # type: ignore
            max_completion_tokens=1024,
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
