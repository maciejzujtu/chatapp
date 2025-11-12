import uuid
import time
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field, ValidationError
from redis.asyncio import Redis

REDIS_URL = "redis://localhost:6379/0"
redis_client: Optional[Redis] = None
EXPIRATION_SECONDS = 300  # 5 minutes (TTL)


class TemporaryRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    title: str
    user_posting_id: str

    model_config = {
        "from_attributes": True
    }

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    try:
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        print("Redis client connected.")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        redis_client = None

    yield

    if redis_client:
        await redis_client.close()
        print("Redis client closed.")


def get_redis_client() -> Redis:
    """Dependency to inject the Redis client."""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis service is unavailable")
    return redis_client


# --- 3. THE EPHEMERAL SERVICE LAYER ---

class EphemeralDataService:
    def __init__(self, r: Redis):
        self.r = r
        self.key_prefix = "topic_id:"

    def _hash_key(self, record_id: str) -> str:
        # Key naming convention: e.g., "ephemeral:a1b2c3d4-..."
        return f"{self.key_prefix}{record_id}"

    async def create_and_expire(self, title: str, user_posting_id: str) -> TemporaryRecord:
        """
        Creates a new record with a unique UUID, stores it as a Hash,
        and sets its expiration time.
        """
        record = TemporaryRecord(title=title, user_posting_id=user_posting_id)
        key = self._hash_key(record.id)

        # 1. Store the data as a Redis Hash
        data_to_store: Dict[str, Any] = record.model_dump()
        await self.r.hset(key, mapping=data_to_store)

        # 2. Set the Time-To-Live (TTL)
        await self.r.expire(key, EXPIRATION_SECONDS)

        return record

    async def get_record(self, record_id: str) -> Optional[TemporaryRecord]:
        """Retrieves a record, or None if it has expired or never existed."""
        key = self._hash_key(record_id)
        hash_data = await self.r.hgetall(key)

        if not hash_data:
            return None

        # Validate and deserialize the data back into the Pydantic object
        try:
            return TemporaryRecord(**hash_data)
        except ValidationError as e:
            print(f"Corrupt record found for ID {record_id}. Deleting it. Error: {e}")
            await self.r.delete(key)
            return None

    async def get_all_records_structured(self) -> List[TemporaryRecord]:
        """
        Retrieves all currently stored (unexpired) ephemeral records as structured Pydantic objects.
        NOTE: Uses Redis Pipelining for better performance than individual HGETALL calls.
        """
        key_pattern = f"{self.key_prefix}*"
        keys = await self.r.keys(key_pattern)

        # Use a pipeline to fetch all hash data concurrently
        pipe = self.r.pipeline()
        for key in keys:
            pipe.hgetall(key)

        raw_hash_results = await pipe.execute()
        all_records: List[TemporaryRecord] = []

        for hash_data in raw_hash_results:
            if hash_data:
                try:
                    # Deserialize and validate
                    record = TemporaryRecord(**hash_data)
                    all_records.append(record)
                except ValidationError:
                    # Skip corrupt data
                    continue

                    # Sort by timestamp (newest first)
        all_records.sort(key=lambda r: r.timestamp, reverse=True)

        return all_records

    async def get_all_raw_records(self) -> List[Dict[str, Any]]:
        """
        Retrieves all currently stored (unexpired) ephemeral records as raw
        key-value pairs (Hashes), showing the full Redis key and the hash fields.
        """
        key_pattern = f"{self.key_prefix}*"
        keys = await self.r.keys(key_pattern)

        all_raw_records: List[Dict[str, Any]] = []

        for key in keys:
            # Retrieve the raw Hash data (a dictionary of strings)
            hash_data = await self.r.hgetall(key)

            if hash_data:
                # Compile the full key and the raw data fields
                record_entry = {
                    "redis_key": key,
                    "fields": hash_data
                }
                all_raw_records.append(record_entry)

        return all_raw_records


# --- 4. FASTAPI ROUTES ---

app = FastAPI(
    title="Ephemeral Data API",
    lifespan=lifespan
)


@app.post("/record", response_model=TemporaryRecord, status_code=status.HTTP_201_CREATED)
async def create_ephemeral_record(
        title: str,
        user_posting_id: str,
        r: Redis = Depends(get_redis_client)
):
    """
    Creates a new temporary record with a unique UUID and sets it to expire in 5 minutes.
    """
    service = EphemeralDataService(r)
    record = await service.create_and_expire(title, user_posting_id)

    ttl_minutes = EXPIRATION_SECONDS / 60
    print(f"Created record {record.id}, expires in {ttl_minutes} minutes.")

    return record


@app.get("/record/{record_id}", response_model=TemporaryRecord)
async def get_ephemeral_record(
        record_id: str,
        r: Redis = Depends(get_redis_client)
):
    """
    Retrieves a temporary record by its UUID. Returns 404 if expired or not found.
    """
    service = EphemeralDataService(r)
    record = await service.get_record(record_id)

    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found or has expired")

    ttl_seconds = await r.ttl(service._hash_key(record_id))
    print(f"Record {record_id} found. Remaining TTL: {ttl_seconds} seconds.")

    return record


@app.get("/records", response_model=List[TemporaryRecord])
async def get_all_ephemeral_records(
        r: Redis = Depends(get_redis_client)
):
    """
    Retrieves a list of all current (unexpired) temporary records as structured
    Pydantic objects, sorted by creation time (efficiently using pipelines).
    """
    service = EphemeralDataService(r)
    records = await service.get_all_records_structured()
    return records


@app.get("/records/raw", response_model=List[Dict[str, Any]])
async def get_all_ephemeral_raw_records(
        r: Redis = Depends(get_redis_client)
):
    """
    Retrieves a list of all current (unexpired) temporary records, showing the
    raw Redis key and hash fields (key-value pairs) before Pydantic processing.
    """
    service = EphemeralDataService(r)
    raw_records = await service.get_all_raw_records()
    return raw_records