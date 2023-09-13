import asyncio


class EventInput:
    def __init__(self, process):
        self.process = process

    async def _receiver(self, channel):
        while True:
            message = await channel.get_message(ignore_subscribe_messages=True)
            if message is not None:
                await self.process(message)

    async def start(self, redis_conn):
        async with redis_conn.pubsub() as pubsub:
            await pubsub.psubscribe("*")

            future = asyncio.create_task(self._receiver(pubsub))

            await future
