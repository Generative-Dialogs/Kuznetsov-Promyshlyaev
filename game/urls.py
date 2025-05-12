from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('register/', views.register, name='register'),
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/create/', views.create_session, name='create_session'),
    path('sessions/get_characters_for_world/', views.get_characters_for_world, name='get_characters_for_world'),
    path('chat/<int:session_id>/', views.chat, name='chat'),
    path('chat/<int:session_id>/send/', views.send_message, name='send_message'),
] 