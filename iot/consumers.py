import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ParkingStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("parking_status", self.channel_name)
        await self.accept()
        await self.send_current_status()

    async def disconnect(self, code):
        await self.channel_layer.group_discard("parking_status", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'ping':
            await self.send(json.dumps({'type': 'pong'}))

    async def parking_update(self, event):
        await self.send(json.dumps(event))

    async def send_current_status(self):
        slots = await self.get_slots()
        await self.send(json.dumps({'type': 'initial_status', 'slots': slots}))

    @database_sync_to_async
    def get_slots(self):
        from parking.models import ParkingSlot
        return list(ParkingSlot.objects.values('id', 'slot_number', 'level', 'column', 'status'))
