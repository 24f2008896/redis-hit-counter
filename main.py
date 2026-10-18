
import os
import time

import redis
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Redis Hit Counter API")

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
)


def get_redis():
    """Connect to Redis, retrying briefly during startup."""
    last_error = None

    for _ in range(10):
        try:
            client.ping()
            return client
        except redis.RedisError as exc:
            last_error = exc
            time.sleep(1)

    raise last_error


@app.get("/healthz")
def healthz():
    try:
        get_redis().ping()
        return {"status": "ok", "redis": "up"}
    except redis.RedisError:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "redis": "down"},
        )


@app.post("/hit/{key}")
def hit(key: str):
    try:
        count = get_redis().incr(f"hit:{key}")
        return {"key": key, "count": count}
    except redis.RedisError:
        return JSONResponse(
            status_code=503,
            content={"error": "Redis unavailable"},
        )


@app.get("/count/{key}")
def count(key: str):
    try:
        value = get_redis().get(f"hit:{key}")
        return {"key": key, "count": int(value) if value else 0}
    except redis.RedisError:
        return JSONResponse(
            status_code=503,
            content={"error": "Redis unavailable"},
        )
