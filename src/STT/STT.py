import speech_recognition as sr  # type: ignore
from typing import Optional, Dict
import numpy as np
from pydub import AudioSegment  # type: ignore
import os


class STT:
    """!
    @brief Класс для распознавания речи (Speech-to-Text)
    
    @details
    Реализует паттерн Singleton для обеспечения единой точки доступа
    к функционалу распознавания речи. Использует библиотеку speech_recognition
    для преобразования аудио в текст.
    
    @note Поддерживает русский и английский языки для распознавания
    """
    __instance: Optional['STT'] = None
    __recognizer: Optional[sr.Recognizer] = None
    __silence_duration_ms: int = 2000  # 2 секунды тишины в начале
    __energy_threshold: float = 300  # Порог энергии для определения речи
    __pause_threshold: float = 0.8  # Порог паузы между словами
    __dynamic_energy_threshold: bool = True  # Динамическая настройка порога энергии
    
    # Словарь соответствия языков и их кодов
    __language_codes: Dict[str, str] = {
        "Russian": "ru-RU",
        "English": "en-US",
        "ru-RU": "ru-RU",
        "en-US": "en-US"
    }
    
    # Текущий язык распознавания
    __current_language: str = "Russian"

    def __new__(cls) -> 'STT':
        """!
        @brief Создание единственного экземпляра класса
        
        @return STT Единственный экземпляр класса STT
        """
        if cls.__instance is None:
            cls.__instance = super(STT, cls).__new__(cls)
            cls.__recognizer = sr.Recognizer()
        return cls.__instance

    def __init__(self) -> None:
        """!
        @brief Инициализация распознавателя речи
        
        @note Метод выполняется только при первом создании экземпляра
        """
        if self.__recognizer is None:
            self.__recognizer = sr.Recognizer()
            # Настройка параметров распознавателя
            self.__recognizer.energy_threshold = self.__energy_threshold
            self.__recognizer.pause_threshold = self.__pause_threshold
            self.__recognizer.dynamic_energy_threshold = self.__dynamic_energy_threshold

    def set_language(self, language: str) -> None:
        """!
        @brief Установка языка распознавания
        
        @param language Язык для распознавания (Russian/English или ru-RU/en-US)
        
        @throws ValueError если указанный язык не поддерживается
        """
        if language not in self.__language_codes:
            raise ValueError(f"Неподдерживаемый язык: {language}. Поддерживаемые языки: {', '.join(self.__language_codes.keys())}")
        self.__current_language = language

    def get_language(self) -> str:
        """!
        @brief Получение текущего языка распознавания
        
        @return str Текущий язык распознавания
        """
        return self.__current_language

    def __add_silence_padding(self, audio_path: str) -> str:
        """!
        @brief Добавление тишины в начало аудиофайла
        
        @param audio_path Путь к исходному аудиофайлу
        
        @return str Путь к новому аудиофайлу с добавленной тишиной
        """
        try:
            # Загрузка аудиофайла
            audio = AudioSegment.from_file(audio_path)
            
            # Создание тишины
            silence = AudioSegment.silent(duration=self.__silence_duration_ms)
            
            # Добавление тишины в начало
            audio_with_silence = silence + audio
            
            # Создание временного файла
            temp_path = audio_path.replace('.wav', '_with_silence.wav')
            audio_with_silence.export(temp_path, format="wav")
            
            return temp_path
        except Exception as e:
            print(f"Ошибка при добавлении тишины: {str(e)}")
            return audio_path

    def __cleanup_temp_file(self, temp_path: str) -> None:
        """!
        @brief Удаление временного файла
        
        @param temp_path Путь к временному файлу
        """
        try:
            if os.path.exists(temp_path) and '_with_silence.wav' in temp_path:
                os.remove(temp_path)
        except Exception as e:
            print(f"Ошибка при удалении временного файла: {str(e)}")

    def audio_to_text(self, audio_path: str) -> str:
        """!
        @brief Преобразование аудиофайла в текст
        
        @param audio_path Путь к аудиофайлу для распознавания
        
        @return str Распознанный текст или сообщение об ошибке
        
        @throws sr.UnknownValueError если речь не может быть распознана
        @throws sr.RequestError если возникла ошибка при подключении к API
        """
        temp_path = None
        try:
            # Добавляем тишину в начало файла
            temp_path = self.__add_silence_padding(audio_path)
            
            if self.__recognizer is None:
                return "Ошибка: распознаватель речи не инициализирован"
                
            with sr.AudioFile(temp_path) as source:
                # Настройка распознавателя для уменьшения шума
                self.__recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = self.__recognizer.record(source)
                
                # Получаем код языка для Google Speech Recognition
                language_code = self.__language_codes[self.__current_language]
                
                # Сначала пробуем использовать Google Speech Recognition
                try:
                    text = self.__recognizer.recognize_google(audio_data, language=language_code)
                    return str(text)
                except (sr.UnknownValueError, sr.RequestError):
                    # Если Google не сработал, пробуем Sphinx
                    try:
                        text = self.__recognizer.recognize_sphinx(audio_data, language=language_code)
                        return str(text)
                    except (sr.UnknownValueError, sr.RequestError):
                        return "Речь не распознана"
        except Exception as e:
            return f"Ошибка при обработке аудио: {str(e)}"
        finally:
            # Удаляем временный файл
            if temp_path:
                self.__cleanup_temp_file(temp_path)


# Пример использования
if __name__ == "__main__":
    stt = STT()
    
    # Установка языка (можно использовать "Russian"/"English" или "ru-RU"/"en-US")
    stt.set_language("Russian")
    
    for i in range(1, 5+1):
        audio_file = f"Audio/test/{i}.wav"
        result = stt.audio_to_text(audio_file)
        print(f"Файл {i}: {result}")