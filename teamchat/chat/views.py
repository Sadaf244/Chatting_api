from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from .models import User
from .serializers import UserSerializer
from .models import Channel, Message, Team
from .serializers import (
    ChannelSerializer,
    MessageSerializer,
    TeamSerializer,
    CustomSignupSerializer,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomLoginSerializer
from django.db.models import Q
from datetime import datetime
class CustomLoginView(APIView):
    def post(self, request):
        serializer = CustomLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomSignupView(APIView):
    def post(self, request):
        serializer = CustomSignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate tokens for the new user
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
    
class TeamListView(generics.ListCreateAPIView):
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Team.objects.filter(members=self.request.user)

    def perform_create(self, serializer):
        # The create() method in serializer will handle this now
        serializer.save()

class ChannelListView(generics.ListCreateAPIView):
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Channel.objects.filter(members=self.request.user)

    def perform_create(self, serializer):
        serializer.save() 

class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
  
    def get_queryset(self):
        channel_id = self.kwargs['channel_id']
        cache_key = f'messages_{channel_id}_{self.request.user.id}'
        queryset = cache.get(cache_key)

        if not queryset:
            queryset = Message.objects.filter(
                channel_id=channel_id,
                channel__members=self.request.user
            ).order_by('-timestamp')[:50]  # Limit to 50 most recent messages
            cache.set(cache_key, queryset, timeout=60*5)  # Cache for 5 minutes
        
        return queryset


class MessageSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, channel_id):
        # Validate channel access
        try:
            channel = Channel.objects.get(id=channel_id, members=request.user)
        except Channel.DoesNotExist:
            return Response(
                {"error": "Channel not found or access denied"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Get search parameters
        search_term = request.GET.get('q', '').strip()
        date_from = request.GET.get('from')
        date_to = request.GET.get('to')
        user_id = request.GET.get('user')
        
        # Start with base queryset
        queryset = Message.objects.filter(
            channel=channel
        ).select_related('sender').order_by('-timestamp')

        # Apply text search if provided
        if search_term:
            queryset = queryset.filter(
                Q(content__icontains=search_term)
            )

        # Apply date range filter if provided
        if date_from or date_to:
            date_filters = Q()
            if date_from:
                try:
                    from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                    date_filters &= Q(timestamp__date__gte=from_date)
                except ValueError:
                    return Response(
                        {"error": "Invalid date format for 'from'. Use YYYY-MM-DD"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            if date_to:
                try:
                    to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                    date_filters &= Q(timestamp__date__lte=to_date)
                except ValueError:
                    return Response(
                        {"error": "Invalid date format for 'to'. Use YYYY-MM-DD"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            queryset = queryset.filter(date_filters)

        # Apply user filter if provided
        if user_id:
            try:
                user_id = int(user_id)
                queryset = queryset.filter(sender_id=user_id)
            except (ValueError, TypeError):
                return Response(
                    {"error": "Invalid user ID"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Pagination
        page_size = min(int(request.GET.get('limit', '20')), 100)
        page = int(request.GET.get('page', '1'))
        total_count = queryset.count()
        messages = queryset[(page-1)*page_size : page*page_size]

        # Serialize results
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        
        return Response({
            'results': serializer.data,
            'total': total_count,
            'page': page,
            'page_size': page_size
        })