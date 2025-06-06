from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from .models import User, Channel, Message, Team
from django.utils.html import escape
User = get_user_model()

class CustomSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user

class CustomLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_active:
            raise serializers.ValidationError("Account disabled.")

        refresh = RefreshToken.for_user(user)  # Generate JWT tokens

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            }
        }
    
    
class TeamSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False,
        allow_empty=True
    )

    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'created_by', 'created_at', 'members']
        read_only_fields = ['created_by', 'created_at']
        extra_kwargs = {
            'name': {'required': True},
            'description': {'required': False}
        }
    # Validate that the creator is not in the members list

    def validate_members(self, value):
        """Ensure creator isn't in members list"""
        user = self.context['request'].user
        if user in value:
            raise serializers.ValidationError("Creator is automatically added as member")
        return value
    
    def create(self, validated_data):
        # Extract members if provided, otherwise default to empty list
        members = validated_data.pop('members', [])
        
        # Get the current user from request context
        user = self.context['request'].user
        
        # Create the team
        team = Team.objects.create(
            created_by=user,
            **validated_data
        )
        
        # Add creator as member and any additional members
        team.members.add(user, *members)
        
        return team

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'online', 'last_seen', 'avatar']


class ChannelSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False  # Make members optional
    )

    class Meta:
        model = Channel
        fields = ['id', 'name', 'team', 'channel_type', 'created_by', 'members']
        read_only_fields = ['created_by']  
        extra_kwargs = {
            'name': {'required': True},
            'channel_type': {'required': True}
        }

    def validate(self, data):
        """Validate channel creation rules"""
        # For direct messages, ensure exactly 2 members
        if data.get('channel_type') == 'direct':
            if 'members' not in data or len(data['members']) != 1:
                raise serializers.ValidationError(
                    "Direct messages require exactly 1 other member"
                )
        return data

    def create(self, validated_data):
        members = validated_data.pop('members', [])
        user = self.context['request'].user
        team = validated_data.get('team')
        
        channel = Channel.objects.create(
            created_by=user,
            **validated_data
        )
        
        # Add creator first
        channel.members.add(user)
        
        # For team channels, add all team members
        if team and channel.channel_type != 'direct':
            team_members = team.members.all()
            channel.members.add(*team_members)
        
        # Add any explicitly specified members
        if members:
            channel.members.add(*members)
        
        return channel
    
class MessageSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='sender.username', read_only=True)
    user_avatar = serializers.CharField(source='sender.avatar', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'channel', 'sender', 'username', 'user_avatar', 
                 'content', 'timestamp', 'edited', 'edited_at', 'parent']
    def validate_content(self, value):
        # Basic XSS protection
        cleaned_value = escape(value)
        if len(cleaned_value) > 2000:
            raise serializers.ValidationError("Message too long")
        return cleaned_value
    
class MessageSearchSerializer(MessageSerializer):
    highlights = serializers.SerializerMethodField()

    class Meta(MessageSerializer.Meta):
        fields = MessageSerializer.Meta.fields + ['highlights']
    
    def get_highlights(self, obj):
        request = self.context.get('request')
        search_term = request.GET.get('q', '') if request else ''
        
        if not search_term:
            return []
        
        content = obj.content
        # Simple highlighting - for more advanced, consider Whoosh or Elasticsearch
        highlighted = []
        terms = search_term.lower().split()
        
        for term in terms:
            start = 0
            while True:
                idx = content.lower().find(term, start)
                if idx == -1:
                    break
                end = idx + len(term)
                highlighted.append((idx, end))
                start = end
        
        # Sort by position and merge overlapping ranges
        highlighted.sort()
        merged = []
        for start, end in highlighted:
            if not merged:
                merged.append([start, end])
            else:
                last_start, last_end = merged[-1]
                if start <= last_end:
                    merged[-1][1] = max(last_end, end)
                else:
                    merged.append([start, end])
        
        # Apply highlights
        result = []
        last_pos = 0
        for start, end in merged:
            if last_pos < start:
                result.append(content[last_pos:start])
            result.append(f'<mark>{content[start:end]}</mark>')
            last_pos = end
        
        if last_pos < len(content):
            result.append(content[last_pos:])
        
        return [''.join(result)]