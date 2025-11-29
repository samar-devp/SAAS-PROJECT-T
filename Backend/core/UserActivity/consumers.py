import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
from .models import UserLocationHistory, UserLiveLocation
from AuthN.models import BaseUserModel

User = get_user_model()


class LocationTrackingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time location tracking"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'location_tracking_{self.user_id}'
        self.admin_id = None
        
        # Get user from query string or headers
        query_string = self.scope.get('query_string', b'').decode()
        if 'admin_id' in query_string:
            self.admin_id = query_string.split('admin_id=')[1].split('&')[0]
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Mark user as online
        await self.mark_user_online(True)
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': 'Connected to location tracking',
            'user_id': self.user_id
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Mark user as offline
        await self.mark_user_online(False)
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'location_update':
                # Handle location update from user
                await self.handle_location_update(data)
            elif message_type == 'start_tracking':
                # Admin wants to start tracking
                await self.handle_start_tracking(data)
            elif message_type == 'stop_tracking':
                # Admin wants to stop tracking
                await self.handle_stop_tracking(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Unknown message type'
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def handle_location_update(self, data):
        """Handle location update from user device"""
        try:
            location_data = data.get('location', {})
            
            # Save to database
            location_history = await self.save_location_history(location_data)
            live_location = await self.update_live_location(location_data)
            
            # Broadcast to admin/observers
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'location_broadcast',
                    'location': {
                        'user_id': self.user_id,
                        'latitude': float(location_data.get('latitude', 0)),
                        'longitude': float(location_data.get('longitude', 0)),
                        'accuracy': location_data.get('accuracy'),
                        'speed': location_data.get('speed'),
                        'heading': location_data.get('heading'),
                        'battery_percentage': location_data.get('battery_percentage'),
                        'is_charging': location_data.get('is_charging', False),
                        'is_moving': location_data.get('is_moving', False),
                        'address': location_data.get('address'),
                        'city': location_data.get('city'),
                        'state': location_data.get('state'),
                        'timestamp': timezone.now().isoformat(),
                    }
                }
            )
            
            # Send confirmation to user
            await self.send(text_data=json.dumps({
                'type': 'location_saved',
                'message': 'Location updated successfully',
                'timestamp': timezone.now().isoformat()
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error saving location: {str(e)}'
            }))
    
    async def handle_start_tracking(self, data):
        """Handle start tracking request from admin"""
        admin_id = data.get('admin_id')
        if admin_id:
            self.admin_id = admin_id
            await self.send(text_data=json.dumps({
                'type': 'tracking_started',
                'message': 'Location tracking started'
            }))
    
    async def handle_stop_tracking(self, data):
        """Handle stop tracking request from admin"""
        await self.send(text_data=json.dumps({
            'type': 'tracking_stopped',
            'message': 'Location tracking stopped'
        }))
    
    async def location_broadcast(self, event):
        """Send location update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'location': event['location']
        }))
    
    @database_sync_to_async
    def save_location_history(self, location_data):
        """Save location to history"""
        try:
            user = BaseUserModel.objects.get(id=self.user_id)
            admin = None
            organization = None
            
            if self.admin_id:
                admin = BaseUserModel.objects.filter(id=self.admin_id, role='admin').first()
                if admin:
                    # Get organization from user profile
                    try:
                        user_profile = user.own_user_profile
                        organization = user_profile.organization
                    except:
                        pass
            
            captured_at = location_data.get('captured_at')
            if isinstance(captured_at, str):
                captured_at = datetime.fromisoformat(captured_at.replace('Z', '+00:00'))
            elif not captured_at:
                captured_at = timezone.now()
            
            location_history = UserLocationHistory.objects.create(
                user=user,
                admin=admin,
                organization=organization,
                latitude=Decimal(str(location_data.get('latitude', 0))),
                longitude=Decimal(str(location_data.get('longitude', 0))),
                accuracy=location_data.get('accuracy'),
                altitude=location_data.get('altitude'),
                speed=location_data.get('speed'),
                heading=location_data.get('heading'),
                battery_percentage=location_data.get('battery_percentage'),
                is_charging=location_data.get('is_charging', False),
                is_moving=location_data.get('is_moving', False),
                address=location_data.get('address'),
                city=location_data.get('city'),
                state=location_data.get('state'),
                country=location_data.get('country'),
                pincode=location_data.get('pincode'),
                source=location_data.get('source', 'mobile'),
                device_id=location_data.get('device_id'),
                app_version=location_data.get('app_version'),
                captured_at=captured_at
            )
            return location_history
        except Exception as e:
            print(f"Error saving location history: {str(e)}")
            return None
    
    @database_sync_to_async
    def update_live_location(self, location_data):
        """Update or create live location"""
        try:
            user = BaseUserModel.objects.get(id=self.user_id)
            admin = None
            organization = None
            
            if self.admin_id:
                admin = BaseUserModel.objects.filter(id=self.admin_id, role='admin').first()
                if admin:
                    try:
                        user_profile = user.own_user_profile
                        organization = user_profile.organization
                    except:
                        pass
            
            live_location, created = UserLiveLocation.objects.update_or_create(
                user=user,
                defaults={
                    'admin': admin,
                    'organization': organization,
                    'latitude': Decimal(str(location_data.get('latitude', 0))),
                    'longitude': Decimal(str(location_data.get('longitude', 0))),
                    'accuracy': location_data.get('accuracy'),
                    'altitude': location_data.get('altitude'),
                    'speed': location_data.get('speed'),
                    'heading': location_data.get('heading'),
                    'battery_percentage': location_data.get('battery_percentage'),
                    'is_charging': location_data.get('is_charging', False),
                    'is_moving': location_data.get('is_moving', False),
                    'address': location_data.get('address'),
                    'city': location_data.get('city'),
                    'state': location_data.get('state'),
                    'is_online': True,
                    'source': location_data.get('source', 'mobile'),
                    'device_id': location_data.get('device_id'),
                }
            )
            return live_location
        except Exception as e:
            print(f"Error updating live location: {str(e)}")
            return None
    
    @database_sync_to_async
    def mark_user_online(self, is_online):
        """Mark user as online/offline"""
        try:
            user = BaseUserModel.objects.get(id=self.user_id)
            UserLiveLocation.objects.filter(user=user).update(
                is_online=is_online,
                last_seen=timezone.now()
            )
        except:
            pass

