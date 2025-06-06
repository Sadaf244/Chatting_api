from django.urls import path
from .views import (
    UserProfileView,
    TeamListView,
    ChannelListView,
    MessageListView,
    MessageSearchView,
    CustomLoginView,
    CustomSignupView,
)

urlpatterns = [
    path('register/', CustomSignupView.as_view(), name='custom-signup'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('login/', CustomLoginView.as_view(), name='custom-login'),
    path('teams/', TeamListView.as_view(), name='team-list'),
    path('channels/', ChannelListView.as_view(), name='channel-list'),
    path('channels/<int:channel_id>/messages/', MessageListView.as_view(), name='message-list'),
    path('channels/<int:channel_id>/search/', MessageSearchView.as_view(), name='message-search'),

]

