import json
import os
import time

import redis
import requests

from sandbox import judge_submission


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QUEUE_NAME = os.getenv("JUDGE_QUEUE_NAME", "judge:submissions")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://backend:8000").rstrip("/")
JUDGE_TOKEN = os.getenv("JUDGE_INTERNAL_TOKEN", "dev-judge-token")


def backend_headers():
    return {"X-Judge-Token": JUDGE_TOKEN}


def fetch_payload(submission_id):
    url = f"{BACKEND_BASE_URL}/api/internal/judge/{submission_id}/payload/"
    response = requests.get(url, headers=backend_headers(), timeout=20)
    response.raise_for_status()
    return response.json()


def post_result(submission_id, result):
    url = f"{BACKEND_BASE_URL}/api/internal/judge/{submission_id}/result/"
    response = requests.post(url, json=result, headers=backend_headers(), timeout=20)
    response.raise_for_status()


def post_system_error(submission_id, message):
    post_result(
        submission_id,
        {
            "verdict": "SYSTEM_ERROR",
            "score": 0,
            "max_time_ms": 0,
            "max_memory_kb": 0,
            "compile_message": message[:4000],
            "case_results": [],
        },
    )


def handle_job(raw):
    payload = json.loads(raw)
    submission_id = payload["submission_id"]
    try:
        submission = fetch_payload(submission_id)
        result = judge_submission(submission)
        post_result(submission_id, result)
        print(f"judged submission={submission_id} verdict={result['verdict']}", flush=True)
    except Exception as exc:
        print(f"judge failed submission={submission_id}: {exc}", flush=True)
        try:
            post_system_error(submission_id, str(exc))
        except Exception as post_exc:
            print(f"failed to post system error submission={submission_id}: {post_exc}", flush=True)


def main():
    client = redis.from_url(REDIS_URL)
    print(f"judge worker started, queue={QUEUE_NAME}, backend={BACKEND_BASE_URL}", flush=True)
    while True:
        item = client.brpop(QUEUE_NAME, timeout=5)
        if not item:
            time.sleep(1)
            continue
        _, raw = item
        handle_job(raw)


if __name__ == "__main__":
    main()
