import os
import json
import asyncio
import redis.asyncio as redis
from fastapi import FastAPI, WebSocket

from api.services.event_input import EventInput
from api.services.websocket_manager import WebSocketManager


app = FastAPI()
socket_pool = WebSocketManager()
event_input = EventInput(socket_pool.broadcast_from_input)
redis_conn = redis.from_url(os.environ.get("REDIS_URL"))


@app.on_event("startup")
async def on_startup():
    loop = asyncio.get_event_loop()
    loop.create_task(event_input.start(redis_conn))


@app.websocket("/vehicle/{vehicle_id}/{sensor}/ws")
async def websocket_endpoint(websocket: WebSocket, vehicle_id: int, sensor: str):
    topic = f"vehicle/{vehicle_id}/{sensor}"

    await socket_pool.add_connection_to_channel(topic, websocket)

    try:
        while True:
            await websocket.receive_text()
    except Exception:
        await socket_pool.remove_connection_from_channel(topic, websocket)


@app.get("/debug/topics")
async def vehicluwus():
    topics = []
    for key in socket_pool.active_connections.keys():
        topics.append(key)

    return json.dumps(topics)
