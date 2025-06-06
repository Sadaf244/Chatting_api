import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Channel, Message, UserChannelLastSeen
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.channel_group_name = f'chat_{self.channel_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.channel_group_name,
            self.channel_name
        )
        
        # Update user presence
        user = self.scope['user']
        if user.is_authenticated:
            await self.update_user_presence(user, True)
            await self.channel_layer.group_send(
                self.channel_group_name,
                {
                    'type': 'user_presence',
                    'user_id': user.id,
                    'status': True
                }
            )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.channel_group_name,
            self.channel_name
        )
        
        # Update user presence
        user = self.scope['user']
        if user.is_authenticated:
            await self.update_user_presence(user, False)
            await self.channel_layer.group_send(
                self.channel_group_name,
                {
                    'type': 'user_presence',
                    'user_id': user.id,
                    'status': False
                }
            )

    async def receive(self, text_data):

        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message', '')[:2000]
            if not message.strip():
                return
            
            user = self.scope['user']
            
            if not user.is_authenticated:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Authentication required'
                }))
                return
            if not await self.check_rate_limit(user):
                await self.send_error('Message rate limit exceeded')
                return
            # Save message to database with additional checks
            saved_message = await self.save_message(user, message)
            print(f"Message saved with ID: {saved_message.id}")  
            # Send message to room group
            await self.channel_layer.group_send(
                self.channel_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'user_id': user.id,
                    'username': user.username,
                    'timestamp': str(saved_message.timestamp),
                    'message_id': saved_message.id
                }
            )

        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    @database_sync_to_async
    def check_rate_limit(self, user):
        """Allow max 20 messages per minute per user"""
        
        cache_key = f'msg_rate_{user.id}'
        count = cache.get(cache_key, 0)
        if count >= 20:
            return False
        cache.set(cache_key, count+1, timeout=60)
        return True
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': event['message'],
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id']
        }))

    async def user_presence(self, event):
        # Send presence update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'presence',
            'user_id': event['user_id'],
            'status': event['status']
        }))

    @database_sync_to_async
    def save_message(self, user, content):
        channel = Channel.objects.get(id=self.channel_id)
        
        # Verify user is a member of the channel
        if not channel.members.filter(id=user.id).exists():
            raise PermissionDenied("You are not a member of this channel")
        
        # Create and save the message
        message = Message.objects.create(
            channel=channel,
            sender=user,
            content=content
        )
        
        # Update last seen timestamp for the user in this channel
        UserChannelLastSeen.objects.update_or_create(
            user=user,
            channel=channel,
            defaults={'last_seen': timezone.now()}
        )
        
        return message

    @database_sync_to_async
    def update_user_presence(self, user, online):
        user.online = online
        user.last_seen = timezone.now()
        user.save(update_fields=['online', 'last_seen'])