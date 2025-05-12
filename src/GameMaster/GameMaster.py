import time
from typing import Optional, Dict, List, Tuple, Set
from src.GameMaster.CommandData import CommandData, CommandDataEnvironmentDescription, CommandSelectCharacter, \
    CommandCreateCharacter, CommandOffTopic, CommandPlayerDeath
from src.MessageGenerator.BaseMessageGenerator import get_base_message_generator, RequesterClass
from src.Actor.ProtocolActor import ProtocolActor
from src.Actor.Actor import Actor
from src.MessageGenerator.ProtocolMessageGenerator import ProtocolMessageGenerator
from src.GameMaster.GameMasterPromts import start_message, world_description_start, correct_formatting, \
    character_name_start
from src.Descriptions.CharacterDecription import base_character_description
from src.Descriptions.WorldDecription import base_world_description
from src.DatabaseManager.DatabaseManager import DatabaseManager
from src.ImageManager.ImageManager import ImageManager
import logging

class PlayerDeathException(Exception):
    """!
    @brief Исключение, возникающее при смерти игрового персонажа
    
    @details
    Выбрасывается, когда игровой персонаж умирает, что приводит к завершению сессии
    и блокировке дальнейшего ввода.
    """
    pass


class GameMaster:
    """!
    @brief Класс, управляющий игровым процессом и взаимодействием с игроком
    
    @details
    Отвечает за:
    - Генерацию ответов на действия игрока
    - Управление игровыми персонажами
    - Поддержание целостности игрового мира
    - Генерацию изображений
    - Взаимодействие с базой данных
    
    """
    def __init__(self, session_id: int,
                 generate_character_images: bool = True) -> None:
        """!
        @brief Инициализация мастера игры
        
        @param session_id ID игровой сессии
        @param generate_character_images Флаг генерации изображений персонажей (опционально)
        """
        self.session_id = session_id
        self.db = DatabaseManager()
        self.generate_character_images = generate_character_images
        
        # Get session info from database
        session_info = self.db.get_session_info(session_id)
        if session_info is None:
            raise ValueError(f"Session {session_id} not found")
            
        self.world_description, self.player_description, self.language, self.initial_message, self.initial_message_eng = session_info

        self.messageGenerator: ProtocolMessageGenerator = get_base_message_generator(RequesterClass.GameMaster)
        self.characters: Dict[str, str] = {}  # name -> description
        self.__actor = Actor(self, session_id)
        self.__image_manager = ImageManager(session_id)

        logging.basicConfig(filename='game_master.log', level=logging.INFO,
                          format='%(asctime)s - %(message)s', filemode='a')

        formatted_character: str = \
            f'''
        {character_name_start}
        Description: {self.player_description}
        '''

        is_new_session = self.db.is_new_session_gm_prompt(session_id)
        
        if is_new_session:
            self.messageGenerator.add_system_message(start_message)
            response = "Understood"
            self.messageGenerator.add_ai_message(response)
            self.db.save_game_master_prompt(session_id, "start", start_message, response)
            
            # World description
            world_prompt = world_description_start + '\n' + self.world_description
            self.messageGenerator.add_user_message(world_prompt)
            response = "Understood"
            self.messageGenerator.add_system_message(response)
            self.db.save_game_master_prompt(session_id, "world", world_prompt, response)
            
            # Character description
            self.messageGenerator.add_user_message(formatted_character)
            response = "Understood"
            self.messageGenerator.add_system_message(response)
            self.db.save_game_master_prompt(session_id, "character", formatted_character, response)
        else:
            # For existing session, load prompts from database
            for prompt_type, prompt_content, model_response in self.db.get_game_master_prompts(session_id):
                self.messageGenerator.add_system_message(prompt_content)
                self.messageGenerator.add_ai_message(model_response)

        # Load existing characters from database
        for name, description, gender in self.db.get_characters(session_id):
            self.characters[name] = description

        # Load master message history
        master_history = self.db.get_master_messages(session_id)
        for _, user_input, master_output, actor_output in master_history:
            self.messageGenerator.add_user_message(user_input)
            self.messageGenerator.add_ai_message(master_output)
            self.messageGenerator.add_system_message(actor_output)

    def generate_answer(self, message: str) -> str:
        """!
        @brief Генерация ответа на сообщение игрока
        
        @param message Сообщение игрока
        
        @return str Ответ системы
        
        @throws PlayerDeathException если игровой персонаж умирает
        """
        # Get the structured output from game master
        rules = '''
        You also need to follow these rules.
            - You can't choose a player character in your teams.
            - With any command your answer should always be specific. For example, you can't write that you need to come to a certain person, it has to be a specific person. You can't offer an abstract artifact sword, it has to be a specific sword with specific properties. If it takes a little more words, it's not so critical.
            - If a player enters into a dialogue or performs an action, then he should get an answer, the other person should not just think or ignore it. Except in cases where he wants to ignore you for plot reasons, in which case you should indicate that he is clearly ignoring you intentionally and give a suggestion as to why this is happening.
            - Never describe what the player is doing, always react to the player's actions, especially if he asked someone a question, he should answer
            - Never write anything in the same line where you select a command, it will break the program.
            - Write the names of the commands exactly as they are written, including dots and other punctuation marks.
            - Never create a player character.
        '''
        commands, real_game_master_output = self.generate_instruction(message + '\n' + rules)
        game_master_output, active_character_names = self.parse_commands(commands)
        
        # Create active characters dictionary from the set of names
        active_characters = {name: self.characters[name] for name in active_character_names}
        self.__actor.update_active_characters(active_characters)
        
        # Generate narrative
        final_message = self.__actor.get_detailed_action(game_master_output, message)
        actor_message = f"Actor's output (What the user will see):\n{final_message}"
        
        self.messageGenerator.add_system_message(actor_message)

        # Save user and master messages
        self.db.save_user_message(self.session_id, message, final_message)
        self.db.save_master_message(self.session_id, message, real_game_master_output, actor_message)
        
        character_ids = []
        for name in active_characters:
            char_id = self.db.get_character_id(self.session_id, name)
            if char_id:
                character_ids.append(char_id)
        
        # Save active characters to DB
        image_prompts = self.db.get_image_prompts(self.session_id)
        sequence_number = len(image_prompts)
        self.db.save_active_characters(self.session_id, sequence_number, character_ids)
        
        return final_message

    def generate_instruction(self, message: str) -> Tuple[List[CommandData], str]:
        """!
        @brief Генерация инструкций на основе сообщения
        
        @param message Сообщение для обработки
        
        @return Tuple[List[CommandData], str] Кортеж из списка команд и текстового вывода
        
        @note Метод может выполнять повторные попытки генерации при некорректном формате
        """
        output: str = self.messageGenerator.generate(message)
        cnt_errore = 0
        parsed_data, error = self.validate_and_parse(output)
        while parsed_data is None:
            cnt_errore += 1
            if cnt_errore > 3:
                raise RuntimeError(f"Too many formatting errors: {error}")
            time.sleep(1)

            logging.info(f"\n\nOutput: {output}\nError: {error}")
            output = self.messageGenerator.generate(
                f"Incorrect formatting. Error: {error}. Repeat using the correct.\n{correct_formatting}")
            parsed_data, error = self.validate_and_parse(output)

        return parsed_data, output

    def validate_and_parse(self, input_text: str) -> Tuple[Optional[List[CommandData]], str]:
        """!
        @brief Валидация и парсинг входного текста
        
        @param input_text Текст для валидации и парсинга
        
        @return Tuple[Optional[List[CommandData]], str] Кортеж из списка команд (или None) и сообщения об ошибке
        """
        cleaned_text = "\n".join([line for line in input_text.splitlines() if line.strip()])
        lines = cleaned_text.strip().split("\n")
        i = 0
        parsed_data: List[CommandData] = []
        tmp_characters_names: List[str] = []
        def match_command(line: str, command: str) -> bool:
            return line.strip().lower() == command.lower() or line.strip().lower() == (command + ".").lower()
        while i < len(lines):
            line = lines[i].strip()

            if match_command(line, "Create character command"):
                if i + 3 >= len(lines):
                    return None, "Error: Incomplete 'Create a character command.'"
                name = lines[i + 1].strip()
                gender = lines[i + 2].strip().lower()
                if gender not in ['male', 'female']:
                    return None, f"Error: Invalid gender '{gender}'. Must be 'male' or 'female'."
                if name in self.characters or name in tmp_characters_names:
                    return None, f"Error: Character name '{name}' already exists."
                description = lines[i + 3].strip()

                parsed_data.append(CommandCreateCharacter(
                    name=name,
                    gender=gender,
                    description=description
                ))
                tmp_characters_names.append(name)
                i += 4

            elif match_command(line, "Select character command"):
                if i + 2 >= len(lines):
                    return None, "Error: Incomplete 'Select character command.'"
                name = lines[i + 1].strip()
                if name not in self.characters and name not in tmp_characters_names:
                    return None, f"Error: Character name '{name}' does not exist."
                action = lines[i + 2].strip()

                parsed_data.append(CommandSelectCharacter(
                    name=name,
                    action=action
                ))
                i += 3

            elif match_command(line, "Describe environment command"):
                if i + 1 >= len(lines):
                    return None, "Error: Incomplete 'The command to describe the environment.'"
                description = lines[i + 1].strip()

                parsed_data.append(CommandDataEnvironmentDescription(
                    description=description
                ))
                i += 2

            elif match_command(line, "Off-topic input command"):
                parsed_data.append(CommandOffTopic())
                i += 1

            elif match_command(line, "Player death command"):
                parsed_data.append(CommandPlayerDeath())
                i += 1

            else:
                return None, f"Error: Unrecognized command '{line}'"
        if len(parsed_data) == 0:
            return None, f"Error: No commands found."

        return parsed_data, "No errors found."

    def parse_commands(self, commands: List[CommandData]) -> Tuple[str, Set[str]]:
        """!
        @brief Обработка списка команд
        
        @param commands Список команд для обработки
        
        @return Tuple[str, Set[str]] Кортеж из текстового вывода и множества имен активных персонажей
        
        @throws PlayerDeathException если встречена команда смерти игрока
        """
        final_output = ""
        active_characters: Set[str] = set()
        for command in commands:
            if isinstance(command, CommandCreateCharacter):
                self.characters[command.name] = command.description
                self.db.save_character(self.session_id, command.name, command.description,command.gender)
                final_output += f"A new character appears: {command.name}. {command.description}\n"
                active_characters.add(command.name)
                
                # Generate character portrait if enabled
                if self.generate_character_images and self.__image_manager:
                    self.__image_manager.generate_character_portrait(command.name, command.description)
                
            elif isinstance(command, CommandSelectCharacter):
                final_output += f"{command.name}: {command.action}\n"
                active_characters.add(command.name)
            elif isinstance(command, CommandDataEnvironmentDescription):
                final_output += f"Environment: {command.description}\n"
            elif isinstance(command, CommandOffTopic):
                final_output = "Input is off-topic"
                break
            elif isinstance(command, CommandPlayerDeath):
                final_output += "The player character has died. The session has ended."
                raise PlayerDeathException("Player character has died. Session ended.")
                
        return final_output, active_characters
