import random
import os
from typing import Dict, List, Optional, Tuple
from src.DatabaseManager.DatabaseManager import DatabaseManager
from src.DialogueProcessor.DialogueProcessor import DialogueProcessor
from src.TTS.FilterPresetsType import FilterPresetsType
from src.TTS.TextToSpeech import TextToSpeech
from pydub import AudioSegment

class AudioManager:
    """!
    @brief Менеджер аудио для управления голосами персонажей
    
    @details
    Отвечает за:
    - Обработку сообщений актера
    - Создание и управление голосами персонажей
    - Настройку параметров голоса (высота, фильтры)
    - Озвучивание текста и объединение аудиофайлов
    """
    # Настройки голоса для GM
    GM_VOICE_SETTINGS = {
        "ru": {
            "voice_name": "ru-RU-Chirp3-HD-Orus",
            "pitch_shift": -3,
            "filter_preset": FilterPresetsType.REALISTIC.value
        },
        "en": {
            "voice_name": "en-US-Chirp3-HD-Orus",
            "pitch_shift": -3,
            "filter_preset": FilterPresetsType.REALISTIC.value
        }
    }
    language_dict = {'en': 'en', 'ru': 'ru', 'English': 'en', 'Russian': 'ru'}
    def __init__(self, session_id: int, language: str = "en"):
        """!
        @brief Инициализация менеджера аудио
        
        @param session_id ID сессии
        @param language Язык для голосов (по умолчанию "en")
        """
        self.session_id = session_id
        self.language = self.language_dict[language]
        self.db = DatabaseManager()
        self.dialogue_processor = DialogueProcessor(session_id)
        self.tts = TextToSpeech()
        
        # Создаем директорию для аудиофайлов сессии
        self.session_audio_dir = os.path.join("sound", str(session_id))
        os.makedirs(self.session_audio_dir, exist_ok=True)
        
        
        self.available_voices = {
            'en': 
                {'male': ['en-US-Casual-K', 'en-US-Chirp-HD-D', 'en-US-Chirp3-HD-Achird', 'en-US-Chirp3-HD-Algenib',
                          'en-US-Chirp3-HD-Alnilam', 'en-US-Chirp3-HD-Charon', 'en-US-Chirp3-HD-Enceladus', 
                          'en-US-Chirp3-HD-Fenrir', 'en-US-Chirp3-HD-Iapetus', 'en-US-Chirp3-HD-Orus', 
                          'en-US-Chirp3-HD-Puck', 'en-US-Chirp3-HD-Rasalgethi', 'en-US-Chirp3-HD-Sadachbia', 
                          'en-US-Chirp3-HD-Sadaltager', 'en-US-Chirp3-HD-Schedar', 'en-US-Chirp3-HD-Umbriel', 
                          'en-US-Chirp3-HD-Zubenelgenubi', 'en-US-Neural2-A', 'en-US-Neural2-D', 'en-US-Neural2-I', 
                          'en-US-Neural2-J'], 
                 'female': ['en-US-Chirp-HD-F', 'en-US-Chirp-HD-O', 'en-US-Chirp3-HD-Achernar', 
                            'en-US-Chirp3-HD-Aoede', 'en-US-Chirp3-HD-Autonoe', 'en-US-Chirp3-HD-Callirrhoe',
                            'en-US-Chirp3-HD-Despina', 'en-US-Chirp3-HD-Erinome', 'en-US-Chirp3-HD-Gacrux', 
                            'en-US-Chirp3-HD-Kore', 'en-US-Chirp3-HD-Laomedeia', 'en-US-Chirp3-HD-Leda',
                            'en-US-Chirp3-HD-Pulcherrima', 'en-US-Chirp3-HD-Sulafat', 'en-US-Chirp3-HD-Vindemiatrix', 
                            'en-US-Chirp3-HD-Zephyr', 'en-US-Neural2-C', 'en-US-Neural2-E', 'en-US-Neural2-F', 
                            'en-US-Neural2-G', 'en-US-Neural2-H']},
            'ru': 
                {'male': ['ru-RU-Chirp3-HD-Charon', 'ru-RU-Chirp3-HD-Fenrir', 'ru-RU-Chirp3-HD-Orus', 
                          'ru-RU-Chirp3-HD-Puck', 'ru-RU-Standard-B', 'ru-RU-Standard-D', 'ru-RU-Wavenet-B', 
                          'ru-RU-Wavenet-D'], 
                'female': ['ru-RU-Chirp3-HD-Aoede', 'ru-RU-Chirp3-HD-Kore', 'ru-RU-Chirp3-HD-Leda', 
                           'ru-RU-Chirp3-HD-Zephyr', 'ru-RU-Standard-A', 'ru-RU-Standard-C',
                           'ru-RU-Standard-E', 'ru-RU-Wavenet-A', 'ru-RU-Wavenet-C', 'ru-RU-Wavenet-E']}}
    def _get_random_voice(self, gender: str) -> str:
        """!
        @brief Получение случайного голоса для заданного пола
        
        @param gender Пол персонажа ('male' или 'female')
        
        @return str Название голоса
        """
        voices = self.available_voices.get(self.language, {}).get(gender, [])
        if not voices:
            # Если голоса для языка не найдены, используем английские
            voices = self.available_voices["en"][gender]
        return random.choice(voices)

    def _get_random_pitch_shift(self) -> int:
        """!
        @brief Получение случайного смещения высоты голоса
        
        @return int Смещение высоты от -3 до 3
        """
        return random.randint(-3, 3)

    def _get_random_filter_preset(self) -> str:
        """!
        @brief Получение случайного пресета фильтра
        
        @return str Название пресета фильтра
        """
        return random.choice(list(FilterPresetsType)).value

    def _create_voice_for_character(self, character_id: int, gender: str) -> None:
        """!
        @brief Создание голоса для персонажа
        
        @param character_id ID персонажа
        @param gender Пол персонажа
        """
        voice_name = self._get_random_voice(gender)
        pitch_shift = self._get_random_pitch_shift()
        filter_preset = self._get_random_filter_preset()
        
        self.db.save_character_voice(character_id, voice_name, pitch_shift, filter_preset)

    def _concatenate_audio_files(self, audio_files: List[str], output_path: str) -> None:
        """!
        @brief Объединение аудиофайлов в один
        
        @param audio_files Список путей к аудиофайлам
        @param output_path Путь для сохранения объединенного файла
        """
        if not audio_files:
            return
            
        # Загружаем первый файл
        combined = AudioSegment.from_mp3(audio_files[0])
        
        # Добавляем остальные файлы
        for audio_file in audio_files[1:]:
            segment = AudioSegment.from_mp3(audio_file)
            combined += segment
        
        # Экспортируем результат
        combined.export(output_path, format="mp3")

    def process_actor_message(self, sequence_number: int) -> str:
        """!
        @brief Обработка сообщения актера и создание аудиофайла
        
        @param sequence_number Порядковый номер сообщения
        
        @return str Путь к созданному аудиофайлу
        """
        # Получаем сегменты диалога
        segments = self.dialogue_processor.process_message(sequence_number)
        
        # Создаем временную директорию для отдельных аудиофайлов
        temp_dir = os.path.join(self.session_audio_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        audio_files = []
        
        # Обрабатываем каждый сегмент
        for i, (speaker, text) in enumerate(segments):
            if speaker == "GM":
                voice_settings = self.GM_VOICE_SETTINGS[self.language]
                voice_name = voice_settings['voice_name']
                pitch_shift = voice_settings['pitch_shift']
                filter_preset = voice_settings['filter_preset']
            else:
                character_id = self.db.get_character_id(self.session_id, speaker)
                if character_id:
                    voice_settings = self.db.get_character_voice(character_id)
                    if not voice_settings:
                        # Получаем пол персонажа из базы данных
                        _, _, gender = self.db.get_character(character_id)
                        self._create_voice_for_character(character_id, gender)
                        filter_preset = FilterPresetsType(int(filter_preset))
                    voice_name, pitch_shift, filter_preset = self.db.get_character_voice(character_id)

            temp_audio_path = os.path.join(temp_dir, f"segment_{i}.mp3")
            
            self.tts.synthesize_text(
                text=text,
                output_file=temp_audio_path,
                voice_name=voice_name,
                pitch_shift=pitch_shift,
                filter_preset=filter_preset
            )
            audio_files.append(temp_audio_path)
        
        # Создаем путь для финального аудиофайла
        final_audio_path = os.path.join(self.session_audio_dir, f"{sequence_number}.mp3")
        
        # Объединяем все аудиофайлы
        self._concatenate_audio_files(audio_files, final_audio_path)
        
        # Удаляем временные файлы
        for audio_file in audio_files:
            os.remove(audio_file)
        os.rmdir(temp_dir)
        
        return final_audio_path 