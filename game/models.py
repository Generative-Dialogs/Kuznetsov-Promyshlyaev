from django.db import models
from django.contrib.auth.models import User as DjangoUser

# Create your models here.

class GameSession(models.Model):
    user = models.ForeignKey(DjangoUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    world_description = models.TextField()
    player_description = models.TextField()
    language = models.CharField(max_length=10, choices=[('en', 'English'), ('ru', 'Russian')])
    created_at = models.DateTimeField(auto_now_add=True)
    game_session_id = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} ({self.user.username})"

class ChatMessage(models.Model):
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='messages')
    user_message = models.TextField()
    bot_response = models.TextField()
    image_path = models.CharField(max_length=255, null=True, blank=True)
    sound_path = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message in {self.session.title}"
