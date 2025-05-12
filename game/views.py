from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import GameSession, ChatMessage
from src.SessionManager.SessionManager import SessionManager
from src.GameManager.GameManager import GameManager
from src.Descriptions.CharacterDecription import base_character_description
from src.GamePresets.GamePresets import GamePresets, GameWorld, GameCharacter
from django.views.decorators.http import require_GET

def landing(request):
    return render(request, 'game/landing.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            session_manager = SessionManager()
            user_id = session_manager.create_user()
            # Store the user_id in the user's profile or session
            request.session['game_user_id'] = user_id
            login(request, user)
            return redirect('session_list')
    else:
        form = UserCreationForm()
    return render(request, 'game/register.html', {'form': form})

@login_required
def session_list(request):
    sessions = GameSession.objects.filter(user=request.user)
    return render(request, 'game/session_list.html', {'sessions': sessions})

@login_required
def create_session(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        language_short = request.POST.get('language')
        world_value = request.POST.get('world')
        character_value = request.POST.get('character')
        
        language_map = {
            'en': 'English',
            'ru': 'Russian'
        }
        language = language_map.get(language_short, 'English')
        user_id = request.session.get('game_user_id')
        if not user_id:
            return render(request, 'game/create_session.html', {
                'error': 'User ID not found. Please log in again.'
            })
        session_manager = SessionManager()
        try:
            if world_value and character_value:
                # Создание сессии по пресету
                world = GameWorld[world_value]
                character = GameCharacter[character_value]
                session_id = session_manager.create_session_by_preset(
                    user_id=user_id,
                    world=world,
                    character=character,
                    language=language
                )
                # Получаем описания для сохранения в Django-модели
                world_description = GamePresets.get_world_description(world)
                player_description = GamePresets.get_character_description(character)
                session = GameSession.objects.create(
                    user=request.user,
                    title=title,
                    world_description=world_description,
                    player_description=player_description,
                    language=language_short,
                    game_session_id=session_id
                )
                
                # Get initial message from GamePresets
                initial_message = GamePresets.get_character_initial_message(character, language)
                
                # Create initial chat message
                ChatMessage.objects.create(
                    session=session,
                    user_message="",
                    bot_response=initial_message,
                    image_path=None,
                    sound_path=None
                )
                
                return redirect('chat', session_id=session.id)
            else:
                return render(request, 'game/create_session.html', {
                    'error': 'Please select both world and character.',
                    'worlds': GamePresets.get_all_worlds(),
                })
        except Exception as e:
            return render(request, 'game/create_session.html', {
                'error': str(e),
                'worlds': GamePresets.get_all_worlds(),
            })
    # GET-запрос: просто отдаем список миров
    return render(request, 'game/create_session.html', {
        'worlds': GamePresets.get_all_worlds(),
    })

@login_required
def chat(request, session_id):
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    messages = ChatMessage.objects.filter(session=session)
    return render(request, 'game/chat.html', {
        'session': session,
        'messages': messages
    })

@login_required
def send_message(request, session_id):
    if request.method == 'POST':
        session = get_object_or_404(GameSession, id=session_id, user=request.user)
        user_message = request.POST.get('message')
        generate_image = request.POST.get('generate_image', 'true').lower() == 'true'
        generate_audio = request.POST.get('generate_audio', 'true').lower() == 'true'
        
        # Get or create GameManager instance for this session
        game_manager = GameManager(session.game_session_id)
        bot_response, image_path, sound_path = game_manager.process_input(user_message, generate_image=generate_image, generate_audio=generate_audio)
        
        # Save the message to our database
        ChatMessage.objects.create(
            session=session,
            user_message=user_message,
            bot_response=bot_response,
            image_path=image_path,
            sound_path=sound_path
        )
        
        return JsonResponse({
            'bot_response': bot_response,
            'image_path': image_path,
            'sound_path': sound_path
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

# AJAX endpoint для получения персонажей выбранного мира
@login_required
@require_GET
def get_characters_for_world(request):
    world_value = request.GET.get('world')
    if not world_value:
        return JsonResponse({'error': 'No world specified'}, status=400)
    try:
        world = GameWorld[world_value]
        characters = GamePresets.get_world_characters(world)
        # characters: List[Tuple[GameCharacter, str]]
        data = [{'value': c[0].name, 'label': c[1]} for c in characters]
        return JsonResponse({'characters': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
