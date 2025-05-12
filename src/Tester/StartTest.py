#!/usr/bin/env python3
from typing import Optional, Tuple
from src.SessionManager.SessionManager import SessionManager
from src.GamePresets.GamePresets import GamePresets, GameWorld, GameCharacter
from src.Tester.Tester import Tester
from src.GameManager.GameManager import GameManager
from src.DatabaseManager.DatabaseManager import DatabaseManager
from src.NaiveModel.NaiveModel import NaiveModel

# Параметры теста
TEST_PARAMETERS = {
    'iterations': 50,           # Количество итераций диалога
    'world': GameWorld.FANTASY,        # Игровой мир
    'character': GameCharacter.mercenary,  # Персонаж
    'language': 'Russian',     # Язык диалога
    'generate_images': True,   # Генерация изображений
    'generate_sound': True,    # Генерация звука
    'use_naive_model': False   # Использовать наивную модель вместо GameManager
}

def run_test(session_id: int, iterations: int, generate_images: bool, generate_sound: bool, use_naive_model: bool) -> None:
    """!
    @brief Запуск теста диалога
    
    @param session_id ID сессии
    @param iterations Количество итераций
    @param generate_images Флаг генерации изображений
    @param generate_sound Флаг генерации звука
    @param use_naive_model Флаг использования наивной модели вместо GameManager
    """
    # Создаем тестер и менеджер игры
    tester = Tester(session_id)
    game_manager = GameManager(session_id) if not use_naive_model else None
    naive_model = NaiveModel(session_id) if use_naive_model else None
    
    print("\nStarting test session...")
    print("="*50)
    print(f"Using {'naive model' if use_naive_model else 'GameManager'} for response processing")
    print("="*50)
    
    # Получаем начальное сообщение из базы данных
    session_info = DatabaseManager().get_session_info(session_id)
    if session_info is None:
        raise ValueError(f"Session {session_id} not found")
    
    _, _, language, initial_message, _ = session_info
    
    # Отправляем начальное сообщение
    print(f"\nInitial message ({language}):")
    print(initial_message)
    print("-"*30)
    
    # Генерируем ответ на начальное сообщение
    response = tester.get_actor_response(initial_message)
    print("\nModel response:")
    print(response)
    print("-"*30)
    
    # Основной цикл теста
    for i in range(iterations):
        print(f"\nIteration {i+1}/{iterations}")
        
        # Обрабатываем ответ модели
        if use_naive_model:
            narrative_response, _ = naive_model.generate_response(response)
        else:
            narrative_response, _, _ = game_manager.process_input(response, generate_images, generate_sound)
        
        print("\nNarrative response:")
        print(narrative_response)
        
        response = tester.get_actor_response(narrative_response)
        print("\nModel response:")
        print(response)
        print("-"*30)
    
    print("\nTest completed!")
    print("="*50)


def main() -> None:
    """!
    @brief Основная функция
    """
    try:
        # Создаем менеджер сессий
        
        
        # Создаем тестовую сессию
        session_id = SessionManager().create_session_by_preset(1,
            TEST_PARAMETERS['world'],
            TEST_PARAMETERS['character'],
            TEST_PARAMETERS['language']
        )
        
        # Запускаем тест
        run_test(
            session_id,
            TEST_PARAMETERS['iterations'],
            TEST_PARAMETERS['generate_images'],
            TEST_PARAMETERS['generate_sound'],
            TEST_PARAMETERS['use_naive_model']
        )
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
        raise


if __name__ == "__main__":
    main() 