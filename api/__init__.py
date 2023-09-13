import os
import asyncio
import redis.asyncio as redis

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket


from api.services.event_input import EventInput
from api.services.websocket_manager import WebSocketManager
from api.common.common_functions import get_value_from_redis, set_value_into_redis


load_dotenv()

app = FastAPI()
socket_pool = WebSocketManager()
event_input = EventInput(socket_pool.broadcast_from_input)
redis_conn = redis.from_url(os.environ.get("REDIS_URL"))


@app.on_event("startup")
async def on_startup():
    loop = asyncio.get_event_loop()
    loop.create_task(event_input.start(redis_conn))


# Vehicle endpoints


from pydantic import BaseModel


class ActiveVehicle(BaseModel):
    id: int


@app.get("/active-vehicles")
async def active_vehicles():
    worker_input_list = await get_value_from_redis(
        redis_conn, os.environ.get("WORKER_INPUT")
    )
    return worker_input_list.get("vehicles")


@app.post("/active-vehicles")
async def add_active_vehicle(vehicle: ActiveVehicle):
    worker_input_list = await get_value_from_redis(
        redis_conn, os.environ.get("WORKER_INPUT")
    )
    vehicle_list = worker_input_list.get("vehicles", [])
    vehicle_list.append(vehicle.id)
    worker_input_list["vehicles"] = vehicle_list

    await set_value_into_redis(
        redis_conn, os.environ.get("WORKER_INPUT"), worker_input_list
    )

    return {"msg": "succeed"}


@app.websocket("/vehicle/{vehicle_id}/{sensor}/ws")
async def websocket_endpoint(websocket: WebSocket, vehicle_id: int, sensor: str):
    topic = f"vehicle/{vehicle_id}/{sensor}"

    await socket_pool.add_connection_to_channel(topic, websocket)

    try:
        while True:
            await websocket.receive_text()
    except Exception:
        await socket_pool.remove_connection_from_channel(topic, websocket)
