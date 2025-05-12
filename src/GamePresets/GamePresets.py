from enum import Enum, auto
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class WorldInfo:
    """!
    @brief Информация о игровом мире
    
    @details
    Содержит полное описание мира и список доступных персонажей
    """
    description: str
    short_description: str
    available_characters: List['GameCharacter']


@dataclass
class CharacterInfo:
    """!
    @brief Информация о персонаже
    
    @details
    Содержит полное описание персонажа, его краткую характеристику
    и начальные сообщения на разных языках
    """
    description: str
    short_description: str
    initial_messages: Dict[str, str]


class GameWorld(Enum):
    """!
    @brief Перечисление доступных игровых миров
    """
    FANTASY = auto()


class GameCharacter(Enum):
    """!
    @brief Перечисление доступных персонажей
    """
    # Fantasy characters
    mercenary = auto()
    archer = auto()


class GamePresets:
    """!
    @brief Класс для управления настройками игры
    
    @details
    Управляет доступными мирами и персонажами, их описаниями и взаимосвязями
    """
    __worlds: Dict[GameWorld, WorldInfo] = {
        GameWorld.FANTASY: WorldInfo(
            description='''
            Imagine a world where magic and chivalry coexist with the dangers of the wild and the intrigues of human kingdoms. In this world:

            Landscapes: Vast forests hiding ancient ruins and magical creatures; mountain ranges where dragons nest; endless fields and fertile valleys crossed by winding rivers. There are bustling ports scattered along the coasts, where cultures of different nations collide.
            Cities: Stone fortresses with high towers surrounded by wooden houses of artisans. The narrow streets are full of merchants, minstrels and secret agents. In the center are castles where monarchs and their court magicians rule.
            Society: Feudal structure – kings, vassals, knights and peasants. However, magicians, alchemists, and priests occupy a special place, sometimes surpassing the influence of aristocrats.
            Magic: The forces of nature obey the will of magicians. Magical artifacts are hidden in ancient ruins guarded by monsters. Spells require sacrifices or rare ingredients that desperate adventurers seek.
            Conflicts: Wars between kingdoms for resources and power, uprisings of oppressed peasants, the struggle of churches with magicians, ancient prophecies foreshadowing disasters.
            Creatures: Humans, elves, dwarves, orcs, and semi-fantastic races such as animal and human hybrids. Dangerous creatures such as griffins, minotaurs, hydra and forest spirits live in the wild.
            Technology: Based on the real Middle Ages, but with the addition of magic: enchanted weapons, flying ships, alchemical potions and magic clocks.
            Culture: Bard songs tell of heroic deeds, knight tournaments celebrate valor, and ancient legends warn of the dangers of greed and pride.
            
            The game starts in the city of Voltung.
            ''',
            short_description="Средневековое фентези",
            available_characters=[
                GameCharacter.mercenary,
                GameCharacter.archer
            ]
        )
    }

    __characters: Dict[GameCharacter, CharacterInfo] = {
        # Fantasy characters
        GameCharacter.mercenary: CharacterInfo(
            description= 
            '''
                A tall, burly warrior with short brown hair and cold blue-gray eyes. Roderick is a former knight who was exiled from the order for insubordination. He wears time–darkened armor with embossed traces of old battles, and always carries his trusty sword, the Bloody Dawn, enchanted to destroy magic.

                Character: cynical, but with his own code of honor. He despises liars and tyrants, although he is not averse to cunning to achieve the goal. He often grumbles, but protects the weak, even if he pretends that he doesn't care.

                Background: Born into a poor peasant family, he mastered the sword early and joined the service of the baron. After his shameful exile, he wanders, running dangerous errands in order to survive. His name is known as the "killer of monsters and magicians."''',
            short_description="Наемный мечник",
            initial_messages={
                "Russian": "Вы прибываете в город Волтунг, после провала последнего контракта у вас осталось, совсем мало денег, стоит поспрашивать о работе.",
                "English": "You arrive in the city of Voltung, after the failure of your last contract, you have very little money left, it's worth asking around for a job."
            }
        ),
        GameCharacter.archer: CharacterInfo(
            description='''
            Taylor – A lean, rugged hunter with windswept auburn hair and sharp, piercing green eyes. Once a skilled tracker for a noble house, he was cast out after refusing an unjust order. His attire is a mix of worn leather and faded forest greens, adorned with trophies from past hunts. Always at his side is Whisperwind.
            Character: Cynical yet principled, Taylor has little patience for deceit or oppression—though he's no stranger to trickery when the hunt demands it. Quick to complain but quicker to act, he pretends indifference yet never turns away from those in need.

            Background: Born in a remote village, Taylor learned the bow to feed his family before being recruited as a royal huntsman. After his exile, he roams as a freelance tracker, famed for feeling beasts and corrupt men alike. Some call him "the Ghost of the Wilds"—a name earned through unmatched aim and a habit of vanishing like mist.

            ''',
            short_description="Лучник, охотник",
            initial_messages={
                "Russian": "Вы прибываете в город Волтунг, в последнее время бог охоты не был к вам благосклонен и вы решили поискать работу в городе.",
                "English": "You arrive in the city of Voltung, recently the god of hunting has not been kind to you and you decided to look for a job in the city."
            }
        )
    }

    @classmethod
    def get_world_description(cls, world: GameWorld) -> str:
        """!
        @brief Получение полного описания мира
        
        @param world Игровой мир
        
        @return str Полное описание мира
        """
        return cls.__worlds[world].description

    @classmethod
    def get_world_short_description(cls, world: GameWorld) -> str:
        """!
        @brief Получение краткого описания мира
        
        @param world Игровой мир
        
        @return str Краткое описание мира
        """
        return cls.__worlds[world].short_description

    @classmethod
    def get_world_characters(cls, world: GameWorld) -> List[Tuple[GameCharacter, str]]:
        """!
        @brief Получение списка персонажей для мира с их краткими описаниями
        
        @param world Игровой мир
        
        @return List[Tuple[GameCharacter, str]] Список кортежей (персонаж, краткое описание)
        """
        return [(char, cls.__characters[char].short_description) 
                for char in cls.__worlds[world].available_characters]

    @classmethod
    def get_character_description(cls, character: GameCharacter) -> str:
        """!
        @brief Получение полного описания персонажа
        
        @param character Персонаж
        
        @return str Полное описание персонажа
        """
        return cls.__characters[character].description

    @classmethod
    def get_character_short_description(cls, character: GameCharacter) -> str:
        """!
        @brief Получение краткого описания персонажа
        
        @param character Персонаж
        
        @return str Краткое описание персонажа
        """
        return cls.__characters[character].short_description

    @classmethod
    def get_character_initial_message(cls, character: GameCharacter, language: str) -> str:
        """!
        @brief Получение начального сообщения персонажа на указанном языке
        
        @param character Персонаж
        @param language Язык сообщения ('Russian' или 'English')
        
        @return str Начальное сообщение персонажа
        """
        return cls.__characters[character].initial_messages.get(language, cls.__characters[character].initial_messages["English"])

    @classmethod
    def get_all_worlds(cls) -> List[Tuple[GameWorld, str]]:
        """!
        @brief Получение списка всех доступных миров с их краткими описаниями
        
        @return List[Tuple[GameWorld, str]] Список кортежей (мир, краткое описание)
        """
        return [(world, info.short_description) for world, info in cls.__worlds.items()]

    @classmethod
    def is_character_in_world(cls, character: GameCharacter, world: GameWorld) -> bool:
        """!
        @brief Проверка принадлежности персонажа к миру
        
        @param character Персонаж для проверки
        @param world Мир для проверки
        
        @return bool True если персонаж принадлежит миру, False в противном случае
        """
        return character in cls.__worlds[world].available_characters 