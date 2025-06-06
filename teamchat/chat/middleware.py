from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from channels.db import database_sync_to_async

class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])
        auth_header = headers.get(b'authorization', b'').decode()
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split()[1]
            jwt_auth = JWTAuthentication()
            
            try:
                validated_token = await database_sync_to_async(jwt_auth.get_validated_token)(token)
                user = await database_sync_to_async(jwt_auth.get_user)(validated_token)
                scope['user'] = user
            except Exception as e:
                scope['user'] = AnonymousUser()
                print(f"JWT validation failed: {e}")
        else:
            scope['user'] = AnonymousUser()

        return await self.app(scope, receive, send)