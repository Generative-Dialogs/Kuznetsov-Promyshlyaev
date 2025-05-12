from dataclasses import dataclass
from typing import Optional

@dataclass
class CommandData:
    """!
    @brief Базовый класс для всех команд в игровой системе
    
    @details
    Используется как маркер для типизации команд и обеспечивает
    единый интерфейс для всех типов команд в системе.
    """
    pass

@dataclass
class CommandDataEnvironmentDescription(CommandData):
    """!
    @brief Команда для описания окружения
    
    @details
    Используется для генерации описания текущего окружения,
    в котором находятся персонажи.
    
    @param description Текстовое описание окружения
    """
    description: str

@dataclass
class CommandSelectCharacter(CommandData):
    """!
    @brief Команда выбора персонажа для действия
    
    @details
    Определяет, какой персонаж выполняет действие и
    какое именно действие он выполняет.
    
    @param name Имя персонажа
    @param action Описание действия
    """
    name: str
    action: str

@dataclass
class CommandCreateCharacter(CommandData):
    """!
    @brief Команда создания нового персонажа
    
    @details
    Используется для добавления нового персонажа в игру
    с заданным именем и описанием.
    
    @param name Имя нового персонажа
    @param gender Пол персонажа (male/female)
    @param description Описание нового персонажа
    """
    name: str
    gender: str
    description: str

@dataclass
class CommandOffTopic(CommandData):
    """!
    @brief Команда для обработки внеигрового ввода
    
    @details
    Используется, когда ввод пользователя не относится
    к игровому процессу или нарушает правила игры.
    """
    pass

@dataclass
class CommandPlayerDeath(CommandData):
    """!
    @brief Команда смерти игрового персонажа
    
    @details
    Используется для обработки ситуации, когда
    игровой персонаж умирает, что приводит к
    завершению игровой сессии.
    """
    pass 