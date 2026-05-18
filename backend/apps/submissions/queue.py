import json

import redis
from django.conf import settings


def enqueue_submission(submission_id):
    client = redis.from_url(settings.REDIS_URL)
    client.lpush(settings.JUDGE_QUEUE_NAME, json.dumps({"submission_id": submission_id}))
