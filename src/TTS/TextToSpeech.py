import os
from google.cloud import texttospeech
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any, List, Tuple
from pedalboard import Pedalboard, PitchShift, Distortion, Clipping, LadderFilter
from pedalboard.io import AudioFile
import numpy as np
from src.TTS.FilterPresetsType import FilterPresetsType
from src.TTS.FilterPresets import FilterPresets

class TextToSpeech:
    """!
    @brief Класс для преобразования текста в речь с использованием Google Cloud Text-to-Speech API
    
    @details
    Использует Google Cloud Text-to-Speech API для синтеза речи из текста.
    Поддерживает различные голоса и языки.
    """
    
    def __init__(self):
        """!
        @brief Инициализация клиента Text-to-Speech
        """
        load_dotenv()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key.json"

        self.client = texttospeech.TextToSpeechClient()
        self.voice_presets: Dict[str, Dict[str, Any]] = {}  # Хранение пресетов голосов
        
        # Инициализация пресетов фильтров
        self.filter_presets = FilterPresets.get_presets()
        
    def synthesize_text(self, text: str, output_file: str, voice_name: str = "ru-RU-Chirp3-HD-Orus", 
                        pitch_shift: Optional[float] = None,
                        filter_preset: FilterPresetsType = FilterPresetsType.NONE) -> bool:
        """!
        @brief Преобразование текста в речь и сохранение в файл
        
        @param text Текст для преобразования в речь
        @param output_file Путь для сохранения аудиофайла
        @param voice_name Имя голоса 
        @param pitch_shift Сдвиг высоты тона в полутонах (отрицательные значения - ниже, положительные - выше)
        @param filter_preset Пресет фильтра для постобработки
        
        @return bool True если успешно, False в случае ошибки
        """
        try:
            # Проверяем входные параметры
            if not text or not text.strip():
                logging.error("Текст для синтеза не может быть пустым")
                return False
                
            if not output_file:
                logging.error("Не указан путь для сохранения файла")
                return False
            
            # Извлекаем код языка из имени голоса (например, ru-RU из ru-RU-Standard-A)
            language_code = voice_name.split('-')[:2]
            if len(language_code) < 2:
                logging.error(f"Некорректное имя голоса: {voice_name}")
                return False
            language_code = f"{language_code[0]}-{language_code[1]}"
            
            # Настройка параметров синтеза
            try:
                voice = texttospeech.VoiceSelectionParams(
                    language_code=language_code,
                    name=voice_name
                )
            except Exception as e:
                logging.error(f"Ошибка при настройке параметров голоса: {str(e)}")
                return False
            
            # Настройка параметров аудио
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            try:
                response = self.client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
            except Exception as e:
                logging.error(f"Ошибка при синтезе речи: {str(e)}")
                return False
            
            # Сохранение аудио во временный файл
            temp_file = output_file
            try:
                with open(temp_file, "wb") as out:
                    out.write(response.audio_content)
                logging.info(f"Аудио успешно сохранено во временный файл {temp_file}")
            except Exception as e:
                logging.error(f"Ошибка при сохранении временного аудио файла: {str(e)}")
                return False
            
            # Применяем постобработку
            try:
                self._apply_post_processing(
                    temp_file, 
                    output_file,
                    pitch_shift,
                    filter_preset
                )
                logging.info(f"Постобработка успешно применена, результат сохранен в {output_file}")
            except Exception as e:
                logging.error(f"Ошибка при постобработке аудио: {str(e)}")
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Неожиданная ошибка при синтезе речи: {str(e)}")
            return False
    
    def _apply_post_processing(self, input_file: str, output_file: str, 
                              pitch_shift: Optional[float] = None,
                              filter_preset: FilterPresetsType = FilterPresetsType.NONE
                              ) -> None:
        """!
        @brief Применение постобработки к аудиофайлу
        
        @param input_file Путь к входному аудиофайлу
        @param output_file Путь для сохранения обработанного аудиофайла
        @param pitch_shift Сдвиг высоты тона в полутонах
        @param filter_preset Пресет фильтра для постобработки
        @param distortion_amount Количество искажений
        """
        # Загрузка аудио
        with AudioFile(input_file, 'r') as f:
            audio = f.read(f.frames)
            sr = f.samplerate
        
        # Создание цепочки эффектов
        effects = []
        
        # Добавляем эффекты только если указаны соответствующие параметры
        if pitch_shift is not None:
            effects.append(PitchShift(semitones=pitch_shift))
        
        # Применяем фильтр на основе пресета
        if filter_preset != FilterPresetsType.NONE and filter_preset in self.filter_presets:
            preset = self.filter_presets[filter_preset]
            effects.append(LadderFilter(
                mode=preset['mode'],
                cutoff_hz=preset['cutoff_hz'],
                resonance=preset['resonance'],
                drive=preset['drive']
            ))
        
        
        # Если есть эффекты, применяем их
        if effects:
            board = Pedalboard(effects)
            processed = board.process(audio, sr)
            
            # Сохранение результата
            with AudioFile(output_file, 'w', sr, processed.shape[0]) as f:
                f.write(processed)
        else:
            # Если эффекты не указаны, просто копируем файл
            with AudioFile(input_file, 'r') as f_in:
                with AudioFile(output_file, 'w', f_in.samplerate, f_in.frames) as f_out:
                    f_out.write(f_in.read(f_in.frames))

    def get_available_voices(self) -> Dict[str, Dict[str, List[str]]]:
        """!
        @brief Получение списка доступных голосов
        
        @return Dict[str, Dict[str, List[str]]] Словарь с доступными голосами в формате:
            {
                "en": {
                    "male": ["en-US-1", "en-US-2", ...],
                    "female": ["en-US-4", "en-US-5", ...]
                },
                "ru": {
                    "male": ["ru-RU-1", "ru-RU-2", ...],
                    "female": ["ru-RU-4", "ru-RU-5", ...]
                }
            }
        """
        try:
            # Получаем список всех доступных голосов
            response = self.client.list_voices()
            
            # Словарь для хранения голосов по языкам и полу
            voices: Dict[str, Dict[str, List[str]]] = {
                "en": {"male": [], "female": []},
                "ru": {"male": [], "female": []}
            }
            available_languages = set(['ru-RU','en-US'])
            
            # Обрабатываем каждый голос
            for voice in response.voices:
                # Проверяем, что голос поддерживает синтез речи
                if not voice.ssml_gender:
                    continue
                if voice.language_codes[0] not in available_languages:
                    continue

                # Получаем код языка и пол
                language_code = voice.language_codes[0][:2]
                gender = "male" if voice.ssml_gender == texttospeech.SsmlVoiceGender.MALE else "female"
                if len(voices[language_code][gender]) > 20:
                    continue
                voices[language_code][gender].append(voice.name)
                
            return voices
            
        except Exception as e:
            logging.error(f"Error getting available voices: {str(e)}")
            return {
                "en": {"male": [], "female": []},
                "ru": {"male": [], "female": []}
            }


