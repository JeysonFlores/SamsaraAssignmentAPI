import json


async def get_value_from_redis(conn, redis_key, to_dict=True):
    """
    Retrieves a value from the module-scoped redis connection.
    """
    try:
        value = await conn.get(redis_key)
        if to_dict and value:
            value = json.loads(value)
    except Exception as _:
        value = None

    return value


async def set_value_into_redis(conn, redis_key, payload, ttl=None):
    """
    Inserts value into a key in redis.
    """
    await conn.set(redis_key, json.dumps(payload))
    if ttl is not None and type(ttl) is int:
        await conn.expire(redis_key, ttl)
