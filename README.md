# Team Chat Application 

## Features
Real-time Messaging
WebSocket-based chat with presence tracking
Message history persistence
Team Collaboration
Multi-team support
Public/private/direct channels
Member management
Advanced Search
Full-text message search
Date range filtering
User-specific message filtering

### Setup Steps
# Clone repository
git clone https://github.com/Sadaf244/Chatting_api.git
cd teamchat

# Create virtual environment
python -m venv venv
source venv/bin/activate  

# Install dependencies
pip install -r requirements.txt

# Configure database in settings.py
# Run migrations
python manage.py makemigrations
python manage.py migrate

# API
## Register API
http://localhost:8000/api/auth/register/
**Request Body**:
```json
{
    "username": "newuser",
    "email": "user@example.com",
    "password": "securepassword123"
}
**Request Body**:
{
    "refresh": "",
    "access": "",
    "user": {
        "id": 11,
        "username": "newuser",
        "email": "securepassword123"
    }
}
## Login API
http://localhost:8000/api/auth/login/
**Request Body**:
```json
{
    "username": "newuser",
    "email": "user@example.com",
}
**Response Body**:
{
    "refresh": "",
    "access": "",
    "user": {
        "id": 11,
        "username": "newuser",
        "email": "securepassword123"
    }
}

## Create Team
http://localhost:8000/api/auth/teams/
** Request Body
{
    "name": "frontend Team",
    "description": "Our dev team channel",
    "members": [1,2, 3,7,9 ]
    
}
Response Body

{
    "name": "Marketing",
    "description": "Marketing team",
    "members": [2, 3,7,9,1,8]
}
## Send Message to Channel
ws://localhost:8001/ws/chat/{channel_id}/
{
    "message": "Hello everyone!"


## search message
http://localhost:8000/api/channels/{channel_id}/search/`

**Parameters**:
- `q`: Search query
- `from`: Start date (YYYY-MM-DD)
- `to`: End date (YYYY-MM-DD)
- `user`: Filter by sender ID
- `page`: Page number

**Response**:
```json
{
    "results": [
        {
            "id": 123,
            "content": "Meeting about <mark>Django</mark>",
            "highlights": ["Meeting about <mark>Django</mark>"]
        }
    ],
    "total": 15,
    "page": 1
}
}
 View All Channel message
http://localhost:8000/api/channels/{channel_id}/messages/
**Response Body:
{
    "count": 4,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 5,
            "channel": 6,
            "sender": 9,
            "username": "neha",
            "user_avatar": null,
            "content": "I am good too",
            "timestamp": "2025-06-06T20:35:25.527454Z",
            "edited": false,
            "edited_at": null,
            "parent": null
        },
 ## See status
http://localhost:8000/api/auth/profile/
Response Body:
{
    "id": 8,
    "username": "nai74052",
    "email": "nai4@gmail.com",
    "online": true,
    "last_seen": "2025-06-06T20:34:10.421232Z",
    "avatar": null
}

Schedule:
Presence cleanup runs every 5 minutes
📦 Dependencies
Component	Purpose
Django	Core application framework
DRF	REST API implementation
sqlite	Primary data store
Redis	Caching and message brokering
Celery	Background task processing
Channels	WebSocket support
