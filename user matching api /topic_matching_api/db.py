from redis.asyncio import Redis
from typing import Optional

DEFAULT_REDIS_URL = "redis://localhost:6379/0"

async def get_async_redis_client( url: str = DEFAULT_REDIS_URL, password: Optional[str] = None,decode_responses: bool = True) -> Redis:

    try:
        client = Redis.from_url(
            url,
            password=password,
            decode_responses=decode_responses
        )

        await client.ping()
        print(f"Successfully connected to Redis at {url}")

        return client

    except ConnectionRefusedError:
        print(f"ERROR: Could not connect to Redis at {url}. Is the Redis server running?")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during Redis connection: {e}")
        raise