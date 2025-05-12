import os
from typing import Optional, List, Dict
from src.MessageGenerator.ProtocolMessageGenerator import ProtocolMessageGenerator
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


class MessageGeneratorTransformers(ProtocolMessageGenerator):
    """!
    @brief Генератор сообщений с использованием локальной модели Qwen
    
    @details
    Реализует интерфейс ProtocolMessageGenerator для генерации сообщений
    через локальную модель Qwen, используя библиотеку transformers.
    """
    __model: AutoModelForCausalLM
    __tokenizer: AutoTokenizer
    __messages: List[Dict[str, str]]
    __model_name: str

    def __init__(self, model_name: str = "Qwen/Qwen3-0.6B") -> None:
        """!
        @brief Инициализация генератора сообщений
        
        @param model_name Название модели для генерации
        """
        self.__model_name = model_name
        self.__tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.__model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map="auto"
        )
        self.__messages = []

    def generate(self, input_message: str, model: Optional[str] = None) -> str:
        """!
        @brief Генерация ответа с использованием модели Qwen
        
        @param input_message Входное сообщение для обработки
        @param model Название модели для генерации (игнорируется, используется модель из конструктора)
        
        @return str Сгенерированный ответ
        """
        self.add_user_message(input_message)
        
        # Подготовка входных данных
        text = self.__tokenizer.apply_chat_template(
            self.__messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False
        )
        model_inputs = self.__tokenizer(text, return_tensors="pt").to(self.__model.device)
        
        # Генерация ответа
        generated_ids = self.__model.generate(
            **model_inputs,
            max_new_tokens=32768
        )
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
        
        # Парсинг ответа
        try:
            # Поиск маркера конца размышлений
            index = len(output_ids) - output_ids[::-1].index(151668)
        except ValueError:
            index = 0
        
        # Извлекаем только финальный ответ
        content = self.__tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")
        
        # Сохраняем ответ в историю
        self.add_ai_message(content)
        return content

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