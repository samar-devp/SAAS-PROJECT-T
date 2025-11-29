# UserActivity - Live Location Tracking with Django Channels

## Features
- Real-time location tracking using WebSockets
- Location history storage
- Live location updates
- Admin can track multiple users
- REST API endpoints for location data

## Installation

### 1. Install Required Packages
```bash
pip install channels channels-redis  # For production, use Redis
# OR for development (InMemoryChannelLayer):
pip install channels
```

### 2. Database Migrations
```bash
python manage.py makemigrations UserActivity
python manage.py migrate
```

### 3. Run Server
```bash
# Development
python manage.py runserver

# For production with ASGI
daphne core.asgi:application
# OR
uvicorn core.asgi:application
```

## WebSocket Connection

### Client Connection (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/location/{user_id}/?admin_id={admin_id}');

ws.onopen = () => {
    console.log('Connected to location tracking');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'location_update') {
        console.log('Location update:', data.location);
    }
};

// Send location update
ws.send(JSON.stringify({
    type: 'location_update',
    location: {
        latitude: 28.6139,
        longitude: 77.2090,
        accuracy: 10,
        speed: 5.5,
        battery_percentage: 85,
        is_charging: false,
        is_moving: true,
        address: "New Delhi",
        city: "Delhi",
        state: "Delhi",
        captured_at: new Date().toISOString()
    }
}));
```

## API Endpoints

### 1. Get Location History
```
GET /api/user-activity/location-history/{user_id}/
Query Params:
- start_date: YYYY-MM-DD (optional)
- end_date: YYYY-MM-DD (optional)
- limit: number (default: 100)
- offset: number (default: 0)
```

### 2. Get Live Location
```
GET /api/user-activity/live-location/
Query Params:
- user_id: UUID (optional, for specific user)
```

### 3. Update Location (REST API alternative)
```
POST /api/user-activity/location-update/
Body:
{
    "latitude": 28.6139,
    "longitude": 77.2090,
    "accuracy": 10,
    "speed": 5.5,
    "battery_percentage": 85,
    "is_charging": false,
    "is_moving": true,
    "address": "New Delhi",
    "city": "Delhi",
    "state": "Delhi"
}
```

## Models

### UserLocationHistory
Stores historical location data with timestamps

### UserLiveLocation
Stores current/live location (OneToOne with User)

## WebSocket Message Types

### From Client:
- `location_update`: Send location data
- `start_tracking`: Start tracking (admin)
- `stop_tracking`: Stop tracking (admin)

### From Server:
- `connection`: Connection confirmation
- `location_update`: Broadcast location to observers
- `location_saved`: Confirmation of saved location
- `error`: Error message

## Production Setup

For production, use Redis as channel layer:

```python
# settings.py
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

Install Redis:
```bash
pip install channels-redis
```

