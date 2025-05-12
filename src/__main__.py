#!/usr/bin/env python3
import os
import sys
import subprocess
from typing import Optional, Tuple
from src.DatabaseManager.DatabaseManager import DatabaseManager
from src.Descriptions.CharacterDecription import base_character_description
from src.Descriptions.WorldDecription import base_world_description
from src.ImagePromptGenerator.ImagePromptGenerator import ImagePromptGenerator
from src.ImageGenerator.ImageGeneratorGoogle import ImageGeneratorGoogle
from src.ImageManager.ImageManager import ImageManager
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.SessionManager.SessionManager import SessionManager
from src.Actor.Actor import Actor
from src.GameMaster.GameMaster import GameMaster
from src.GameManager.GameManager import GameManager


def run_mypy() -> None:
    result = subprocess.run(['python', '-m', 'mypy', '--show-error-codes', 'src/'], capture_output=True, text=True)
    if result.returncode != 0:
        print("Mypy check failed:")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)


def select_user(manager: SessionManager) -> int:
    while True:
        print("\nAvailable users:")
        users = manager.db.get_all_users()
        if users:
            print("Existing users:")
            for user_id in users:
                print(f"User ID: {user_id}")
        print("\nOptions:")
        print("a. Select existing user (enter user ID)")
        print("b. Create new user")
        choice = input("Your choice: ").strip()
        
        if choice == "b":
            return manager.create_user()
        elif choice.isdigit():
            user_id = int(choice)
            if user_id in users:
                return user_id
        print("Invalid choice. Please try again.")


def select_session(manager: SessionManager, user_id: int) -> Tuple[int, bool]:
    while True:
        sessions = manager.db.get_user_sessions(user_id)
        if sessions:
            print("\nExisting sessions:")
            for session_id, created_at, world_desc, player_desc in sessions:
                print(f"\nSession ID: {session_id}")
                print(f"Created: {created_at}")
                print(f"World: {world_desc[:50]}...")
                print(f"Player: {player_desc[:50]}...")
            print("\nOptions:")
            print("a. Select existing session (enter session ID)")
            print("b. Create new session")
            choice = input("Your choice: ").strip()
        else:
            choice = "b"
            
        if choice == "b":
            print("\nCreating new session:")
            player_description = input("\nEnter player description, print d for default\n")
            language = select_language()

            if player_description == "d":
                player_description = base_character_description
            session_id = manager.db.create_session(user_id, world_description=base_world_description, player_description=player_description,language=language)
            return session_id, True
            

                
        elif choice.isdigit():
            session_id = int(choice)
            for existing_id, _, _, _ in sessions:
                if session_id == existing_id:
                    return session_id, False
                    
        print("Invalid choice. Please try again.")


def select_language() -> str:
    while True:
        print("\nSelect language:")
        print("1. English (en)")
        print("2. Russian (ru)")
        choice = input("Your choice (1-2): ").strip()
        
        language_map = {
            "1": "English",
            "2": "Russian"
        }
        
        if choice in language_map:
            return language_map[choice]
        print("Invalid choice. Please try again.")


def main() -> None:
    manager = SessionManager()
    
    user_id = select_user(manager)
    print(f"\nSelected User ID: {user_id}")
    
    session_id, is_new = select_session(manager, user_id)
    print(f"\nSelected Session ID: {session_id}")
    

    game_manager = GameManager(session_id)
    try:

        sessions = manager.db.get_user_sessions(user_id)
        session_id = int(session_id)
        if any(session_id == existing_id for existing_id, _, _, _ in sessions):
            print("\nMessage History:")
            print("="*50)
            
            # Get and display user messages
            user_messages = manager.db.get_user_messages(session_id)
            for seq, user_input, response in user_messages:
                print(f"\nMessage #{seq}")
                print(f"User: {user_input}")
                print(f"Response: {response}")
                print("-"*30)
                        
    except ValueError:
        pass
    while True:
        game_manager.generate_image(2)
        print("Enter your message:")
        user_input = input().strip()
        if user_input.lower() == 'quit':
            break
            
        # Process input and get both narrative response and image path
        narrative_response, image_path = game_manager.process_input(user_input,True)
        
        # Display results
        print("\nNarrative Response:")
        print(narrative_response)
        #game_manager.generate_image(user_input, narrative_response)            
        print("\n" + "="*50)

if __name__ == "__main__":
    run_mypy()
    main()
