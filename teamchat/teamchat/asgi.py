import os
import django
from django.core.asgi import get_asgi_application

# Set the default settings module before any imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'teamchat.settings')

# Initialize Django before importing models
django.setup()

# Now import other things that depend on Django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat.routing import websocket_urlpatterns
from chat.middleware import JWTAuthMiddleware
import chat.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})