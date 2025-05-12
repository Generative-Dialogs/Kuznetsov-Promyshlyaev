from typing import List, Tuple, Optional
import re
from src.DatabaseManager.DatabaseManager import DatabaseManager
from src.MessageGenerator.BaseMessageGenerator import get_base_message_generator, RequesterClass

class DialogueProcessor:
    """!
    @brief Процессор диалогов для обработки текста и выделения говорящих персонажей
    
    @details
    Класс обрабатывает текст, выделяет диалоги персонажей и размечает их.
    Использует базу данных для получения информации о персонажах и
    MessageGenerator для разметки текста. Сохраняет промпты и ответы модели
    в базу данных для последующего использования.
    """
    def __init__(self, session_id: int):
        """!
        @brief Инициализация процессора диалогов
        
        @param session_id ID сессии для получения персонажей и промптов из базы данных
        """
        self.db = DatabaseManager()
        self.session_id = session_id
        self.message_generator = get_base_message_generator(RequesterClass.ImagePromter)
        self._load_characters()
        self._load_prompts()

    def _load_prompts(self) -> None:
        """!
        @brief Загрузка промптов из базы данных
        
        @details
        Загружает все промпты для текущей сессии и добавляет их в историю сообщений
        генератора для поддержания контекста диалога.
        """
        prompts = self.db.get_dialogue_prompts(self.session_id)
        for sequence_number, prompt_content, model_response in prompts:
            self.message_generator.add_user_message(prompt_content)
            self.message_generator.add_ai_message(model_response)

    def _save_prompt(self, sequence_number: int, prompt_content: str, model_response: str) -> None:
        """!
        @brief Сохранение промпта в базу данных
        
        @param sequence_number Порядковый номер сообщения
        @param prompt_content Содержимое промпта
        @param model_response Ответ модели
        """
        self.db.save_dialogue_prompt(self.session_id, sequence_number, prompt_content, model_response)

    def _load_characters(self) -> None:
        """!
        @brief Загрузка персонажей из базы данных для текущей сессии
        
        @details
        Загружает имена и описания персонажей, которые будут использоваться
        при разметке диалогов.
        """
        characters = self.db.get_characters(self.session_id)
        self.character_names = [char[0] for char in characters]
        self.character_descriptions = {char[0]: char[1] for char in characters}

    def _analyze_errors(self, original_text: str, segments: List[Tuple[str, str]]) -> Optional[str]:
        """!
        @brief Анализ ошибок в разметке текста
        
        @param original_text Исходный текст
        @param segments Обработанные сегменты текста
        
        @return Optional[str] Описание ошибок или None если ошибок нет
        
        @details
        Проверяет:
        1. Наличие неизвестных персонажей
        2. Наличие цитат в оригинальном тексте (убирая кавычки из ответа модели)
        """
        errors = []
        
        # Проверка на неизвестных персонажей
        unknown_speakers = []
        for i, (speaker, _) in enumerate(segments):
            if speaker not in self.character_names:
                # Ищем похожие имена
                similar_names = []
                speaker_lower = speaker.lower()
                for name in self.character_names:
                    if speaker_lower in name.lower() or name.lower() in speaker_lower:
                        similar_names.append(f"[{name}]")
                
                if similar_names:
                    unknown_speakers.append((i, speaker, similar_names))
                else:
                    unknown_speakers.append((i, speaker, None))
        
        if unknown_speakers:
            error_locations = []
            for i, speaker, similar_names in unknown_speakers:
                if similar_names:
                    error_locations.append(f"segment {i}: '{speaker}' - did you mean {', '.join(similar_names)}?")
                else:
                    error_locations.append(f"segment {i}: '{speaker}'")
            
            errors.append(f"Unknown speakers found at: {', '.join(error_locations)}")
        
        # Проверка что все цитаты присутствуют в оригинальном тексте
        for i, (_, quote) in enumerate(segments):
            # Убираем кавычки из цитаты, если они есть
            clean_quote = quote.strip('"')
            if clean_quote not in original_text:
                errors.append(f"Quote at segment {i} not found in original text: {quote}")
        
        return "\n".join(errors) if errors else None

    def _create_initial_prompt(self, text: str, errors: Optional[str] = None) -> str:
        """!
        @brief Создание начального промпта для разметки текста
        
        @param text Текст для разметки
        @param errors Описание ошибок предыдущей попытки (если есть)
        
        @return str Промпт для генератора
        
        @details
        Создает промпт, который содержит:
        1. Правила форматирования диалогов
        2. Список допустимых имен персонажей
        3. Описания известных персонажей
        4. Примеры правильного форматирования
        """
        self._load_characters()
        characters_info = "\n".join([
            f"Character name- [{name}]. \n Character description- {desc}" 
            for name, desc in self.character_descriptions.items()
        ])
        
        prompt = f"""
            You are a dialogue processor. Your task is to identify ONLY direct speech in the text and mark who is speaking.
            
            Rules:
            1. ONLY mark direct speech (text in quotes) with the speaker's name
            2. Format each direct speech segment as:
               Speaker=={{speaker_name}}
               Text=={{exact_quote}}
            
            3. Valid speaker names are:
               - One of the known character names: {f'\n'.join([f'[{name}]' for name in self.character_names])}
               - You MUST use the FULL name as shown in square brackets, but WITHOUT the brackets in the output
               - Do not use partial names or nicknames
            
            4. Format requirements:
               - Each segment must start with "Speaker==" followed by the speaker's name
               - The next line must start with "Text==" followed by the EXACT quote
               - There must be no empty lines between Speaker== and Text==
               - Each new dialogue segment should be separated by a blank line
            
            5. Text processing rules:
               - ONLY mark direct speech (text in quotes)
               - Keep the exact quote as it appears in the text
               - Do not add any additional text or explanations
               - Do not modify the text content
               - Preserve all punctuation and formatting
            
            Known characters and their descriptions:
            {characters_info}

            Text to process:
            {text}

            Example of correct format:
            Speaker==John
            Text=="I'll have a pint of your finest ale, barkeep."
            
            Speaker==Barkeep
            Text=="That'll be one coin."
            
            Speaker==John
            Text=="Ok, Good."

            Return only the direct speech segments in the specified format, nothing else.
            Remember, ONLY mark direct speech (text in quotes) with the speaker's name.
        """
        if errors is not None:
            prompt += f"\n Previous attempt had the following errors: \n {errors}"
        return prompt

    def _parse_response(self, response: str) -> List[Tuple[str, str]]:
        """!
        @brief Парсинг ответа генератора в список кортежей
        
        @param response Ответ генератора
        
        @return List[Tuple[str, str]] Список кортежей (имя_персонажа, текст)
        
        @throws ValueError если обнаружено недопустимое имя персонажа
        
        @details
        Разбирает ответ генератора на сегменты диалога, проверяя:
        1. Корректность формата (Speaker== и Text==)
        2. Допустимость имен персонажей
        3. Наличие текста для каждого сегмента
        """
        segments = []
        current_speaker = None
        current_text = None
        
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('Speaker=='):
                # Если есть предыдущий сегмент, сохраняем его
                if current_speaker and current_text is not None:
                    segments.append((current_speaker, current_text))
                
                # Извлекаем имя говорящего
                speaker = line[9:].strip()
                current_speaker = speaker
                current_text = None
                
            elif line.startswith('Text==') and current_speaker:
                current_text = line[6:].strip()
        
        # Добавляем последний сегмент
        if current_speaker and current_text is not None:
            segments.append((current_speaker, current_text))
        return segments

    def _is_not_only_punctuation(self, text: str) -> bool:
        """!
        @brief Проверка, состоит ли текст только из знаков препинания
        
        @param text Текст для проверки
        
        @return bool True если текст состоит только из знаков препинания
        """
        return any(c.isalnum() for c in text)

    def process_text(self, text: str, sequence_number: int) -> List[Tuple[str, str]]:
        """!
        @brief Обработка текста и создание промпта для модели
        
        @param text Исходный текст для обработки
        @param sequence_number Порядковый номер сообщения
        
        @return List[Tuple[str, str]] Список кортежей (говорящий, текст)
        
        @details
        Обрабатывает текст в несколько попыток:
        1. Создает промпт
        2. Получает ответ модели
        3. Парсит ответ
        4. Проверяет на ошибки
        5. Упорядочивает цитаты по их позиции в тексте
        6. Добавляет оставшийся текст как GM
        7. Сохраняет промпт и ответ
        """
        max_attempts = 5
        attempt = 0
        errors = None
        
        while attempt < max_attempts:
            try:
                prompt = self._create_initial_prompt(text, errors)
                response = self.message_generator.generate(prompt)
                segments = self._parse_response(response)
                errors = self._analyze_errors(text, segments)
                self._save_prompt(sequence_number, prompt, response)

                if errors is None:
                    # Упорядочиваем цитаты по их позиции в тексте
                    ordered_segments = []
                    for speaker, quote in segments:
                        pos = text.find(quote)
                        if pos != -1:
                            ordered_segments.append((pos, speaker, quote))
                    
                    ordered_segments.sort(key=lambda x: x[0])
                    
                    # Формируем результат
                    result = []
                    current_pos = 0
                    
                    for pos, speaker, quote in ordered_segments:
                        # Добавляем текст до цитаты как GM
                        if pos > current_pos:
                            gm_text = text[current_pos:pos].strip()
                            if gm_text and self._is_not_only_punctuation(gm_text):
                                result.append(("GM", gm_text))
                        
                        # Добавляем цитату
                        result.append((speaker, quote))
                        current_pos = pos + len(quote)
                    
                    # Добавляем оставшийся текст как GM
                    if current_pos < len(text):
                        remaining = text[current_pos:].strip()
                        if remaining and self._is_not_only_punctuation(remaining):
                            result.append(("GM", remaining))
                    
                    return result
                    
                attempt += 1
                continue
            except ValueError as e:
                attempt += 1
                continue
                
        raise ValueError("Failed to process text after multiple attempts")

    def process_message(self, sequence_number: int) -> List[Tuple[str, str]]:
        """!
        @brief Обработка сообщения по его порядковому номеру
        
        @param sequence_number Порядковый номер сообщения
        
        @return List[Tuple[str, str]] Список кортежей (говорящий, текст)
        
        @throws ValueError если сообщение не найдено
        
        @details
        1. Получает текст сообщения из базы данных
        2. Обрабатывает текст
        3. Возвращает разобранные сегменты диалога
        """
        message_data = self.db.get_user_message(self.session_id, sequence_number)
        if not message_data:
            raise ValueError(f"No message found for sequence {sequence_number}")
            
        _, text = message_data
        
        segments = self.process_text(text, sequence_number)
        
        return segments 