import sqlite3
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from src.config import DATABASE_NAME
import logging
from sqlalchemy import text

class DatabaseManager:
    """!
    @brief Менеджер базы данных для управления игровыми сессиями
    
    @details
    Реализует паттерн Singleton для обеспечения единой точки доступа к базе данных.
    Управляет всеми операциями с базой данных, включая:
    - Пользователей и их сессии
    - Персонажей и их описания
    - Историю сообщений и диалогов
    - Промпты для генерации контента
    - Изображения и их промпты
    
    @note Класс использует SQLite в качестве системы управления базами данных
    """
    _instance = None
    db_path: str

    def __new__(cls) -> 'DatabaseManager':
        """!
        @brief Реализация паттерна Singleton
        
        @return DatabaseManager Единственный экземпляр класса
        """
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.db_path = DATABASE_NAME
            cls._instance._init_database()
        return cls._instance

    def __init__(self) -> None:
        """!
        @brief Инициализация атрибутов экземпляра
        
        @details
        Устанавливает путь к базе данных и инициализирует структуру базы данных
        """
        self.db_path = DATABASE_NAME
        self._init_database()

    def _init_database(self) -> None:
        """!
        @brief Инициализация структуры базы данных
        
        @details
        Создает все необходимые таблицы, если они не существуют:
        - users: информация о пользователях
        - sessions: игровые сессии
        - characters: персонажи
        - character_voices: настройки голоса персонажей
        - active_characters: активные персонажи в сессии
        - user_messages: история сообщений пользователя
        - master_messages: история сообщений мастера игры
        - actor_messages: история сообщений актора
        - game_master_prompts: промпты для мастера игры
        - actor_prompts: промпты для актора
        - image_prompts: промпты для генерации изображений
        - dialogue_prompts: промпты для обработки диалогов
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT
                )
            ''')
            
            # Create sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    world_description TEXT,
                    player_description TEXT,
                    language TEXT,
                    initial_message TEXT,
                    initial_message_eng TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Create characters table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS characters (
                    character_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    name TEXT,
                    description TEXT,
                    gender TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')

            # Create character voices table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS character_voices (
                    character_id INTEGER PRIMARY KEY,
                    voice_name TEXT NOT NULL,
                    pitch_shift REAL NOT NULL,
                    filter_preset TEXT NOT NULL,
                    FOREIGN KEY (character_id) REFERENCES characters(character_id)
                )
            ''')

            # Create active characters table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS active_characters (
                    session_id INTEGER,
                    sequence_number INTEGER,
                    character_id INTEGER,
                    PRIMARY KEY (session_id, sequence_number, character_id),
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                    FOREIGN KEY (character_id) REFERENCES characters(character_id)
                )
            ''')

            # Create user dialog history table (what user sees)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    sequence_number INTEGER,
                    user_input TEXT,
                    response TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')

            # Create game master history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS master_messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    sequence_number INTEGER,
                    user_input TEXT,
                    master_output TEXT,
                    actor_output TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')

            # Create actor history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS actor_messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    sequence_number INTEGER,
                    master_prompt TEXT,
                    actor_response TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')

            # Create game master prompts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_master_prompts (
                    prompt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    prompt_type TEXT,
                    prompt_content TEXT,
                    model_response TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')

            # Create actor prompts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS actor_prompts (
                    prompt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    prompt_content TEXT,
                    model_response TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')

            # Create image prompts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS image_prompts (
                    prompt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    sequence_number INTEGER,
                    user_input TEXT,
                    narrative_response TEXT,
                    image_prompt TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')
            
            # Create dialogue prompts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dialogue_prompts (
                    prompt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    sequence_number INTEGER,
                    prompt_content TEXT,
                    model_response TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                    FOREIGN KEY (sequence_number) REFERENCES user_messages(sequence_number)
                )
            ''')
            
            conn.commit()

    def create_user(self) -> int:
        """!
        @brief Создание нового пользователя
        
        @return int ID созданного пользователя
        
        @throws RuntimeError если не удалось создать пользователя
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users DEFAULT VALUES')
            conn.commit()
            result = cursor.lastrowid
            if result is None:
                raise RuntimeError("Failed to create user: no ID returned")
            return result

    def get_all_users(self) -> List[int]:
        """!
        @brief Получение списка всех пользователей
        
        @return List[int] Список ID всех пользователей
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users')
            return [row[0] for row in cursor.fetchall()]

    def create_session(self, user_id: int, world_description: str, player_description: str, language: str = "Russian", initial_message: str = "", initial_message_eng: str = "") -> int:
        """!
        @brief Создание новой игровой сессии
        
        @param user_id ID пользователя
        @param world_description Описание игрового мира
        @param player_description Описание игрока
        @param language Язык сессии (Russian/English)
        @param initial_message Начальное сообщение персонажа на языке сессии
        @param initial_message_eng Начальное сообщение персонажа на английском
        
        @return int ID созданной сессии
        
        @throws ValueError если указан неподдерживаемый язык
        @throws RuntimeError если не удалось создать сессию
        """
        if language not in ["Russian", "English"]:
            raise ValueError(f"Неподдерживаемый язык: {language}. Поддерживаемые языки: Russian, English")
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions (user_id, world_description, player_description, language, initial_message, initial_message_eng)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, world_description, player_description, language, initial_message, initial_message_eng))
            conn.commit()
            result = cursor.lastrowid
            if result is None:
                raise RuntimeError("Failed to create session: no ID returned")
            return result

    def get_user_sessions(self, user_id: int) -> List[Tuple[int, str, str, str]]:
        """!
        @brief Получение списка сессий пользователя
        
        @param user_id ID пользователя
        
        @return List[Tuple[int, str, str, str]] Список кортежей (session_id, created_at, world_description, player_description)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT session_id, created_at, world_description, player_description
                FROM sessions WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
            return cursor.fetchall()

    def get_session_info(self, session_id: int) -> Tuple[str, str, str, str, str]:
        """!
        @brief Получение информации о сессии
        
        @param session_id ID сессии
        
        @return Tuple[str, str, str, str, str] Кортеж из:
            - Описание игрового мира
            - Описание игрока
            - Язык сессии
            - Начальное сообщение персонажа на языке сессии
            - Начальное сообщение персонажа на английском
            
        @throws RuntimeError если сессия не найдена
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT world_description, player_description, language, initial_message, initial_message_eng 
                FROM sessions WHERE session_id = ?
            ''', (session_id,))
            result = cursor.fetchone()
            if result is None:
                raise RuntimeError(f"Session {session_id} not found")
            return result

    def save_character(self, session_id: int, name: str, description: str, gender: str) -> None:
        """!
        @brief Сохранение персонажа
        
        @param session_id ID сессии
        @param name Имя персонажа
        @param description Описание персонажа
        @param gender Пол персонажа
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO characters (session_id, name, description, gender)
                VALUES (?, ?, ?, ?)
            ''', (session_id, name, description, gender))
            conn.commit()

    def get_characters(self, session_id: int) -> List[Tuple[str, str, str]]:
        """!
        @brief Получение списка персонажей сессии
        
        @param session_id ID сессии
        
        @return List[Tuple[str, str, str]] Список кортежей (name, description, gender)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT name, description, gender FROM characters 
                WHERE session_id = ?
            ''', (session_id,))
            return cursor.fetchall()

    def save_user_message(self, session_id: int, user_input: str, response: str) -> None:
        """!
        @brief Сохранение сообщения пользователя
        
        @param session_id ID сессии
        @param user_input Ввод пользователя
        @param response Ответ системы
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COALESCE(MAX(sequence_number), 0) FROM user_messages 
                WHERE session_id = ?
            ''', (session_id,))
            next_seq = cursor.fetchone()[0] + 1
            
            cursor.execute('''
                INSERT INTO user_messages (session_id, sequence_number, user_input, response)
                VALUES (?, ?, ?, ?)
            ''', (session_id, next_seq, user_input, response))
            conn.commit()

    def save_master_message(self, session_id: int, user_input: str, master_output: str, actor_output: str) -> None:
        """!
        @brief Сохранение сообщения мастера игры
        
        @param session_id ID сессии
        @param user_input Ввод пользователя
        @param master_output Вывод мастера игры
        @param actor_output Вывод актора
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COALESCE(MAX(sequence_number), 0) FROM master_messages 
                WHERE session_id = ?
            ''', (session_id,))
            next_seq = cursor.fetchone()[0] + 1
            
            cursor.execute('''
                INSERT INTO master_messages (session_id, sequence_number, user_input, master_output, actor_output)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, next_seq, user_input, master_output, actor_output))
            conn.commit()

    def save_actor_message(self, session_id: int, master_prompt: str, actor_response: str) -> None:
        """!
        @brief Сохранение сообщения актора
        
        @param session_id ID сессии
        @param master_prompt Промпт мастера игры
        @param actor_response Ответ актора
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COALESCE(MAX(sequence_number), 0) FROM actor_messages 
                WHERE session_id = ?
            ''', (session_id,))
            next_seq = cursor.fetchone()[0] + 1
            
            cursor.execute('''
                INSERT INTO actor_messages (session_id, sequence_number, master_prompt, actor_response)
                VALUES (?, ?, ?, ?)
            ''', (session_id, next_seq, master_prompt, actor_response))
            conn.commit()

    def get_user_messages(self, session_id: int) -> List[Tuple[int, str, str]]:
        """!
        @brief Получение истории сообщений пользователя
        
        @param session_id ID сессии
        
        @return List[Tuple[int, str, str]] Список кортежей (sequence_number, user_input, response)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sequence_number, user_input, response 
                FROM user_messages 
                WHERE session_id = ?
                ORDER BY sequence_number
            ''', (session_id,))
            return cursor.fetchall()

    def get_master_messages(self, session_id: int) -> List[Tuple[int, str, str, str]]:
        """!
        @brief Получение истории сообщений мастера игры
        
        @param session_id ID сессии
        
        @return List[Tuple[int, str, str, str]] Список кортежей (sequence_number, user_input, master_output, actor_output)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sequence_number, user_input, master_output, actor_output 
                FROM master_messages 
                WHERE session_id = ?
                ORDER BY sequence_number
            ''', (session_id,))
            return cursor.fetchall()

    def get_actor_messages(self, session_id: int) -> List[Tuple[int, str, str]]:
        """!
        @brief Получение истории сообщений актора
        
        @param session_id ID сессии
        
        @return List[Tuple[int, str, str]] Список кортежей (sequence_number, master_prompt, actor_response)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sequence_number, master_prompt, actor_response 
                FROM actor_messages 
                WHERE session_id = ?
                ORDER BY sequence_number
            ''', (session_id,))
            return cursor.fetchall()

    def delete_session(self, session_id: int) -> None:
        """!
        @brief Удаление сессии и всех связанных с ней данных
        
        @param session_id ID сессии
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
            cursor.execute('DELETE FROM characters WHERE session_id = ?', (session_id,))
            cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
            conn.commit()

    def delete_user_data(self, user_id: int) -> None:
        """!
        @brief Удаление всех данных пользователя
        
        @param user_id ID пользователя
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Get all sessions for this user
            cursor.execute('SELECT session_id FROM sessions WHERE user_id = ?', (user_id,))
            sessions = cursor.fetchall()
            for (session_id,) in sessions:
                self.delete_session(session_id)
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            conn.commit()

    def save_game_master_prompt(self, session_id: int, prompt_type: str, prompt_content: str, model_response: str) -> None:
        """!
        @brief Сохранение промпта мастера игры
        
        @param session_id ID сессии
        @param prompt_type Тип промпта
        @param prompt_content Содержимое промпта
        @param model_response Ответ модели
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO game_master_prompts (session_id, prompt_type, prompt_content, model_response)
                VALUES (?, ?, ?, ?)
            ''', (session_id, prompt_type, prompt_content, model_response))
            conn.commit()

    def save_actor_prompt(self, session_id: int, prompt_content: str, model_response: str) -> None:
        """!
        @brief Сохранение промпта актора
        
        @param session_id ID сессии
        @param prompt_content Содержимое промпта
        @param model_response Ответ модели
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO actor_prompts (session_id, prompt_content, model_response)
                VALUES (?, ?, ?)
            ''', (session_id, prompt_content, model_response))
            conn.commit()

    def get_game_master_prompts(self, session_id: int) -> List[Tuple[str, str, str]]:
        """!
        @brief Получение промптов мастера игры
        
        @param session_id ID сессии
        
        @return List[Tuple[str, str, str]] Список кортежей (prompt_type, prompt_content, model_response)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT prompt_type, prompt_content, model_response 
                FROM game_master_prompts 
                WHERE session_id = ?
                ORDER BY created_at
            ''', (session_id,))
            return cursor.fetchall()

    def get_actor_prompts(self, session_id: int) -> List[Tuple[str, str]]:
        """!
        @brief Получение промптов актора
        
        @param session_id ID сессии
        
        @return List[Tuple[str, str]] Список кортежей (prompt_content, model_response)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT prompt_content, model_response 
                FROM actor_prompts 
                WHERE session_id = ?
                ORDER BY created_at
            ''', (session_id,))
            return cursor.fetchall()

    def is_new_session_actor_prompt(self, session_id: int) -> bool:
        """!
        @brief Проверка, является ли сессия новой для промптов актора
        
        @param session_id ID сессии
        
        @return bool True если сессия новая, False если промпты уже существуют
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT EXISTS (
                    SELECT 1 FROM actor_prompts WHERE session_id = ?
                )
            ''', (session_id,))
            return not bool(cursor.fetchone()[0])

    def is_new_session_gm_prompt(self, session_id: int) -> bool:
        """!
        @brief Проверка, является ли сессия новой для промптов мастера игры
        
        @param session_id ID сессии
        
        @return bool True если сессия новая, False если промпты уже существуют
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT EXISTS (
                    SELECT 1 FROM game_master_prompts WHERE session_id = ?
                )
            ''', (session_id,))
            return not bool(cursor.fetchone()[0])

    def save_image_prompt(self, session_id: int, user_input: str, narrative_response: str, image_prompt: str) -> None:
        """!
        @brief Сохранение промпта для генерации изображения
        
        @param session_id ID сессии
        @param user_input Ввод пользователя
        @param narrative_response Нарративный ответ
        @param image_prompt Промпт для генерации изображения
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COALESCE(MAX(sequence_number), 0) FROM image_prompts 
                WHERE session_id = ?
            ''', (session_id,))
            next_seq = cursor.fetchone()[0] + 1
            
            cursor.execute('''
                INSERT INTO image_prompts (session_id, sequence_number, user_input, narrative_response, image_prompt)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, next_seq, user_input, narrative_response, image_prompt))
            conn.commit()

    def get_image_prompts(self, session_id: int) -> List[Tuple[int, str, str, str]]:
        """!
        @brief Получение промптов для генерации изображений
        
        @param session_id ID сессии
        
        @return List[Tuple[int, str, str, str]] Список кортежей (sequence_number, user_input, narrative_response, image_prompt)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sequence_number, user_input, narrative_response, image_prompt 
                FROM image_prompts 
                WHERE session_id = ?
                ORDER BY sequence_number
            ''', (session_id,))
            return cursor.fetchall()

    def save_active_characters(self, session_id: int, sequence_number: int, character_ids: List[int]) -> None:
        """!
        @brief Сохранение активных персонажей для конкретного номера последовательности в сессии
        
        @param session_id ID сессии
        @param sequence_number Номер последовательности промпта мастера
        @param character_ids Список ID персонажей, которые в данный момент активны
        
        @throws Exception если произошла ошибка при сохранении
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Delete existing active characters for this sequence
                cursor.execute(
                    "DELETE FROM active_characters WHERE session_id = ? AND sequence_number = ?",
                    (session_id, sequence_number)
                )
                # Insert new active characters
                for char_id in character_ids:
                    cursor.execute(
                        "INSERT INTO active_characters (session_id, sequence_number, character_id) VALUES (?, ?, ?)",
                        (session_id, sequence_number, char_id)
                    )
                conn.commit()
        except Exception as e:
            logging.error(f"Error saving active characters: {str(e)}")
            raise

    def get_active_characters(self, session_id: int, sequence_number: int) -> List[str]:
        """!
        @brief Получение списка активных персонажей для конкретного номера последовательности в сессии
        
        @param session_id ID сессии
        @param sequence_number Номер последовательности промпта мастера
        
        @return List[str] Список имен активных персонажей
        
        @throws Exception если произошла ошибка при получении данных
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT c.name 
                    FROM active_characters ac
                    JOIN characters c ON ac.character_id = c.character_id
                    WHERE ac.session_id = ? AND ac.sequence_number = ?
                ''', (session_id, sequence_number))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting active characters: {str(e)}")
            raise

    def update_active_characters(self, session_id: int, sequence_number: int, character_ids: List[int]) -> None:
        """!
        @brief Обновление списка активных персонажей для конкретного номера последовательности в сессии
        
        @param session_id ID сессии
        @param sequence_number Номер последовательности промпта мастера
        @param character_ids Список ID персонажей, которые в данный момент активны
        """
        self.save_active_characters(session_id, sequence_number, character_ids)

    def get_character(self, character_id: int) -> Optional[Tuple[str, str]]:
        """!
        @brief Получение информации о персонаже по ID
        
        @param character_id ID персонажа
        
        @return Optional[Tuple[str, str]] Кортеж (name, description) или None если персонаж не найден
        
        @throws Exception если произошла ошибка при получении данных
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name, description, gender FROM characters WHERE character_id = ?",
                    (character_id,)
                )
                result = cursor.fetchone()
                return result if result else None
        except Exception as e:
            logging.error(f"Error getting character: {str(e)}")
            raise

    def get_active_characters_ids(self, session_id: int, sequence_number: int) -> List[int]:
        """!
        @brief Получение ID активных персонажей для конкретного номера последовательности в сессии
        
        @param session_id ID сессии
        @param sequence_number Номер последовательности промпта мастера
        
        @return List[int] Список ID активных персонажей
        
        @throws Exception если произошла ошибка при получении данных
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT character_id 
                    FROM active_characters 
                    WHERE session_id = ? AND sequence_number = ?
                ''', (session_id, sequence_number))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting active character IDs: {str(e)}")
            raise

    def get_user_message(self, session_id: int, sequence: int) -> Optional[Tuple[str, str]]:
        """!
        @brief Получение конкретного сообщения пользователя по номеру последовательности
        
        @param session_id ID сессии
        @param sequence Номер последовательности сообщения
        
        @return Optional[Tuple[str, str]] Кортеж (user_input, response) или None если сообщение не найдено
        
        @throws Exception если произошла ошибка при получении данных
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_input, response 
                    FROM user_messages 
                    WHERE session_id = ? AND sequence_number = ?
                ''', (session_id, sequence))
                result = cursor.fetchone()
                return result if result else None
        except Exception as e:
            logging.error(f"Error getting user message: {str(e)}")
            raise

    def get_character_id(self, session_id: int, name: str) -> Optional[int]:
        """!
        @brief Получение ID персонажа по ID сессии и имени
        
        @param session_id ID сессии
        @param name Имя персонажа
        
        @return Optional[int] ID персонажа или None если персонаж не найден
        
        @throws Exception если произошла ошибка при получении данных
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT character_id FROM characters WHERE session_id = ? AND name = ?",
                    (session_id, name)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logging.error(f"Error getting character ID: {str(e)}")
            raise

    def get_session_language(self, session_id: int) -> str:
        """!
        @brief Получение языка сессии
        
        @param session_id ID сессии
        
        @return str Язык сессии (Russian/English)
        
        @throws RuntimeError если сессия не найдена
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT language FROM sessions WHERE session_id = ?
            ''', (session_id,))
            result = cursor.fetchone()
            if result is None:
                raise RuntimeError(f"Session {session_id} not found")
            return str(result[0])  # Ensure we return a string

    def save_dialogue_prompt(self, session_id: int, sequence_number: int, prompt_content: str, model_response: str) -> None:
        """!
        @brief Сохранение промпта для обработки диалогов
        
        @param session_id ID сессии
        @param sequence_number Порядковый номер сообщения
        @param prompt_content Содержимое промпта
        @param model_response Ответ модели
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO dialogue_prompts (session_id, sequence_number, prompt_content, model_response)
                VALUES (?, ?, ?, ?)
            ''', (session_id, sequence_number, prompt_content, model_response))
            conn.commit()

    def get_dialogue_prompts(self, session_id: int) -> List[Tuple[int, str, str]]:
        """!
        @brief Получение промптов для обработки диалогов
        
        @param session_id ID сессии
        
        @return List[Tuple[int, str, str]] Список кортежей (sequence_number, prompt_content, model_response)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sequence_number, prompt_content, model_response 
                FROM dialogue_prompts 
                WHERE session_id = ?
                ORDER BY created_at
            ''', (session_id,))
            return cursor.fetchall()

    def save_character_voice(self, character_id: int, voice_name: str, pitch_shift: float, filter_preset: str) -> None:
        """!
        @brief Сохранение настроек голоса персонажа
        
        @param character_id ID персонажа
        @param voice_name Название голоса
        @param pitch_shift Смещение высоты голоса
        @param filter_preset Название пресета фильтра
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO character_voices (character_id, voice_name, pitch_shift, filter_preset)
                VALUES (?, ?, ?, ?)
            ''', (character_id, voice_name, pitch_shift, filter_preset))
            conn.commit()

    def get_character_voice(self, character_id: int) -> Optional[Tuple[str, float, str]]:
        """!
        @brief Получение настроек голоса персонажа
        
        @param character_id ID персонажа
        
        @return Optional[Tuple[str, float, str]] Кортеж (voice_name, pitch_shift, filter_preset) или None если настройки не найдены
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT voice_name, pitch_shift, filter_preset 
                FROM character_voices 
                WHERE character_id = ?
            ''', (character_id,))
            result = cursor.fetchone()
            return result if result else None

    def get_characters_with_voices(self, session_id: int) -> List[Tuple[str, str, str, Optional[Tuple[str, float, str]]]]:
        """!
        @brief Получение списка персонажей с их настройками голоса
        
        @param session_id ID сессии
        
        @return List[Tuple[str, str, str, Optional[Tuple[str, float, str]]]] 
            Список кортежей (name, description, gender, voice_settings)
            где voice_settings это (voice_name, pitch_shift, filter_preset) или None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.name, c.description, c.gender, cv.voice_name, cv.pitch_shift, cv.filter_preset
                FROM characters c
                LEFT JOIN character_voices cv ON c.character_id = cv.character_id
                WHERE c.session_id = ?
            ''', (session_id,))
            results = []
            for row in cursor.fetchall():
                name, description, gender = row[0:3]
                voice_settings = row[3:6] if row[3] is not None else None
                results.append((name, description, gender, voice_settings))
            return results