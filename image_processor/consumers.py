from channels.generic.websocket import AsyncWebsocketConsumer  # type: ignore[import]
import json
from .clarifai_processor import AsyncVideoProcessor
import asyncio as asy


class ImageProcessorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.type = self.scope["url_route"]["kwargs"]["type"]
        if self.type not in ["stream", "chat"]:
            print("invalid route")
            await self.close()
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"{self.type}_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        self.cp = AsyncVideoProcessor()
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        pass

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            await self.handle_text_data(text_data)
        elif bytes_data:
            await self.handle_binary_data(bytes_data)

    async def handle_text_data(self, text_data):
        text_data_json = json.loads(text_data)
        data_type = text_data_json["type"]
        if data_type == "chat":
            message = text_data_json["message"]
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "chat_message", "message": message}
            )

    async def handle_binary_data(self, bytes_data):
        stream = bytes_data
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "stream_message", "stream": stream, "stream_type": "mp4"},
        )

    async def chat_message(self, event):
        message = event["message"]
        # handle the logic for chatting with the ai
        # reply = ai.reply(message)
        reply = "Hi my name is Ilens and I'm pleased to be your assistant"
        await self.send(text_data=json.dumps({"user": message, "ai": reply}))

    async def stream_message(self, event):
        stream = event["stream"]
        event["stream_type"]
        results = await self.cp.process_video(stream, 4)
        print("- Image Generated")
        result_bytes = await asy.to_thread(
            self.cp.convert_result_image_arrays_to_bytes, results
        )
        print("- Image Converted")
        await asy.to_thread(self.clarifai.find_all_objects, result_bytes)
        print("- Image identified")
        await self.send(
            text_data=json.dumps({"stream": "Successfully received stream"})
        )
