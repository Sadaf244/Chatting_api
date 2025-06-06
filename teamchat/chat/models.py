from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser
    """
    online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)
    avatar = models.URLField(blank=True, null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['online']),
        ]
    
    def update_presence(self, is_online):
        """Update user's online status and last seen timestamp"""
        self.online = is_online
        self.last_seen = timezone.now()
        self.save(update_fields=['online', 'last_seen'])

class Team(models.Model):
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='created_teams'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(
        User,
        related_name='teams'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Channel(models.Model):
   
    CHANNEL_TYPES = (
        ('public', 'Public'),
        ('private', 'Private'),
        ('direct', 'Direct Message'),
    )
    
    name = models.CharField(max_length=100)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True, related_name='channels')
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_channels')
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(User, related_name='channels')
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['team', 'channel_type']),
            models.Index(fields=['channel_type']),
        ]
        unique_together = ('name', 'team')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_channel_type_display()})"

class Message(models.Model):

    channel = models.ForeignKey(Channel, on_delete=models.CASCADE,related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE,related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,related_name='replies')
    
    class Meta:
        
        indexes = [
            models.Index(fields=['channel', '-timestamp']),
            models.Index(fields=['sender', '-timestamp']),
            models.Index(fields=['content'], name='content_idx', opclasses=['text_pattern_ops']),
        ]
        ordering = ['-timestamp']
        get_latest_by = 'timestamp'
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"



class UserChannelLastSeen(models.Model):
   
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='channel_visits')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='user_visits')
    last_seen = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'channel')
        indexes = [
            models.Index(fields=['user', 'channel']),
        ]
    
    def __str__(self):
        return f"{self.user.username} last seen {self.channel.name} at {self.last_seen}"

