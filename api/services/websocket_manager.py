import json
import asyncio
from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self.active_connections = {}

    async def add_connection_to_channel(self, channel: str, socket: WebSocket):
        """
        Initializes a WebSocket connection and adds it to the pool.
        """
        await socket.accept()
        if self.active_connections.get(channel) is None:
            self.active_connections[channel] = []

        self.active_connections[channel].append(socket)

    async def remove_connection_from_channel(self, channel: str, socket: WebSocket):
        """
        Removes WebSocket connection from the pool.
        """
        self.active_connections[channel].remove(socket)

    async def broadcast(self, channel: str, message: dict):
        """
        Broadcast message to all peers.
        """
        events = [
            socket.send_text(json.dumps(message))
            for socket in self.active_connections[channel]
        ]

        await asyncio.gather(*events)

    async def broadcast_from_input(self, message):
        """
        Broadcast message to all peers from input format.
        """
        channel = message.get("channel").decode("utf-8")
        sockets = self.active_connections.get(channel)

        if sockets is None:
            return

        events = [
            socket.send_text(message.get("data", b"").decode("utf-8"))
            for socket in self.active_connections[channel]
        ]

        await asyncio.gather(*events)
