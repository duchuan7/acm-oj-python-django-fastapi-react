import time
import uuid

import redis
from django.conf import settings


RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]
redis.call("ZREMRANGEBYSCORE", key, "-inf", now - window_ms)
local count = redis.call("ZCARD", key)
if count >= limit then
    local earliest = redis.call("ZRANGE", key, 0, 0, "WITHSCORES")
    local retry_after = math.ceil((tonumber(earliest[2]) + window_ms - now) / 1000)
    return {0, math.max(retry_after, 1)}
end
redis.call("ZADD", key, now, member)
redis.call("EXPIRE", key, math.ceil(window_ms / 1000) + 1)
return {1, 0}
"""


def acquire_submission_slot(user_id):
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    now_ms = int(time.time() * 1000)
    allowed, retry_after = client.eval(
        RATE_LIMIT_SCRIPT,
        1,
        f"submission-rate:{user_id}",
        now_ms,
        settings.SUBMISSION_RATE_LIMIT_WINDOW_SECONDS * 1000,
        settings.SUBMISSION_RATE_LIMIT_COUNT,
        f"{now_ms}:{uuid.uuid4().hex}",
    )
    return bool(allowed), int(retry_after)
