from channels.generic.websocket import AsyncWebsocketConsumer
import json
from datetime import datetime

# =============================================================================== #
#                                LIVE-CHAT CONSUMER                               #
# =============================================================================== #
# Consumer used for the live-chat feature for citizen/contact
# Utilising sessions and JavaScript for message storing and retrieval to work while site is in use for citizen users (template: monitor.html)
# Reference: Advanced Web Development [CM3035], week 12, "6.406 Implement a Chat server",  https://www.coursera.org/learn/uol-cm3035-advanced-web-development/lecture/CgMEO/6-406-implement-a-chat-server
class LiveChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.contact = self.scope['url_route']['kwargs']['contact']
        self.contact_group = 'chat_%s' % self.contact

        # Join channel
        await self.channel_layer.group_add(
            self.contact_group,
            self.channel_name
        )

        await self.accept()

    # Disconnect
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.contact_group,
            self.channel_name
        )

    # Receive message from the WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        contact = text_data_json.get('contact', '')  
        timestamp = datetime.now().strftime('%H:%M')

        # Send message to channel layer
        await self.channel_layer.group_send(
            self.contact_group,
            {
                'type': 'chat_message',
                'message': message,
                'contact': contact,
                'timestamp': timestamp
            }
        )

    # Receive messages
    async def chat_message(self, event):
        message = event['message']
        contact = event['contact']
        timestamp = event['timestamp']
        
        # Send
        await self.send(text_data=json.dumps({
            'message': message,
            'contact': contact,
            'timestamp': timestamp
        }))